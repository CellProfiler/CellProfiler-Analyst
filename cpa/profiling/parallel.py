import logging
import itertools
from optparse import OptionGroup

logger = logging.getLogger(__name__)

class ParallelProcessor(object):
    """
    A ParallelProcessor has a method view() that takes an optional
    keyword argument "name".  This method returns a view.  A view is
    an object that has an imap method.

    """

    @classmethod
    def add_options(cls, parser):
        group = OptionGroup(parser, 'Parallel processing options (specify only one)')
        group.add_option('--ipython-profile', dest='ipython_profile', 
                         metavar='PROFILE-NAME',
                         help='use iPython.parallel')
        group.add_option('--lsf-directory', dest='lsf_directory', 
                         metavar='/path/to/control/directory',
                         help='use the cpa.profiling.lsf interface to LSF')
        group.add_option('--multiprocessing', dest='multiprocessing', 
                         help='use multiprocessing on the local machine', 
                         action='store_true')
        group.add_option('--memory', dest='memory',
                         help='main memory requirement in gigabytes')
        parser.add_option_group(group)

    @classmethod
    def create_from_legacy(cls, ipython_profile):
        """For backwards compatibility, return a parallel profile
        based on an argument that can be an LSF objct, an ipython
        profile name, False, or None."""
        if isinstance(ipython_profile, LSF):
            import LSF
        elif ipython_profile:
            from IPython.parallel import Client, LoadBalancedView
            client = Client(profile=ipython_profile)
            return IPython(client)
            return view.imap
        elif ipython_profile == False:
            return Uniprocessing()
        else:
            return Multiprocessing()

    @classmethod
    def create_from_options(cls, parser, options):
        noptions = ((options.ipython_profile and 1 or 0) +
                    (options.lsf_directory and 1 or 0) + 
                    (options.multiprocessing and 1 or 0))
        if noptions > 1:
            parser.error('You can only specify one of --ipython-profile, --lsf-directory, and --multiprocessing.')
        if options.lsf_directory:
            import lsf
            return lsf.LSF(50, options.lsf_directory, memory=options.memory)
        elif options.ipython_profile:
            from IPython.parallel import Client, LoadBalancedView
            client = Client(profile=options.ipython_profile)
            return IPython(client)
        elif options.multiprocessing:
            return Multiprocessing()
        else:
            return Uniprocessing()


class IPython(ParallelProcessor):
    def __init__(self, client):
        self.client = client

    def view(self, name=None):
        logger.debug('%s: %d iPython engines' % (name, len(self.client.ids)))
        return self.client.load_balanced_view()


class Multiprocessing(ParallelProcessor):
    def view(self, name=None):
        from multiprocessing import Pool, cpu_count
        import threading
        logging.debug('%s: %d multiprocessing processes' % (name, cpu_count()))
        return Pool()


class Uniprocessing(ParallelProcessor):
    def view(self, name=None):
        logging.debug('%s: 1 sequential process' % name)
        return UniprocessingView()

class UniprocessingView(object):
    imap = itertools.imap

def test_function((seconds)):
    import time
    time.sleep(seconds)
    return seconds

def test():
    from optparse import OptionParser
    import random

    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    ParallelProcessor.add_options(parser)
    options, args = parser.parse_args()
    parallel = ParallelProcessor.create_from_options(parser, options)
    view = parallel.view('foo')
    for result in view.imap(test_function, [random.randint(1, 10)
                                            for task in range(10)]):
        print 'Task returned', result
    
if __name__ == '__main__':
    test()
