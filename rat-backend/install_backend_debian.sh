#!/bin/sh
apt-get update
apt install chromium
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb &&
dpkg -i google-chrome*.deb &&
rm google-chrome*.deb
source /home/rat-backend/rat/bin/activate
pip install --upgrade pip
pip install pip-review
pip-review --local --auto
pip install wheel
pip install setuptools
pip install psutil
pip install apscheduler
pip install pandas
pip install beautifulsoup4
pip install lxml
pip install -U selenium
pip install psycopg2-binary
pip install -U pytest
pip install pdoc
pip install ipinfo
pip install pytest
pip install selenium-wire
pip install Pillow
deactivate
apt --fix-broken install