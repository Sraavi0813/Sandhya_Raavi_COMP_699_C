from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import time, datetime, timedelta

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


@app.template_filter('time_format')
def time_format(value):
    if isinstance(value, time):
        return value.strftime('%H:%M')
    try:
        return value.strftime('%H:%M')
    except Exception:
        return str(value)


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
    if 'officemanager_id' not in session:
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
        specialization = request.form.get('specialization') if role == "Doctor" else None

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('staff_registration'))

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM staff WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email is already registered!", "warning")
                cursor.close()
                conn.close()
                return redirect(url_for('staff_registration'))

            hashed_password = generate_password_hash(password)

            sql = """
                INSERT INTO staff (firstname, lastname, phone, email, password_hash, role, specialization)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (firstname, lastname, phone, email, hashed_password, role, specialization))
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

                session['first_name'] = staff['firstname']
                session['last_name'] = staff['lastname']
                session['role'] = staff['role']
                # Redirect based on role
                if staff['role'] == 'Doctor':
                    session['doctor_id'] = staff['id']
                    return redirect(url_for('doctor_dashboard'))  # You can create this route
                elif staff['role'] == 'Office Manager':
                    session['officemanager_id'] = staff['id']
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
    if 'officemanager_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('staff_login'))
    return render_template('office_manager_dashboard.html')


@app.route('/doctor-dashboard')
def doctor_dashboard():
    if 'doctor_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('staff_login'))

    return render_template('doctor_dashboard.html')


@app.route('/set-schedule')
def doctor_set_schedule():
    if 'doctor_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('staff_login'))

    doctor_id = session['doctor_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM doctor_availability WHERE doctor_id = %s ORDER BY FIELD(day_of_week, 'Monday',"
                   "'Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')", (doctor_id,))
    availability_records = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('doctor_set_availability.html', availability_records=availability_records)


@app.route('/doctor/set-availability', methods=['GET', 'POST'])
def doctor_set_availability():
    if 'doctor_id' not in session:
        flash("Please log in to manage your availability.", "warning")
        return redirect(url_for('staff_login'))

    if request.method == 'POST':
        doctor_id = session['doctor_id']
        day_of_week = request.form['day_of_week']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        slot_duration = int(request.form['slot_duration'])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration)
            VALUES (%s, %s, %s, %s, %s)
        """, (doctor_id, day_of_week, start_time, end_time, slot_duration))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Availability added successfully!", "success")
        return redirect(url_for('doctor_set_schedule'))

    # This renders the page normally if it's a GET request
    return render_template('doctor_set_availability.html')


@app.route('/manage-availability')
def doctor_manage_availability():
    if 'doctor_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('staff_login'))

    doctor_id = session['doctor_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM doctor_availability WHERE doctor_id = %s ORDER BY FIELD(day_of_week, 'Monday',"
                   "'Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')", (doctor_id,))
    availability_records = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('doctor_manage_availability.html', availability_records=availability_records)


# BEGINNING OF APPOINTMENT SCHEDULING ROUTES

@app.route('/appointment/select-doctor')
def select_doctor():
    if 'patient_id' not in session:
        flash("Please log in to book an appointment.", "warning")
        return redirect(url_for('patient_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, firstname, lastname, specialization FROM staff WHERE role = 'Doctor'")
    doctors = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('select_doctor.html', doctors=doctors)


@app.route('/appointment/select-slot/<int:doctor_id>')
def select_slot(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get doctor info
    cursor.execute("SELECT id, firstname, lastname, specialization FROM staff WHERE id = %s", (doctor_id,))
    doctor = cursor.fetchone()

    # Get doctor availability
    cursor.execute("""
        SELECT * FROM doctor_availability
        WHERE doctor_id = %s
    """, (doctor_id,))
    availabilities = cursor.fetchall()

    # Get booked appointments
    cursor.execute("""
        SELECT appointment_date, start_time FROM appointments
        WHERE doctor_id = %s
    """, (doctor_id,))
    booked = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('select_slot.html', doctor=doctor, availabilities=availabilities, booked=booked)


@app.route('/appointment/select-time/<int:doctor_id>', methods=['GET', 'POST'])
def select_time_slot(doctor_id):
    if 'patient_id' not in session:
        flash("Please log in to schedule an appointment.", "warning")
        return redirect(url_for('patient_login'))

    available_slots = []
    selected_date = None

    if request.method == 'POST':
        selected_date_str = request.form['appointment_date']
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        day_of_week = selected_date.strftime('%A')  # e.g. "Monday"

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Get doctor's availability for that weekday
        cursor.execute("""
            SELECT * FROM doctor_availability
            WHERE doctor_id = %s AND day_of_week = %s
        """, (doctor_id, day_of_week))
        availability = cursor.fetchone()

        if availability:
            # Ensure these are cast to time objects if needed
            start_time_db = availability['start_time']
            end_time_db = availability['end_time']

            if isinstance(start_time_db, timedelta):
                start_time_db = (datetime.min + start_time_db).time()
            if isinstance(end_time_db, timedelta):
                end_time_db = (datetime.min + end_time_db).time()

            start_time = datetime.combine(selected_date, start_time_db)
            end_time = datetime.combine(selected_date, end_time_db)
            slot_duration = timedelta(minutes=availability['slot_duration'])

            # 2. Get all booked appointments for that doctor on selected date
            # 2. Get all booked appointments for that doctor on selected date
            cursor.execute("""
                SELECT start_time FROM appointments
                WHERE doctor_id = %s AND appointment_date = %s
            """, (doctor_id, selected_date))
            booked = cursor.fetchall()

            booked_slots = []
            for b in booked:
                time_value = b['start_time']
                if isinstance(time_value, timedelta):
                    time_value = (datetime.min + time_value).time()
                booked_slots.append(datetime.combine(selected_date, time_value))

            # 3. Generate all possible slots
            current = start_time
            while current + slot_duration <= end_time:
                if current not in booked_slots:
                    slot = {
                        'start': current.time(),
                        'end': (current + slot_duration).time()
                    }
                    available_slots.append(slot)
                current += slot_duration

        cursor.close()
        conn.close()

    return render_template('patient_select_time_slot.html', doctor_id=doctor_id,
                           available_slots=available_slots, selected_date=selected_date)


@app.route('/book-appointment/<doctor_id>/<date>', methods=['POST'])
def book_appointment(doctor_id, date):
    if 'patient_id' not in session:
        flash("Please log in to book an appointment.", "warning")
        return redirect(url_for('patient_login'))

    patient_id = session['patient_id']
    slot_start = request.form['slot_start']
    slot_end = request.form['slot_end']

    # Check if the selected time slot is already booked
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM appointments
        WHERE doctor_id = %s
        AND appointment_date = %s
        AND start_time = %s AND end_time = %s
    """, (doctor_id, date, slot_start, slot_end))

    existing_appointment = cursor.fetchone()
    if existing_appointment:
        flash("This time slot has already been booked. Please choose another time.", "danger")
        return redirect(url_for('select_time_slot', doctor_id=doctor_id, selected_date=date))

    # If slot is available, create a new appointment
    cursor.execute("""
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s)
    """, (patient_id, doctor_id, date, slot_start, slot_end))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Your appointment has been successfully booked!", "success")
    return redirect(url_for('patient_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
