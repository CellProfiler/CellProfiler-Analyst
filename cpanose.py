"""
CellProfiler Analyst is distributed under the GNU General Public
License.  See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2013 Broad Institute
All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
"""

import nose
import sys

import numpy as np
np.seterr(all='ignore')

def dummy_start_vm(args, run_headless=False):
    pass

if '--noguitests' in sys.argv:
    sys.argv.remove('--noguitests')
    sys.modules['wx'] = None
    import matplotlib
    matplotlib.use('agg')

if '--nojavatests' in sys.argv:
    sys.argv.remove('--nojavatests')
    import javabridge
    javabridge.start__vm = dummy_start_vm

if len(sys.argv) == 0:
    args = ['--testmatch=(?:^)test_.*']
else:
    args = sys.argv

nose.main(argv=args + ['-w', 'cpa/tests'])
