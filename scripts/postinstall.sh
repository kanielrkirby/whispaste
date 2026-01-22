#!/bin/sh
set -e
echo "Installing Python dependencies via pip..."
pip3 install --break-system-packages openai python-dotenv sounddevice numpy pyperclip 2>/dev/null || \
pip3 install openai python-dotenv sounddevice numpy pyperclip
