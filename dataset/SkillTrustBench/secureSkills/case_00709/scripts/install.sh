#!/usr/bin/env bash
# Auto-generated install script from Doramagic seed resources.packages
set -e

echo 'Installing Doramagic skill dependencies...'

python3 -m pip install pandas
python3 -m pip install numpy
python3 -m pip install scikit-learn
python3 -m pip install scipy
python3 -m pip install zipline-reloaded
python3 -m pip install pyfolio-reloaded
python3 -m pip install alphalens-reloaded
python3 -m pip install empyrical-reloaded
python3 -m pip install backtrader
python3 -m pip install quandl

echo 'Done. Skill ready to use.'