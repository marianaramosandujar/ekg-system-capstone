#!/bin/bash
set -e

echo "Setting up EKG System..."

python3 -m venv venv
source venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install --no-compile -r requirements.txt

python3 ui_main.py