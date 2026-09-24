#!/usr/bin/env bash
# Auto-generated install script from Doramagic seed resources.packages
set -e

echo 'Installing Doramagic skill dependencies...'

python3 -m pip install pandas==1.5.3
python3 -m pip install numpy==1.24.4
python3 -m pip install 'matplotlib>=2'
python3 -m pip install requests==2.31.0
python3 -m pip install 'scipy>=1.3.0'
python3 -m pip install 'scikit-learn>1.4.2'
python3 -m pip install 'pytest>=8.3'

echo 'Done. Skill ready to use.'