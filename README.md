EKG System Setup Instructions (Windows)
These instructions are for setting up and running the EKG system on Windows.


1. Download the latest version of Python in this link https://www.python.org/downloads/
2. Download the latest version of Git https://git-scm.com/install/

2. Clone the repository
Make sure Git and Python are installed.
In the terminal window of your device, type this.

git clone https://github.com/marianaramosandujar/ekg-system-capstone.git 

4. Move into this folder - **cd ekg-system-capstone **

5. git checkout testing-branch

6. Create and activate virtual environment
python -m venv venv venv\Scripts\activate or python3 -m venv venv venv\Scripts\activate depends on your device. 

7. Install dependencies
pip install -r requirements.txt
or pip3 install -r requirements.txt

8. Run the UI
python ui_main.py


