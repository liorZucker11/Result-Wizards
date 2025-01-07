#!/usr/bin/env bash
set -x

# Set directory for Chromium
CHROMIUM_DIR=$HOME/chromium
mkdir -p $CHROMIUM_DIR

# Download pre-built Chromium binary
wget -q -O $CHROMIUM_DIR/chromium.tar.xz https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/982481/chrome-linux.zip

# Extract Chromium
tar -xf $CHROMIUM_DIR/chromium.tar.xz -C $CHROMIUM_DIR
