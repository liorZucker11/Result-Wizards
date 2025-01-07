#!/usr/bin/env bash
# Exit on error
set -o errexit

# Persistent storage directory for Chrome
STORAGE_DIR=/opt/render/project/.render

if [[ ! -d $STORAGE_DIR/chrome ]]; then
  echo "...Downloading Chrome"
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome

  # Download Chrome
  wget -q -O chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

  # Extract the Chrome binary
  dpkg -x chrome.deb $STORAGE_DIR/chrome

  # Clean up
  rm chrome.deb
  cd $HOME/project/src # Return to the project directory
else
  echo "...Using Chrome from cache"
fi
