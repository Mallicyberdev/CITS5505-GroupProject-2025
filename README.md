# CITS5505 Group Project

## Purpose

This repository contains a data analytics web application developed for the CITS5505 group project. The application is a diary management system that allows users to create, edit, view, and share diary entries. It incorporates emotion analysis using a transformer-based model (j-hartmann/emotion-english-distilroberta-base) to analyze the emotional content of diary entries. The application is built using Flask, a Python web framework, and includes user authentication, session management, and a responsive front-end styled with Bootstrap and custom CSS. The primary purpose is to provide users with a platform to record personal diary entries, analyze their emotional tone, and share entries securely with other registered users.

## Design and Use

1. User Authentication: Users can register, log in, and log out securely using Flask-Login and WTForms for form validation. Passwords are hashed using Werkzeug's security utilities.

2. Diary Management: Authenticated users can create, edit, view, and delete diary entries. Each entry includes a title, content, and metadata such as creation and update timestamps.

3. Emotion Analysis: Upon creating or editing a diary entry, the content is analyzed for emotional tone using a pre-trained transformer model. The dominant emotion and its score are stored, along with a JSON object containing all emotion scores.

4. Sharing Functionality: Users can share their diary entries with other registered users, with access control to ensure only authorized users can view shared entries.

5. Responsive UI: The front-end is designed with Bootstrap and custom CSS, featuring a clean, modern interface with support for both light and dark modes. Key pages include a homepage, diary creation/editing forms, and a dashboard for viewing owned and shared diaries.

6. Database: SQLite is used for simplicity in development, with SQLAlchemy and Flask-Migrate handling database operations and migrations.

The application is intended for personal use, allowing users to reflect on their emotions through diary entries while providing a secure and user-friendly interface.

## Group Members

| UWA ID   | Name                          | GitHub Username |
|----------|-------------------------------|-----------------|
| 24371476 | Mallikarjuna Vittalapura Ravi | Mallicyberdev   |
| 24281642 | Zhenyi Su                     | Mangomigu       |
| 24374395 | Zeke Ding                     | Dzx1025         |
| 24069389 | Dmitry Prytkov                | gambit0070      |

## Setup Instructions

1. Clone the Repository:
    git clone <repository-url>

2. Set Up a Virtual Environment:
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Dependencies: Ensure you have Python 3.8+ installed. Then, install the required packages:
    python.exe -m pip install --upgrade pip 
    pip install -r requirements.txt

4. Prepare the database
    flask db upgrade

5. Launch the Application:
    python run.py

6. Open http://localhost:5001 in your browser

## Test Instructions



