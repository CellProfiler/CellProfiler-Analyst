/* _classifier.c - */

#include "sqlite3.h"
#include "Python.h"

static void c_classifier(sqlite3_context* context, int argc, sqlite3_value** argv)
{
    int num_stumps = sqlite3_value_int(argv[0]);
    int num_classes = (argc - 1) / num_stumps - 2;
    double best_score = - 2 * num_stumps;
    int best_class = 0;
    int data_offset = 1 + 2 * num_stumps;
    int stumps[1024];
    int weights_offset = 1 + 2 * num_stumps;
    int i, j;


    // compute the stumps
    for (i = 0; i < num_stumps; i++) {
      stumps[i] = sqlite3_value_double(argv[1 + i]) > sqlite3_value_double(argv[1 + i + num_stumps]);
    }

    // compute the scores
    for (i = 0; i < num_classes; i++) {
      double score = 0.0;
      for (j = 0; j < num_stumps; j++) {
        score += stumps[j] * sqlite3_value_double(argv[weights_offset]);
        weights_offset++;
      }
      if (score > best_score) {
        best_score = score;
        best_class = i;
      }
    }

    sqlite3_result_int(context, best_class);
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
    PyObject* ret;
    int rc;
    pysqlite_Connection *conn;

    if (!PyArg_ParseTuple(args, "O", &conn))
      return NULL;

    rc = sqlite3_create_function(conn->db, "classifier", -1, SQLITE_UTF8, NULL, c_classifier, NULL, NULL);

    if (rc != SQLITE_OK) {
        return NULL;
    } else {
        Py_INCREF(Py_None);
        return Py_None;
    }
}

static PyMethodDef ClassifierMethods[] = {
    {"create_classifier_function",  create_classifier_function, METH_VARARGS, "Create the C classifier function on a connection."},
    {NULL, NULL, 0, NULL}      
};


#ifdef __cplusplus
extern "C"
#endif
init_classifier(void)
{
     PyObject *m;

     m = Py_InitModule("_classifier", ClassifierMethods);
     if (m == NULL)
       return;
}
