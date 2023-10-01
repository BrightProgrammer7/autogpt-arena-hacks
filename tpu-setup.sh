#! /bin/bash

sudo apt update
sudo apt upgrade -y

sudo apt python-is-python3 -y
sudo apt install nano
cat >> .bashrc
export PATH="/home/richa/.local/bin:$PATH" 
>> .bashrc
export PATH="/usr/local/bin:/usr/bin:/bin$PATH" 
>> .bashrc <<EOF

source .bashrc

curl https://pyenv.run | bash

pyenv install 3.10.0
pyenv global 3.10.0

curl -sSL https://install.python-poetry.org | python3 -

pip install wheel setuptools
pip install jupyter lab

sudo lsblk
