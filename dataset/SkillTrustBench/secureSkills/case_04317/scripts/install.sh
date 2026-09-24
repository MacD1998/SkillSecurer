#!/usr/bin/env bash
# Auto-generated install script from Doramagic seed resources.packages
set -e

echo 'Installing Doramagic skill dependencies...'

python3 -m pip install 'cvxpy>=1.1.19'
python3 -m pip install 'numpy>=1.26.0,<3.0.0'
python3 -m pip install 'pandas>=1.0.0,<4.0.0'
python3 -m pip install 'scipy>=1.3.0'
python3 -m pip install 'scikit-learn>=0.24.1'
python3 -m pip install 'scikit-base<0.14.0'
python3 -m pip install 'matplotlib>=3.2.0'
python3 -m pip install 'plotly>=5.0.0,<7'
python3 -m pip install 'ecos>=2.0.14,<2.1'
python3 -m pip install cvxopt

echo 'Done. Skill ready to use.'