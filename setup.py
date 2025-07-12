import codecs
import os
import re

import setuptools.dist

import cpa.util.version


def read(*directories):
    pathname = os.path.abspath(os.path.dirname(__file__))

    return codecs.open(os.path.join(pathname, *directories), "r").read()


def find_version(*pathnames):
    data = read(*pathnames)

    matched = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", data, re.M)

    if matched:
        return matched.group(1)

    raise RuntimeError("Unable to find version string.")


def package_data():
    resources = []

    for root, _, filenames in os.walk(os.path.join("cellprofiler", "data")):
        resources += [
            os.path.relpath(os.path.join(root, filename), "cellprofiler")
            for filename in filenames
        ]

    for root, _, filenames in os.walk(os.path.join("cellprofiler", "gui")):
        resources += [
            os.path.relpath(os.path.join(root, filename), "cellprofiler")
            for filename in filenames
            if ".html" in filename
        ]

    return {"cellprofiler": resources}


setuptools.setup(
    app=['CellProfiler-Analyst.py'],
    author="Broad Institute",
    author_email="imagingadmin@broadinstitute.org",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering",
    ],
    # entry_points={"console_scripts": ["cellprofiler-analyst=CellProfiler-Analyst.__main__:main"]},
    extras_require={
        "build": ["pyinstaller"],
    },
    install_requires=[
        "boto3~=1.28.33",
        "botocore~=1.31.33",
        "imagecodecs>=2021.2.26",
        "imageio>=2.9.0",
        "joblib>=1.0.1",
        "matplotlib~=3.7.2",
        "mock>=4.0.3",
        "mysqlclient==1.4.6",
        "numpy~=1.23.4",
        "pandas~=2.0.3",
        "Pillow~=10.3.0",
        "progressbar>=2.5",
        "python-bioformats~=4.0.7",
        "python-javabridge==4.0.4",
        "pytz>=2021.1",
        "requests>=2.25.1",
        "scikit-learn~=0.24.2",
        "scipy~=1.9.0",
        "seaborn~=0.13.2",
        "tifffile==2022.4.8",
        "verlib==0.1",
        "wxPython~=4.2.0",
    ],
    license="BSD",
    name="CellProfiler-Analyst",
    package_data=package_data(),
    include_package_data=True,
    packages=setuptools.find_packages(exclude=["tests*"]),
    python_requires=">=3.8",
    setup_requires=["pytest"],
    url="https://github.com/CellProfiler/CellProfiler-Analyst",
    version=cpa.util.version.__version__,
    windows=[{'script': 'CellProfiler-Analyst.py',
              'icon_resources': [(1, '.\cpa\icons\cpa.ico')]}],

)
