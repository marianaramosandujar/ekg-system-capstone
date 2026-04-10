EKG System Setup Instructions (Windows)
These instructions are for setting up and running the EKG system on Windows.
OPTION ONE:


Window/Linux users:
Download Python here before starting: https://www.python.org/downloads/release/python-3133/

1. Click the code button above and click download zip.
2. In your file explore it, extract the entire folder.
3. Open the folder the folder named ekg_system_capstone, and find the file called
    **setup_and_run.bat**
4. Double click that file and it should start up.

Mac Users: 
Download Python here before starting: https://www.python.org/downloads/release/python-3133/
1. Click the Code button above and click Download ZIP.
2. In Finder, locate the downloaded ZIP file and extract the entire folder.
3. Open the extracted folder named ekg_system_capstone.
4. Find the file called **setup_and_run_mac.sh.**
5. Right click the file and select Open With then Terminal (or open Terminal and navigate to the folder).
6. In terminal, run this once to allow execution
**chmod +x setup_and_run_mac.sh**
7. then type this in your terminal window
**./setup_and_run_mac.sh**
then application will start up.

OPTION 2 TO DOWNLOAD IF MORE FAMILIAR WITH GIT:
Make sure your device has Python and Git already installed, if not, follow these instructions. 
 Download the latest version of Python in this link https://www.python.org/downloads/
 Download the latest version of Git https://git-scm.com/install/

1. Clone the repository in the terminal window of your device, type this.

**git clone https://github.com/marianaramosandujar/ekg-system-capstone.git**

2. Move into this folder, in your terminal type this
 
  **cd ekg-system-capstone**


3. Create and activate virtual environment, in your terminal type this.

   
If windows or Linux, type this

**python -m venv venv venv\Scripts\activate**

If Mac, type this
**python3 -m venv venv venv\Scripts\activate** 


4. Install dependencies by typing this into your terminal.

Windows - **pip install -r requirements.txt** 

Mac- **pip3 install -r requirements.txt**

5. Run the UI
For Windows - **python ui_main.py**

For Mac - **python3 ui_main.py**


