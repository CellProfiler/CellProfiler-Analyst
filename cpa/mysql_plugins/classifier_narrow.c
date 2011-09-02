/* 
 * classifier_narrow.c
 *
 * Compile with:
 * gcc -Wall -fPIC -c `mysql_config --cflags` classifier_narrow.c
 * gcc -o classifier_narrow.so -shared classifier_narrow.o
 *
 * To add this function to mysql, compile it to classifier_narrow.so,
 * put it in a directory on the LD_LIBRARY_PATH for mysql, and execute
 * this statement within mysql:
 * 
 * CREATE FUNCTION classifier_narrow RETURNS INTEGER SONAME 'classifier_narrow.so';
 *
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#if defined(WIN32) || defined(MS_WINDOWS) || defined(WINDOWS)
#else
//typedef unsigned long long ulonglong;
//typedef long long longlong;
#endif /*__WIN__*/


#include <my_global.h>
#include <my_sys.h>
#include <mysql.h>
#include <m_ctype.h>
#include <m_string.h>           // To get strmov()

my_bool classifier_narrow_init(UDF_INIT *initid, UDF_ARGS *args, char *message)
{
  int num_stumps, num_classes, i;

  // Classifier function can't return null.
  initid->maybe_null = 0;
  
  if ((args->arg_count < 4) || (args->args[0] == NULL) || (args->arg_type[0] != INT_RESULT)) {
    strcpy(message, "Requires at least 6 arguments, the first of which is a constant integer.");
    return 1; // fail
  }
  
  num_stumps = *((longlong*) args->args[0]);
  if (num_stumps <= 0) {
    strcpy(message, "First argument must be positive.");
    return 1; // fail
  } 

  num_classes = ((args->arg_count - 3) / num_stumps) - 2;
  
  if ((args->arg_count - 3) != (num_stumps * (num_classes + 2))) {
    strcpy(message, "Mismatch in argument number");
    return 1; // fail
  }

  int *stumps = (int *)malloc(sizeof(int) * (num_stumps + 1));
  stumps[0] = num_stumps;
  initid->ptr = (char *)stumps;
  if (!(initid->ptr)) {
    strcpy(message,"Couldn't allocate memory");
    return 1; // fail
  }

  // set the argument types we want
  for (i = 1; i < args->arg_count; i++) 
    args->arg_type[i] = REAL_RESULT;
    
  return 0; // success
}

void classifier_narrow_deinit(UDF_INIT *initid)
{
  if (initid->ptr)
    free(initid->ptr);
}

void classifier_narrow_clear(UDF_INIT *initid, char *is_null, char *error)
{
  int *stumps = (int *)(initid->ptr);
  int num_stumps = stumps[0];
  memset(stumps + 1, 0, num_stumps * sizeof(int));
}

#define get_arg(idx) ((args->args[idx] == NULL) ? 0.0 : *((double *) args->args[idx]))

void classifier_narrow_add(UDF_INIT *initid, UDF_ARGS *args,
			   char *is_null, char *error)
{
  int num_stumps = *((longlong *)args->args[0]);
  int feature_id = *((longlong *)args->args[args->arg_count - 2]);
  double feature_value = get_arg(args->arg_count - 1);
  double threshold;
  int *stumps = (int *)(initid->ptr);
  int stump, i;

  /* Which feature is this row for? */
  for (stump = 0; stump < num_stumps; stump++) {
    i = *((longlong *)args->args[stump + 1]);
    if (i == feature_id)
      break;
  }
  if (stump == num_stumps)
    return; /* This row is for a feature the classifier does not use. */

  threshold = get_arg(1 + num_stumps + stump);
  stumps[stump + 1] = feature_value > threshold;
}

/* Used by older version of MySQL. */
void classifier_narrow_reset(UDF_INIT *initid, UDF_ARGS *args,
			     char *is_null, char *error)
{
  classifier_narrow_clear(initid, is_null, error);
  classifier_narrow_add(initid, args, is_null, error);
}

longlong classifier_narrow(UDF_INIT *initid, UDF_ARGS *args, char *is_null,
                           char *error)
{
  longlong class; 
  double best_score;
  int num_stumps = *((longlong*) args->args[0]);
  int num_classes = ((args->arg_count - 1) / num_stumps) - 2;
  int *stumps = (int *) (initid->ptr);
  int offset, i, k;

  // weights start at this offset.
  offset = 1 + 2 * num_stumps;
  for (k = 0; k < num_classes; k++) {
    double temp_score = 0.0;
    for (i = 0; i < num_stumps; i++) {
      temp_score += get_arg(offset + i) * stumps[i + 1];
    }
    if ((k == 0) || (temp_score > best_score)) {
      best_score = temp_score;
      class = k;
    }
    offset += num_stumps;
  }

  return class;
}
