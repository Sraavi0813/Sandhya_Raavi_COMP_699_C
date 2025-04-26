# HealthyCare Medical Clinic Appointment Scheduling System (MediClinic)

This project is a web-based appointment booking system designed for HealthyCare Medical Clinic. It allows patients to book, reschedule, and cancel appointments online, and helps clinic staff manage doctor availability and appointment scheduling easily.

The system is built using Flask (Python web framework) for the backend, MySQL for the database, and MySQL Connector Python for connecting Flask to the database.

## Dependencies
Before running the system, make sure you have the following installed:

- Python (version 3.x recommended)

- Flask (Python package)

- MySQL Connector Python (Python package for MySQL database connection)

- XAMPP (for MySQL database server and phpMyAdmin)

You can install the required Python packages by running:

`pip install flask mysql-connector-python`

## How to Build the System
- Install Python: Download and install Python from python.org.
- Install XAMPP: Download and install XAMPP from apachefriends.org.
- Setup the Database: Open XAMPP and start Apache and MySQL services.
- Go to http://localhost/phpmyadmin/ in your browser. Import the provided mediclinic.sql file to create the database and necessary tables.
- Install PyCharm (optional but recommended) and create a new Python project.
- Install Required Packages: Open the PyCharm terminal and run:
`pip install flask mysql-connector-python`
- Copy the Project Files: Copy the provided templates/ folder, static/ folder, and app.py file into your PyCharm project.
  
## How to Run the System
- Make sure XAMPP is running (both Apache and MySQL services must be started).
- In your PyCharm terminal (or any terminal), navigate to your project directory and run:
`python app.py`
- Once the app is running, open your browser and go to:
`http://127.0.0.1:5000/`
The HealthyCare Medical Clinic website should now be live locally!

**NB:**
- Make sure the database credentials inside app.py match your local MySQL username and password (default for XAMPP is usually root with no password).
- If you change the database or table names, update the code accordingly.
- For best performance, use a virtual environment (venv) in Python to manage your packages.

