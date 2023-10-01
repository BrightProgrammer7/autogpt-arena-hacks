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

gcloud compute disks create diskodisk --size 300 --type pd-balanced --replica-zones us-central1-f

gcloud alpha compute tpus tpu-vm attach-disk --zone "us-central1-f" "tpu-vm" --project "bakobiibizo-b8d9f" --disk "disk-mikes"

sudo lsblk