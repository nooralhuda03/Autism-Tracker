Autism Spectrum Disorder (ASD) Tracking and Evaluation System

This is a comprehensive web application built on the Flask framework, designed to facilitate the tracking and evaluation of behavioral patterns in children with Autism Spectrum Disorder (ASD). The system aims to effectively bridge the communication and data exchange between parents (Mothers) and attending physicians.

 Core Features

 Doctor Dashboard

Patient Management: Detailed overview and listing of patients associated with the doctor.

Daily Appointment Management: Filtering capability to display only patients with booked appointments for the current day.

Appointment Completion: Toggle switch (or button) linked to an AJAX request to update the appointment status from booked to completed.

Filtering: Integrated filtering for patient name search and appointment status.

 Mother Dashboard

Daily Assessment: A structured interface divided into 6 distinct axes for evaluating daily behavior (Communication, Social Interaction, Self-Regulation, Daily Habits, etc.).

Appointment System:

Dynamic retrieval of available appointment slots via AJAX.

Instant UI Update (Dual UI Update): Instant booking removes the slot from the available list and immediately adds it to the list of booked appointments.

Persistent Storage: Booked appointments are permanently retrieved and displayed upon subsequent page loads, thanks to correct data handling via the ChildAppointment table.

Design: A calm and user-friendly interface using a Unified Pastel Gradient Theme.

 Technology Stack 

Backend Framework: Flask (Python)

Database ORM: Flask-SQLAlchemy

Frontend: Jinja2, HTML5, Bootstrap 5.3

Styling: Custom CSS & Pastel Gradient Theme

Charting: Chart.js (For performance reports)

Version Control: Git / GitHub

Installation and Setup Guide 
To run this application locally, follow the steps below:

Prerequisites

Python (3.12)

Git

1. Clone the Repository

Open your terminal or command prompt and execute:

git clone [https://github.com/nooralhuda03/Autism-Tracker.git](https://github.com/nooralhuda03/Autism-Tracker.git)
cd Autism-Tracker


2. Environment Setup and Dependencies (إعداد البيئة)

It is highly recommended to use a virtual environment:

# Create a virtual environment
python -m venv .venv

# Activate the environment (Example for Windows)
.venv\Scripts\activate

# Install core dependencies (ensure you have the corresponding file/packages)
pip install Flask Flask-SQLAlchemy Jinja2 python-dotenv


3. Database Initialization 

Ensure your database connection settings are configured (e.g., in app.py or .env).

Create the necessary database tables (you may need to run Flask-Migrate commands if using Alembic, e.g., flask db upgrade).

4. Run the Application (تشغيل التطبيق)

python app.py


The application will typically be accessible at: http://127.0.0.1:5000

 Design and Theme Philosophy 
The project utilizes a Pastel Gradient theme throughout all primary user interfaces (Login, Mother Dashboard, Doctor Dashboard) to create a relaxed, comfortable, and unified user experience suitable for child health and development tracking.
