
/* classify.c - */

// To add this function to mysql, compile it to classify.so, put it in a
// directory on the LD_LIBRARY_PATH for mysql, and execute this statement
// within mysql:
// mysql> CREATE FUNCTION classifier RETURNS INTEGER SONAME 'classify.so';



#include <stdio.h>
#include <string.h>

#if defined(WIN32) || defined(MS_WINDOWS) || defined(WINDOWS)
#else
typedef unsigned long long ulonglong;
typedef long long longlong;
#endif /*__WIN__*/


#include <my_global.h>
#include <my_sys.h>
#include <mysql.h>
#include <m_ctype.h>
#include <m_string.h>           // To get strmov()

my_bool classifier_init(UDF_INIT *initid, UDF_ARGS *args, char *message)
{
  int num_stumps, num_classes, i;

  // Classifier function can't return null.
  initid->maybe_null = 0;
  
  if ((args->arg_count < 4) || (args->args[0] == NULL) || (args->arg_type[0] != INT_RESULT)) {
    strcpy(message, "Requires at least 4 arguments, the first of which is a constant integer.");
    return 1; // fail
  }
  
  num_stumps = *((longlong*) args->args[0]);
  if (num_stumps <= 0) {
    strcpy(message, "First argument must be positive.");
    return 1; // fail
  } 

  num_classes = ((args->arg_count - 1) / num_stumps) - 2;
  
  if ((args->arg_count - 1) != (num_stumps * (num_classes + 2))) {
    strcpy(message, "Mismatch in argument number");
    return 1; // fail
  }

  initid->ptr = (char *) malloc(sizeof (int) * num_stumps);
  if (!(initid->ptr)) {
    strcpy(message,"Couldn't allocate memory");
    return 1; // fail
  }

  // set the argument types we want
  for (i = 1; i < args->arg_count; i++) 
    args->arg_type[i] = REAL_RESULT;
    
  return 0; // success
}

void classifier_deinit(UDF_INIT *initid)
{
  if (initid->ptr)
    free(initid->ptr);
}

longlong classifier(UDF_INIT *initid, UDF_ARGS *args, char *is_null,
                           char *error)
{
  longlong class; 
  double best_score;
  int num_stumps = *((longlong*) args->args[0]);
  int num_classes = ((args->arg_count - 1) / num_stumps) - 2;
  int *stumps = (int *) (initid->ptr);
  int offset, i, k;

#define get_arg(idx) ((args->args[idx] == NULL) ? 0.0 : *((double *) args->args[idx]))

  // evaluate stumps
  for (i = 0; i < num_stumps; i++) {
    stumps[i] = get_arg(i + 1) > get_arg(i + 1 + num_stumps);
  }

  // weights start at this offset.
  offset = 1 + 2 * num_stumps;
  for (k = 0; k < num_classes; k++) {
    double temp_score = 0.0;
    for (i = 0; i < num_stumps; i++) {
      temp_score += get_arg(offset + i) * stumps[i];
    }
    if ((k == 0) || (temp_score > best_score)) {
      best_score = temp_score;
      class = k;
    }
    offset += num_stumps;
  }

  return class;
}
