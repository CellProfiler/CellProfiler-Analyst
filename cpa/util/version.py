'''version.py - Version fetching and comparison.

CellProfiler Analyst is distributed under the GNU General Public License,
but this file is licensed under the more permissive BSD license.
See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2021 Broad Institute

All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofileranalyst.org
'''


import re
import sys
import os.path

_cached_description = None

__version__ = '3.0.4' # Version used by update checker, must be in format "N.N.N"
_sub_version = '' # Use this to tag release candidates, betas, etc.

display_version = __version__ + _sub_version

def _get_description():
    """Get description from git or file system.

    If we're not frozen and this is a git repository, try to get the
    description by running ``git describe``, then store it in
    javabridge/_description.py. Otherwise, try to load the description
    from that file. If both methods fail, quietly return None.

    """
    global _cached_description
    git_description = None
    if (not hasattr(sys, 'frozen') and 
        os.path.exists(os.path.join(os.path.dirname(__file__), '..', '..',
                                    '.git'))):
        import subprocess
        try:
            git_description = subprocess.Popen(['git', 'describe', '--long'], 
                                               stdout=subprocess.PIPE).communicate()[0].strip()
        except:
            pass

    description_file = os.path.join(os.path.dirname(__file__), '..',
                                '_description.py')
    if os.path.exists(description_file):
        with open(description_file) as f:
            cached_description_line = f.read().strip()
        try:
            # From http://stackoverflow.com/a/3619714/17498
            _cached_description = re.search(r"^__description__ = ['\"]([^'\"]*)['\"]", 
                                            cached_description_line, re.M).group(1)
        except:
            raise RuntimeError("Unable to find description in %s" % description_file)
    else:
        _cached_description = None

    if git_description and git_description != _cached_description:
        with open(description_file, 'w') as f:
            print('__description__ = "%s"' % git_description, file=f)

    return git_description or _cached_description

def _parse_description(description):
    if description is None:
        return None
    m = re.match('(.*)-(\d+)-g([0-9a-f]+)$', description)
    if m is None:
        return None
    else:
        return m.groups()

def get_commit(_description=_get_description()):
    tag, additional, commit = _parse_description(_description)
    return commit

if __name__ == '__main__':
    if len(sys.argv) == 2:
        description = sys.argv[1]
    elif len(sys.argv) == 1:
        description = _get_description()
    else:
        print("Usage: %s [DESCRIPTION]" % os.path.basename(sys.argv[0]), file=sys.stderr)
        sys.exit(64) # EX_USAGE
    print('Description:', description)
    print('Version:', __version__)
    print('Commit:', get_commit(description))
