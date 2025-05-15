CITS5505 Group Project

## Purpose

**MoodDiary** is a web-based emotional journaling platform that enables users to reflect on their thoughts while
automatically analyzing mood patterns over time.

The application provides:

- A secure and user-friendly interface for creating personal diary entries
- Integrated sentiment analysis using natural language processing (NLP)
- Visual representations of emotional trends to support mental health awareness
- Entry sharing with role-based access for trusted collaborators
- A responsive design, ensuring accessibility across devices

This website has been constructed as coursework for the **CITS5505 Agile Web Development** unit at the **University of
Western Australia**.
It stands as proof of our commitment to applying agile principles to real issues in digital self-care and health.

## Design

Authentication & Security
Registration, login, and logout are securely accessible to users. Sessions are managed by Flask-Login, and input
validation is performed by WTForms. Passwords are stored safely by hashing them with Werkzeug.

User Interface
The interface is built with Bootstrap and CSS, giving a responsive layout that supports both desktop and mobile usage.
Light/dark theme support and simple homepage, dashboard, and diary editor layouts have been included in the application.

Diary Entry System
Successful authentication allows users to add, modify, read, and delete their own diary entries. An entry has a title, a
free-form body, and automatically filled timestamp for creation and last update.

Entry Sharing
Users have the option to share specific diary entries with other registered users. Access control is provided so that
only authorized users can see shared content.

Emotion Detection with NLP
When an entry is saved, its text is processed by a pre-trained transformer model to detect emotional tone. The system
stores the overall emotion label and score, along with the full emotion profile in JSON format.

## Group Members

| UWA ID   | Name                          | GitHub Username |
|----------|-------------------------------|-----------------|
| 24371476 | Mallikarjuna Vittalapura Ravi | Mallicyberdev   |
| 24281642 | Zhenyi Su                     | Mangomigu       |
| 24374395 | Zeke Ding                     | Dzx1025         |
| 24069389 | Dmitry Prytkov                | Gambit0070      |

## Project Structure

```text
CITS5505-GroupProject-2025/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── extensions.py        # Flask extensions
│   ├── auth/                # Authentication blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── data_handling/       # Diary handling blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── analysis.py
│   ├── main/                # Main routes blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── static/              # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/           # HTML templates
│       ├── auth/
│       ├── diary/
│       └── main/
├── migrations/              # Database migrations
├── tests/                   # Test files
├── .gitignore
├── config.py                # Configuration settings
├── requirements.txt         # Project dependencies
└── run.py                   # Application entry point
```

## Setup Instructions

1. Clone the repository

   ```bash
   git clone https://github.com/Mallicyberdev/CITS5505-GroupProject-2025.git
   cd CITS5505-GroupProject-2025
   ```

2. Create and activate a virtual environment

    - Windows(PowerShell)
    ```bash
    python -m venv .venv
    . .\\.venv\\Scripts\\Activate.ps1
    ```

    - Windows(CMD)
    ```bash
    python -m venv .venv
    .venv\\Scripts\\activate.bat
    ```

    - macOS / Linux bash
    ```bash
      python3 -m venv .venv
      source .venv/bin/activate\n
    ```

3. Install dependencies

   ```bash
   python -m pip install --upgrade pip   
   pip install -r requirements.txt
   ```

4. Prepare the database

   ```bash
   flask db upgrade
   ```

5. Run the application

   ```bash
   python run.py
   ```

6. Open the application in your web browser

   Open http://localhost:5001 in your browser

## Test Instructions

Unit Tests

The project includes Python unit tests to verify authentication, diary creation, editing, deletion, sharing, and access
control. These tests are located in tests/test_app.py and use pytest with the pytest-flask plugin.

Prerequisites and Running Unit Tests:

1. Complete the Setup Instructions above (clone repository, activate virtual environment, install dependencies, prepare
   database).

2. Ensure pytest, pytest-flask, and pytest-cov are installed (included in requirements.txt).

3. Run the unit tests: pytest tests/test_app.py

4. Run tests with coverage report: pytest --cov=app tests/test_app.py

Notes:

Tests use an in-memory SQLite database (sqlite:///:memory:) to avoid modifying instance/app.db.

If tests fail, check the Troubleshooting section for dependency or database issues.

Warnings can be suppressed by adding to pytest.ini

## Troubleshooting

Permission is denied when creating .venv

	Close any IDE or terminal that might be using the folder. Delete the .venv folder manually, then retry the python -m venv .venv command as administrator. On PowerShell, you may also need: 
                                                                       Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

Model download is extremely slow or interrupted

	Make sure  no firewall/proxy blocking requests to Hugging Face. You can retry pip install -r requirements.txt or clear ~/.cache/huggingface.

App starts but shows Internal Server Error Check the console traceback.

     The most common cause is missing dependencies.

Changes to models are not reflected in the database
Run migrations again:

```bash
flask db migrate -m
flask db upgrade
```

App runs, but nothing happens at <localhost:5001>
Ensure the app has fully started without exceptions. Try visiting http://127.0.0.1:5001 instead. If you're in VSCode,
check if the debugger is holding the port.
