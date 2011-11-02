import sys
import itertools
import numpy as np

class InputError(Exception):
    def __init__(self, filename, message, line=None):
        self.filename = filename
        self.message = message
        self.line = line

    def __unicode__(self):
        if self.line is None:
            print >>sys.stderr, '%s: Error: %s' % (self.filename, self.message)
        else:
            print >>sys.stderr, '%s:%d: Error: %s' % (self.filename, self.line, 
                                                      self.message)

class Profiles(object):
    def __init__(self, keys, data, variables, key_size=None):
        assert isinstance(keys, list)
        assert all(isinstance(k, tuple) for k in keys)
        assert all(isinstance(v, str) for v in variables)
        self._keys = keys
        self.data = np.array(data)
        self.variables = variables
        if key_size is None:
            self.key_size = len(keys[0])
        else:
            self.key_size = key_size

    @classmethod
    def load(cls, filename):
        data = []
        keys = []
        for i, line in enumerate(open(filename).readlines()):
            line = line.rstrip()
            if i == 0:
                headers = line.split('\t')
                try:
                    headers.index('')
                except ValueError:
                    raise InputError(filename, 'Header should be empty for the key columns', i + 1)
                key_size = len(headers) - headers[::-1].index('')
                variables = headers[key_size:]
            else:
                row = line.split('\t')
                key = tuple(row[:key_size])
                values = row[key_size:]
                if len(values) != len(variables):
                    raise InputError(filename, 'Expected %d feature values, found %d' % (len(variables), len(values)), i + 1)
                keys.append(key)
                data.append(map(float, values))
        return cls(keys, np.array(data), variables, key_size)

    def save(self, filename=None):
        header = ['' for i in xrange(self.key_size)] + self.variables
        if isinstance(filename, str):
            f = open(filename, 'w')
        elif filename is None:
            f = sys.stdout
        else:
            f = filename
        try:
            print >>f, '\t'.join(header)
            for key, vector in zip(self._keys, self.data):
                print >>f, '\t'.join(map(str, itertools.chain(key, vector)))
        finally:
            f.close()

    def items(self):
        return itertools.izip(self._keys, self.data)

    def keys(self):
        return self._keys

    def isnan(self):
        return np.any(np.isnan(vector))

    def assert_not_isnan(self):
        for key, vector in self.items():
            assert not np.any(np.isnan(vector)), 'Error: Profile %r has a NaN value.' % key
