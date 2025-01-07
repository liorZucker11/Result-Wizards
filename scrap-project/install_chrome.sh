#!/usr/bin/env bash
set -x

# Set up Chromium directory
CHROMIUM_DIR=$HOME/chromium
mkdir -p $CHROMIUM_DIR

# Download a verified headless Chromium binary for Linux
wget -q -O $CHROMIUM_DIR/chromium.zip https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-55/stable-headless-chromium.tar.gz

# Extract the Chromium binary
tar -xvzf $CHROMIUM_DIR/chromium.zip -C $CHROMIUM_DIR
