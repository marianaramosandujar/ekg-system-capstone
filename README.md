EKG System Setup Instructions (Windows)
These instructions are for setting up and running the EKG system on Windows.


1. Download the latest version of Python in this link https://www.python.org/downloads/
2. Download the latest version of Git https://git-scm.com/install/

2. Clone the repository in the terminal window of your device, type this.

**git clone https://github.com/marianaramosandujar/ekg-system-capstone.git **

4. Move into this folder, in your terminal type this
 
  **cd ekg-system-capstone **

7. In your terminal, type this

  ** git checkout testing-branch**

9. Create and activate virtual environment, in your terminal type this.

   
If windows or Linux, type this **python -m venv venv venv\Scripts\activate**

If Mac, type this **python3 -m venv venv venv\Scripts\activate** 


8. Install dependencies by typing this into your terminal.

Windows -** pip install -r requirements.txt **

Mac  - ** pip3 install -r requirements.txt**

10. Run the UI
For Windows - **python ui_main.py**
For Mac - **python3 ui_main.py**


