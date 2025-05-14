 CITS5505 Group Project

## Purpose

This is the repository for our group project, a data analytics application for "project".
## Group Members

| UWA ID   | Name                              | GitHub Username |
|----------|-----------------------------------|-----------------|
| 24371476 | Mallikarjuna Vittalapura Ravi     | Mallicyberdev   |
| 24281642 | Zhenyi Su                         | Mangomigu       |
| 24374395 | Zeke Ding                         | Dzx1025         |
| 24069389 | Dmitry Prytkov                    |                 |

## Setup Instructions

1. Clone the repository

git clone https://github.com/<ORG_OR_USER>/CITS5505-GroupProject-2025.git
cd CITS5505-GroupProject-2025

2. Create and activate a virtual environment
OS / Shell	Commands
Windows (PowerShell)	bash\npython -m venv .venv\n. .\\.venv\\Scripts\\Activate.ps1\n
Windows (CMD)	bash\npython -m venv .venv\n.venv\\Scripts\\activate.bat\n
macOS / Linux	bash\npython3 -m venv .venv\nsource .venv/bin/activate\n

3. Install dependencies

python -m pip install --upgrade pip
pip install python-magic-bin==0.4.27     # Windows libmagic wheel
pip install -r requirements.txt

4. Prepare the database

flask db upgrade

5. Run the application

python run.py

6. Open the application in your web browser

Open http://localhost:5001 in your browser




## Test Instructions

(To be added after development begins.)