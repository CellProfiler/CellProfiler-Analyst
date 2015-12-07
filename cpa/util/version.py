'''version.py - Version fetching and comparison.

CellProfiler is distributed under the GNU General Public License,
but this file is licensed under the more permissive BSD license.
See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2011 Broad Institute
All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
'''

import re
import sys
import os.path
import verlib

_cached_description = None

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
            print >>f, '__description__ = "%s"' % git_description

    return git_description or _cached_description

def _parse_description(description):
    if description is None:
        return None
    m = re.match('(.*)-(\d+)-g([0-9a-f]+)$', description)
    if m is None:
        return None
    else:
        return m.groups()

def _get_parsed():
    return _parse_description(_get_description())

def get_display_version(_description=_get_description()):
    tag, additional, commit = _parse_description(_description)
    version = get_normalized_version()
    return '%s (rev. %s)' % (version, commit)

def get_normalized_version(_description=_get_description()):
    """Return the normalized version or None.

    Normalized versions are defined by PEP 386, and are what should go
    in the module's __version__ variable.

    """
    if _description is None:
        return None
    tag, additional, commit = _parse_description(_description)
    if additional == '0':
        s = tag
    else:
        s = tag + '.post' + additional
    return verlib.suggest_normalized_version(s)

def get_bundle_version(_description=_get_description()):
    """Get the MacOS X bundle version.

    The MacOS X bundle version is always three integers separated by
    dots. If our version does not match that (e.g., because we have
    additional commits past a tag), return "0.0.0".

    """
    if _description is None:
        return '0.0.0'
    tag, additional, commit = _parse_description(_description)
    if additional == '0' and re.match('\d+\.\d+\.\d+$', tag):
        return tag
    else:
        return '0.0.0'

def get_commit(_description=_get_description()):
    tag, additional, commit = _parse_description(_description)
    return commit

if __name__ == '__main__':
    if len(sys.argv) == 2:
        description = sys.argv[1]
    elif len(sys.argv) == 1:
        description = _get_description()
    else:
        print >>sys.stderr, "Usage: %s [DESCRIPTION]" % os.path.basename(sys.argv[0])
        sys.exit(64) # EX_USAGE
    print 'Description:', description
    print 'Normalized version:', get_normalized_version(description)
    print 'Bundle version:', get_bundle_version(description)
    print 'Commit:', get_commit(description)
    print 'Display version:', get_display_version(description)
