from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Configurations
app.config['SECRET_KEY'] = 'hjhfhdbbfhgjhfgjhg'

# MySQL database configuration
db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'mediclinic'
}


# Function to connect to MySQL
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def patient_registration():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate password match
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('patient_registration'))

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT email FROM patients WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Email is already registered!", "warning")
                cursor.close()
                conn.close()
                return redirect(url_for('patient_registration'))

            # Hash password
            hashed_password = generate_password_hash(password)

            # Insert new patient record
            sql = "INSERT INTO patients (firstname, lastname, phone, email, password_hash) VALUES (%s, %s, %s, %s, %s)"
            values = (firstname, lastname, phone, email, hashed_password)
            cursor.execute(sql, values)
            conn.commit()

            cursor.close()
            conn.close()

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('patient_login'))
    return render_template('patient_registration.html')


@app.route('/login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM patients WHERE email = %s", (email,))
            patient = cursor.fetchone()

            cursor.close()
            conn.close()

            if patient and check_password_hash(patient['password_hash'], password):
                # Login success
                session['patient_id'] = patient['id']
                session['first_name'] = patient['firstname']
                session['last_name'] = patient['lastname']
                flash(f"Welcome back, {patient['firstname']}!", "success")
                return redirect(url_for('patient_dashboard'))  # Replace with your dashboard route

            else:
                flash("Invalid email or password", "danger")
                return redirect(url_for('patient_login'))

    return render_template('patient_login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('patient_login'))


@app.route('/staff-logout')
def staff_logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('staff_login'))


@app.route('/staff/register', methods=['GET', 'POST'])
def staff_registration():
    if 'staff_id' not in session:
        flash("Please log in to register staff.", "warning")
        return redirect(url_for('staff_login'))

    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        # Password match validation
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('staff_registration'))

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)

            # Check for duplicate email
            cursor.execute("SELECT * FROM staff WHERE email = %s", (email,))
            existing_staff = cursor.fetchone()
            if existing_staff:
                flash("Email is already registered!", "warning")
                cursor.close()
                conn.close()
                return redirect(url_for('staff_registration'))

            hashed_password = generate_password_hash(password)

            # Insert into staff table
            sql = """
                INSERT INTO staff (firstname, lastname, phone, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (firstname, lastname, phone, email, hashed_password, role))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Staff registered successfully!", "success")
            return redirect(url_for('staff_registration'))

    return render_template('staff_registration.html')


@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM staff WHERE email = %s", (email,))
            staff = cursor.fetchone()

            cursor.close()
            conn.close()

            if staff and check_password_hash(staff['password_hash'], password):
                # Login success
                session['staff_id'] = staff['id']
                session['first_name'] = staff['firstname']
                session['last_name'] = staff['lastname']
                session['role'] = staff['role']
                # Redirect based on role
                if staff['role'] == 'Doctor':
                    return redirect(url_for('doctor_dashboard'))  # You can create this route
                elif staff['role'] == 'Office Manager':
                    return redirect(url_for('office_manager_dashboard'))  # You can create this route
                else:
                    flash("Unauthorized Login", "danger")
                    return redirect(url_for('staff_login'))

            else:
                flash("Invalid email or password", "danger")
                return redirect(url_for('staff_login'))

    return render_template('staff_login.html')


@app.route('/patient-dashboard')
def patient_dashboard():
    if 'patient_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('patient_login'))

    return render_template('patient_dashboard.html',
                           first_name=session.get('first_name'),
                           last_name=session.get('last_name'))


@app.route('/office-manager-dashboard')
def office_manager_dashboard():
    if 'staff_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('staff_login'))
    return render_template('office_manager_dashboard.html')


@app.route('/doctor-dashboard')
def doctor_dashboard():
    if 'staff_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('staff_login'))

    return render_template('doctor_dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)
