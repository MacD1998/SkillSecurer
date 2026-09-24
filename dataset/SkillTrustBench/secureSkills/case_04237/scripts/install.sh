#!/usr/bin/env bash
# Auto-generated install script from Doramagic seed resources.packages
set -e

echo 'Installing Doramagic skill dependencies...'

python3 -m pip install 'click >=7.0'
python3 -m pip install 'python-dateutil >=2.6.0'
python3 -m pip install 'regex >=2022.9.13'
python3 -m pip install 'flex / winflexbison-bin >=2.6.4'
python3 -m pip install 'bison-bin / winflexbison-bin >=3.8.0'
python3 -m pip install 'meson >=1.2.1'
python3 -m pip install 'meson-python >=0.14.0'
python3 -m pip install pytest
python3 -m pip install mypy
python3 -m pip install types-python-dateutil

echo 'Done. Skill ready to use.'