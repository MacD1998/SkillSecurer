#!/usr/bin/env bash
# Auto-generated install script from Doramagic seed resources.packages
set -e

echo 'Installing Doramagic skill dependencies...'

python3 -m pip install numpy
python3 -m pip install pandas
python3 -m pip install scikit-learn
python3 -m pip install scipy
python3 -m pip install statsmodels
python3 -m pip install cython
python3 -m pip install numba
python3 -m pip install POT
python3 -m pip install networkx
python3 -m pip install joblib

echo 'Done. Skill ready to use.'