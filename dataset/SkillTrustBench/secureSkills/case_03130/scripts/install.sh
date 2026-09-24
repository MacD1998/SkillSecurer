#!/usr/bin/env bash
# Auto-generated install script from Doramagic seed resources.packages
set -e

echo 'Installing Doramagic skill dependencies...'

python3 -m pip install py_lets_be_rational
python3 -m pip install numpy
python3 -m pip install scipy
python3 -m pip install pandas
python3 -m pip install simplejson
python3 -m pip install numba
python3 -m pip install pytest
python3 -m pip install sphinx
python3 -m pip install sphinx_rtd_theme
python3 -m pip install recommonmark

echo 'Done. Skill ready to use.'