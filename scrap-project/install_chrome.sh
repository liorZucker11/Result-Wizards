#!/usr/bin/env bash
set -x

# Set directory for Chromium
CHROMIUM_DIR=$HOME/chromium
mkdir -p $CHROMIUM_DIR

# Download pre-built Chromium binary
wget -q -O $CHROMIUM_DIR/chromium.zip https://github.com/macchrome/winchrome/releases/download/v113.0.5672.63-r1077478-Win64/ChromiumPortable_113.0.5672.63-r1077478-win64.7z

# Extract Chromium
unzip $CHROMIUM_DIR/chromium.zip -d $CHROMIUM_DIR
