from distutils.core import setup
import py2exe
import matplotlib

setup(console=['ClassifierGUI.py'],
      options={
        'py2exe': {
            'packages' : ['matplotlib', 'pytz'],
            }
        },
      data_files=matplotlib.get_py2exe_datafiles(),
)



