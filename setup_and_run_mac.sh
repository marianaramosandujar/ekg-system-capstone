#!/bin/bash

echo "Setting up EKG System..."

python3 -m venv venv
source venv/bin/activate

python3 -m pip install --upgrade pip
pip install -r requirements.txt

python3 ui_main.py