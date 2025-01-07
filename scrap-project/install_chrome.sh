#!/usr/bin/env bash
set -x

# Download Chrome for Linux
CHROME_DIR="/opt/chrome"
mkdir -p $CHROME_DIR
wget -q -O $CHROME_DIR/chrome-linux.zip https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get -y install libnss3 libnspr4 libxss1 fonts-liberation libappindicator3-1 xdg-utils libgbm-dev
# Unzip and make Chrome executable
dpkg -i chrome.deb

