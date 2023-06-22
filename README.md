# CS3200: RecipeMaster

## Installation

Ensure you have the most up to date [Python version installed](https://www.python.org/downloads/) (3.11+) as well as [PIP](https://pip.pypa.io/en/stable/installation/) to install the packages needed to run this application. You may also wish to initialize a virtual environment to run this project. If so, run `pip install virtualenv` (if you do not already have it installed) then `python -m venv env` in this directory. Finally, if you are on MacOS or Linux, run `source env/bin/activate` in this directory to activate it. If you are on Windows, run `.\venv\Scripts\activate` instead in this directory.

Once you are prepared to begin installing the main packages, in this directory run

```bash
pip install -r requirements.txt
```

This will ensure all the necessary packages are properly installed.

You will need to have a local MySQL server active on your machine to continue.

To initialize the MySQL database schema and functions, simply run the database dump file (`YoungTDatabaseDump.sql`) in MySQL Workbench or another SQL editor. You will use the credentials to your local server to log in at the start of the application.

## Running

Within this directory, run

```bash
python source.py
```

to start the application.

From there, enjoy using RecipeMaster!
