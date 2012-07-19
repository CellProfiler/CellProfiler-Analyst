import sys
import itertools
import logging
import numpy as np
from .parallel import ParallelProcessor

# compress is new in Python 2.7
if not hasattr(itertools, 'compress'):
    itertools.compress = lambda data, selectors: (d for d, s in itertools.izip(data, selectors) if s)

logger = logging.getLogger(__name__)

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
    def __init__(self, keys, data, variables, key_size=None, group_name=None):
        assert isinstance(keys, list)
        assert all(isinstance(k, tuple) for k in keys)
        assert all(isinstance(v, str) for v in variables)
        self._keys = [tuple(map(str, t)) for t in keys]
        assert ~np.any(np.isnan(data))
        self.data = np.array(data)
        self.variables = variables
        if key_size is None:
            self.key_size = len(keys[0])
        else:
            self.key_size = key_size
        self.group_name = group_name

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
                    key_size = len(headers) - headers[::-1].index('')
                except ValueError:
                    key_size = 1
                for h in headers[1:key_size]:
                    if h != '':
                        raise InputError(filename, 'Header should be empty for the key columns, except for the first, which should contain the group name', i + 1)
                variables = headers[key_size:]
                group_name = headers[0]
            else:
                row = line.split('\t')
                key = tuple(row[:key_size])
                values = row[key_size:]
                if len(values) != len(variables):
                    raise InputError(filename, 'Expected %d feature values, found %d' % (len(variables), len(values)), i + 1)
                keys.append(key)
                data.append(map(float, values))
        return cls(keys, np.array(data), variables, key_size, group_name=group_name)

    @classmethod
    def load_csv(cls, filename):
        import csv
        reader = csv.reader(open(filename))
        data = []
        keys = []
        for i, row in enumerate(reader):
            if i == 0:
                headers = row
                try:
                    headers.index('')
                    key_size = len(headers) - headers[::-1].index('')
                except ValueError:
                    key_size = 1
                for h in headers[1:key_size]:
                    if h != '':
                        raise InputError(filename, 'Header should be empty for the key columns, except for the first, which should contain the group name', i + 1)
                variables = headers[key_size:]
                group_name = headers[0]
            else:
                key = tuple(row[:key_size])
                values = row[key_size:]
                if len(values) != len(variables):
                    raise InputError(filename, 'Expected %d feature values, found %d' % (len(variables), len(values)), i + 1)
                keys.append(key)
                data.append(map(float, values))
        return cls(keys, np.array(data), variables, key_size, group_name=group_name)

    def header(self):
        header = ['' if self.group_name is None else self.group_name] + \
            [''] * (self.key_size - 1) + self.variables
        assert len(header) == self.key_size + self.data.shape[1]
        return header

    def save(self, filename=None):
        header = self.header()
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

    def save_csv(self, filename=None):
        import csv
        header = self.header()
        if isinstance(filename, str):
            f = open(filename, 'w')
        elif filename is None:
            f = sys.stdout
        else:
            f = filename
        try:
            w = csv.writer(f)
            w.writerow(header)
            for key, vector in zip(self._keys, self.data):
                w.writerow(tuple(key) + tuple(vector))
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

    @classmethod
    def compute(cls, keys, variables, function, parameters, parallel=None,
                ipython_profile=None, group_name=None, show_progress=True):
        """
        Compute profiles by applying the parameters to the function in parallel.

        """
        assert len(keys) == len(parameters)
        njobs = len(parameters)
        parallel = parallel or ParallelProcessor.create_from_legacy(ipython_profile)
        generator = parallel.view('profiles.compute').imap(function, parameters)
        if show_progress:
            import progressbar
            progress = progressbar.ProgressBar(widgets=[progressbar.Percentage(), ' ',
                                                        progressbar.Bar(), ' ', 
                                                        progressbar.Counter(), '/', 
                                                        str(njobs), ' ',
                                                        progressbar.ETA()],
                                               maxval=njobs)
        else:
            progress = lambda x: x
        data = list(progress(generator))

        if all([l is None for l in data]):
            print "No data returned! Not generating a Profile class"
            return
        
        for i, (p, r) in enumerate(zip(parameters, data)):
            if r is None:
                logger.info('Retrying failed computation locally')
                data[i] = function(p)

        rowmask = [(l != None) and all(~np.isnan(l)) for l in data]
        import itertools
        data = list(itertools.compress(data, rowmask))
        keys = list(itertools.compress(keys, rowmask))

        return cls(keys, data, variables, group_name=group_name)


def add_common_options(parser):
    parser.add_option('--normalization', help='normalization method (default: RobustLinearNormalization)',
                      default='RobustLinearNormalization')
    parser.add_option('--preprocess', dest='preprocess_file', 
                      help='model to preprocess with (default: none)')
