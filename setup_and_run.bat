@echo off
echo Setting up EKG System...

python -m venv venv
call venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

python ui_main.py

pause