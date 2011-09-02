/* _classifier.c - */

// Compile (for testing) with:
//   python setup.py build_ext -i

#include "sqlite3.h"
#include "Python.h"
#include "numpy/arrayobject.h"
#include <stdio.h>

#define MAX_STUMPS 100  // Default limit for sqlite3
#define MAX_CLASSES 100 

static struct {
  int num_classes;
  int num_stumps;
  double thresholds[MAX_STUMPS];
  double stump_weights_a[MAX_STUMPS][MAX_CLASSES];
  double stump_weights_b[MAX_STUMPS][MAX_CLASSES];
  int valid;
} classifier_data;

#define TYPE_ERROR(str, fail_label) {PyErr_SetString(PyExc_TypeError, (str)); goto fail_label;}
#define VALUE_ERROR(str, fail_label) {PyErr_SetString(PyExc_ValueError, (str)); goto fail_label;}

static PyObject *setup_classifier(PyObject *self, PyObject *args)
{
  PyObject *weak_learners;
  PyArrayObject *wl_array;
  int i, j;

  if (! PyArg_ParseTuple(args, "O", &weak_learners)) 
    TYPE_ERROR("one argument required", fail_1);

  wl_array = (PyArrayObject *) PyArray_FROM_OTF(weak_learners, NPY_DOUBLE, NPY_IN_ARRAY);
  if (! wl_array)
    return NULL;

  if (wl_array->nd != 2)
    TYPE_ERROR("argument must be 2D array of floats (or convertable to same)", fail_2);

  if ((PyArray_DIM(wl_array, 1) % 2) == 0) 
    TYPE_ERROR("argument must have an odd dimenions along axis 1", fail_2);

  classifier_data.num_stumps = PyArray_DIM(wl_array, 0);
  classifier_data.num_classes = PyArray_DIM(wl_array, 1) / 2;

  if (classifier_data.num_stumps > MAX_STUMPS)
    VALUE_ERROR("maximum number of stumps (100) exceeded.", fail_2);
  
  for (i = 0; i < classifier_data.num_stumps; i++) {
    classifier_data.thresholds[i] = * (double *) PyArray_GETPTR2(wl_array, i, 0);

    for (j = 0; j < classifier_data.num_classes; j++) {
      classifier_data.stump_weights_a[i][j] = * (double *) PyArray_GETPTR2(wl_array, i, 1 + j);
      classifier_data.stump_weights_b[i][j] = * (double *) PyArray_GETPTR2(wl_array, i, 1 + classifier_data.num_classes + j);
    }
  }

  classifier_data.valid = 1;

  Py_DECREF(wl_array);
  Py_INCREF(Py_None);
  return Py_None;

 fail_2:
  Py_DECREF(wl_array);
 fail_1:
  return NULL;
}

static void c_classifier(sqlite3_context* context, int argc, sqlite3_value** argv)
{
    int stumps[MAX_STUMPS], i, j;
    double best_score = -3 * classifier_data.num_stumps;
    int best_class = 0;

    if (! classifier_data.valid) {
      sqlite3_result_error(context, "setup_classifier() must be called before using classifier() in SQL.", -1);
      return;
    }

    if (argc != classifier_data.num_stumps) {
      sqlite3_result_error(context, "The number of arguments to classifier() must be the same as the number passed to setup_classifier()", -1);
      return;
    } 

    // compute the stumps
    for (i = 0; i < argc; i++) {
      stumps[i] = sqlite3_value_double(argv[i]) > classifier_data.thresholds[i];
    }

    // compute the scores
    for (i = 0; i < classifier_data.num_classes; i++) {
      double score = 0.0;
      for (j = 0; j < classifier_data.num_stumps; j++) 
        score += stumps[j] ? classifier_data.stump_weights_a[j][i] : classifier_data.stump_weights_b[j][i];
      if (score > best_score) {
        best_score = score;
        best_class = i;
      }
    }

    sqlite3_result_int(context, best_class + 1);
}


// NB: this will blow up if the pysqlite_Connection structure changes.
// This is just the first few bytes of the structure, so we can get the db.
typedef struct
{
    PyObject_HEAD
    sqlite3* db;
} pysqlite_Connection;

static PyObject* create_classifier_function(PyObject* self, PyObject* args)
{
    int rc;
    pysqlite_Connection *conn;

    if (!PyArg_ParseTuple(args, "O", &conn))
      return NULL;

    if (SQLITE_VERSION_NUMBER >= 3006020)
      sqlite3_initialize();
    rc = sqlite3_create_function(conn->db, "classifier", -1, SQLITE_UTF8, NULL, c_classifier, NULL, NULL);

    if (rc != SQLITE_OK) {
        return NULL;
    } else {
        Py_INCREF(Py_None);
        return Py_None;
    }
}

static PyMethodDef ClassifierMethods[] = {
    {"setup_classifier", setup_classifier, METH_VARARGS, "Set up a run of the classifier function"},
    {"create_classifier_function",  create_classifier_function, METH_VARARGS, "Create the C classifier function on a connection."},
    {NULL, NULL, 0, NULL}      
};


#ifdef __cplusplus
extern "C"
#endif
PyMODINIT_FUNC init_classifier(void)
{
     PyObject *m;

     classifier_data.valid = 0;

     m = Py_InitModule("_classifier", ClassifierMethods);
     import_array();

     if (m == NULL)
       return;
}
