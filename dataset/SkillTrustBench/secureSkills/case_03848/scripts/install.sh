#!/usr/bin/env bash
# Auto-generated install script from Doramagic seed resources.packages
set -e

echo 'Installing Doramagic skill dependencies...'

python3 -m pip install 'numpy>=1.17.3'
python3 -m pip install 'pandas>=1.1.5'
python3 -m pip install torch
python3 -m pip install 'stable-baselines3[extra]>=2.0.0a5'
python3 -m pip install elegantrl
python3 -m pip install 'ray[default,tune]>=2.0'
python3 -m pip install gymnasium
python3 -m pip install pandas_market_calendars
python3 -m pip install 'stockstats>=0.4.0'
python3 -m pip install 'pyfolio-reloaded>=0.9'

echo 'Done. Skill ready to use.'