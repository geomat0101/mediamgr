# mediamgr
software for managing media libraries

This assumes python3 and virtualenv / virtualenvwrapper are installed and configured properly

## Initial virtual environment setup
* `mkvirtualenv mediamgr`
* `workon mediamgr` (fyi you're going to want to configure vscode to use this venv at some point too)
* `pip install ffmpeg-python jsonschema numpy python-arango pytest`

## System cuda / dlib dependencies (if not installed already)
* cuda (GPU) support: [install cuda keyring](https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=Ubuntu&target_version=22.04&target_type=deb_network)
* `sudo apt install libx11-dev, cuda, libcudnn8-dev`

## Build / Install dlib
* `git clone https://github.com/davisking/dlib`
* `cd dlib/`
* `python setup.py install`
* read the top of the build output where it's performing installed software checks.  Abort the build and install system packages if anything is missing (blas, lapack, ffmpeg, etc.  Individual symbols not found are ok and normal, but if it tells you you're missing an installed system package go fix it).  If the build completed, use pip remove dlib to nuke it.  rm -rf the dlib/build directory and restart the build to try again.
* run the example in mediamgr/python/examples

## Install the local project in editable mode
* `pip -e .`  while in the directory containing this README

The output of `pip list` should look something like this:
```
(mediamgr) mdg@ftl:~/src/mediamgr/python$ pip list
Package             Version  Editable project location
------------------- -------- -----------------------------
attrs               23.1.0
certifi             2023.5.7
charset-normalizer  3.1.0
dlib                19.24.99
exceptiongroup      1.1.1
ffmpeg-python       0.2.0
future              0.18.3
idna                3.4
iniconfig           2.0.0
jsonschema          4.17.3
mediamgr_geomat0101 0.0.1    /path/to/geomat0101/mediamgr/python
numpy               1.24.3
packaging           23.1
pip                 22.0.2
pluggy              1.0.0
PyJWT               2.7.0
pyrsistent          0.19.3
pytest              7.3.1
python-arango       7.5.7
requests            2.30.0
requests-toolbelt   1.0.0
setuptools          59.6.0
tomli               2.0.1
urllib3             2.0.2
wheel               0.37.1
```
