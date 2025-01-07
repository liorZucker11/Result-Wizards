#!/usr/bin/env bash
# Exit on error
set -o errexit

# Persistent storage directory for Chrome
STORAGE_DIR=/opt/render/project/.render

if [[ ! -d $STORAGE_DIR/chrome ]]; then
  echo "...Downloading Chrome version 114"
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome

  # Download Chrome version 114
  wget -q -O chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.198-1_amd64.deb

  # Extract the Chrome binary
  dpkg -x chrome.deb $STORAGE_DIR/chrome

  # Clean up
  rm chrome.deb
  cd $HOME/project/src # Return to the project directory
else
  echo "...Using Chrome from cache"
fi
