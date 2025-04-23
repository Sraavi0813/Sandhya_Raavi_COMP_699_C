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


@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M'):
    if isinstance(value, (datetime,)):
        return value.strftime(format)
    return value  # return as is if not datetime


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

            if staff:
                if staff['status'] != 'active':
                    flash("Your account is currently blocked. Please contact the office manager.", "danger")
                    return redirect(url_for('staff_login'))

                if check_password_hash(staff['password_hash'], password):
                    # Login success
                    session['first_name'] = staff['firstname']
                    session['last_name'] = staff['lastname']
                    session['role'] = staff['role']

                    # Redirect based on role
                    if staff['role'] == 'Doctor':
                        session['doctor_id'] = staff['id']
                        return redirect(url_for('doctor_dashboard'))
                    elif staff['role'] == 'Office Manager':
                        session['officemanager_id'] = staff['id']
                        return redirect(url_for('office_manager_dashboard'))
                    else:
                        flash("Unauthorized Login", "danger")
                        return redirect(url_for('staff_login'))

            flash("Invalid email or password", "danger")
            return redirect(url_for('staff_login'))

    return render_template('staff_login.html')


@app.route('/patient-dashboard')
def patient_dashboard():
    if 'patient_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('patient_login'))

    patient_id = session['patient_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT a.id AS appointment_id, a.appointment_date, a.start_time, a.end_time,
               s.firstname AS doctor_firstname, s.lastname AS doctor_lastname, s.specialization AS specialization 
        FROM appointments a
        JOIN staff s ON a.doctor_id = s.id
        WHERE a.patient_id = %s AND a.status = 'approved'
        ORDER BY a.appointment_date, a.start_time
    """
    cursor.execute(query, (patient_id,))
    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('patient_dashboard.html',
                           first_name=session.get('first_name'),
                           last_name=session.get('last_name'),
                           appointments=appointments)


@app.route('/office-manager-dashboard')
def office_manager_dashboard():
    if 'officemanager_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    today = datetime.now().date()

    appointments = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.id AS appointment_id,
                a.appointment_date AS appointment_date,
                a.start_time,
                a.end_time,
                a.status,
                d.firstname AS doctor_firstname,
                d.lastname AS doctor_lastname,
                p.firstname AS patient_firstname,
                p.lastname AS patient_lastname
            FROM appointments a
            JOIN staff d ON a.doctor_id = d.id
            LEFT JOIN patients p ON a.patient_id = p.id
            WHERE DATE(a.appointment_date) = %s AND a.status = 'approved'
            ORDER BY a.appointment_date ASC
        """
        cursor.execute(query, (today,))
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('office_manager_dashboard.html', appointments=appointments)


@app.route('/doctor-dashboard')
def doctor_dashboard():
    if 'doctor_id' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('staff_login'))

    doctor_id = session['doctor_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch pending (booked) appointments
    query = """
        SELECT a.id AS appointment_id, a.appointment_date, a.start_time, a.end_time,
               p.firstname AS patient_firstname, p.lastname AS patient_lastname
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = %s AND a.status = 'booked'
        ORDER BY a.appointment_date, a.start_time
    """
    cursor.execute(query, (doctor_id,))
    pending_appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('doctor_dashboard.html',
                           first_name=session.get('first_name'),
                           last_name=session.get('last_name'),
                           pending_appointments=pending_appointments)


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

    cursor.execute(
        "SELECT id, firstname, lastname, specialization FROM staff WHERE role = 'Doctor' AND availability ='available' AND status = 'active'")
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

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if time slot is already booked
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

    # Book the appointment
    cursor.execute("""
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s)
    """, (patient_id, doctor_id, date, slot_start, slot_end))

    # Create a notification for the doctor
    # Optionally, fetch patient name if you want more context
    cursor.execute("SELECT firstname, lastname FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    patient_name = f"{patient['firstname']} {patient['lastname']}"

    message = f"New appointment booked by {patient_name} on {date} from {slot_start} to {slot_end}."

    cursor.execute("""
        INSERT INTO notifications (sender_id, receiver_id, sender_role, receiver_role, message)
        VALUES (%s, %s, %s, %s, %s)
    """, (patient_id, doctor_id, 'Patient', 'Doctor', message))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Your appointment has been successfully booked!", "success")
    return redirect(url_for('patient_pending_bookings'))


@app.route('/patient/pending-bookings')
def patient_pending_bookings():
    if 'patient_id' not in session:
        flash("Please log in to view your appointments.", "warning")
        return redirect(url_for('patient_login'))

    patient_id = session['patient_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT a.id AS appointment_id, a.appointment_date, a.start_time, a.end_time, a.status AS appointment_status,
               s.firstname AS doctor_firstname, s.lastname AS doctor_lastname, s.specialization AS specialization FROM appointments a
        JOIN staff s ON a.doctor_id = s.id
        WHERE a.patient_id = %s AND a.status = 'booked'
        ORDER BY a.appointment_date, a.start_time
    """
    cursor.execute(query, (patient_id,))
    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('patient_pending_bookings.html', appointments=appointments)


@app.route('/cancel-appointment/<int:appointment_id>', methods=['POST'])
def patient_cancel_appointment(appointment_id):
    if 'patient_id' not in session:
        flash("Please log in to cancel an appointment.", "warning")
        return redirect(url_for('patient_login'))

    reason = request.form.get('reason', '').strip()

    if not reason:
        flash("Cancellation reason is required.", "danger")
        return redirect(url_for('patient_pending_appointments'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET status = 'cancelled', cancellation_reason = %s
        WHERE id = %s AND patient_id = %s
    """, (reason, appointment_id, session['patient_id']))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Appointment cancelled successfully.", "success")
    return redirect(url_for('patient_cancelled_appointments'))


@app.route('/patient/cancelled-appointments')
def patient_cancelled_appointments():
    if 'patient_id' not in session:
        flash("Please log in to view your appointments.", "warning")
        return redirect(url_for('patient_login'))

    patient_id = session['patient_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT a.id AS appointment_id, a.appointment_date,a.cancellation_reason, a.start_time, a.end_time,
               s.firstname AS doctor_firstname, s.lastname AS doctor_lastname, s.specialization AS specialization, 
                a.status AS appointment_status
        FROM appointments a
        JOIN staff s ON a.doctor_id = s.id
        WHERE a.patient_id = %s AND a.status = 'cancelled'
        ORDER BY a.appointment_date, a.start_time
    """
    cursor.execute(query, (patient_id,))
    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('patient_cancelled_appointments.html', appointments=appointments)


@app.route('/patient/upcoming-appointments')
def patient_upcoming_appointments():
    if 'patient_id' not in session:
        flash("Please log in to view your appointments.", "warning")
        return redirect(url_for('patient_login'))

    patient_id = session['patient_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT a.id AS appointment_id, a.appointment_date, a.start_time, a.end_time,
               s.firstname AS doctor_firstname, s.lastname AS doctor_lastname, s.specialization AS specialization
        FROM appointments a
        JOIN staff s ON a.doctor_id = s.id
        WHERE a.patient_id = %s AND a.status = 'approved'
        ORDER BY a.appointment_date, a.start_time
    """
    cursor.execute(query, (patient_id,))
    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('patient_upcoming_appointments.html', appointments=appointments)


@app.route('/patient/appointments-history')
def patient_previous_appointments():
    if 'patient_id' not in session:
        flash("Please log in to view your appointments.", "warning")
        return redirect(url_for('patient_login'))

    patient_id = session['patient_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT a.id AS appointment_id, a.appointment_date, a.start_time, a.end_time, a.cancellation_reason, a.doctor_notes, a.status AS appointment_status,
               s.firstname AS doctor_firstname, s.lastname AS doctor_lastname, s.specialization AS specialization, 
               a.status AS appointment_status
        FROM appointments a
        JOIN staff s ON a.doctor_id = s.id
        WHERE a.patient_id = %s AND a.status NOT IN ('booked', 'approved')
        ORDER BY a.appointment_date, a.start_time
    """
    cursor.execute(query, (patient_id,))
    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('patient_previous_appointments.html', appointments=appointments)


@app.route('/approve-appointment/<int:appointment_id>')
def approve_appointment(appointment_id):
    if 'doctor_id' not in session:
        flash("Please log in to perform this action.", "warning")
        return redirect(url_for('staff_login'))

    doctor_id = session['doctor_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get appointment info
    cursor.execute("""
        SELECT patient_id, appointment_date, start_time
        FROM appointments
        WHERE id = %s
    """, (appointment_id,))
    appt = cursor.fetchone()

    if not appt:
        flash("Appointment not found.", "danger")
        return redirect(url_for('doctor_dashboard'))

    # Approve the appointment
    cursor.execute("""
        UPDATE appointments
        SET status = 'approved'
        WHERE id = %s
    """, (appointment_id,))

    # Insert notification to patient
    message = f"Your appointment on {appt['appointment_date']} at {appt['start_time']} was approved."
    cursor.execute("""
        INSERT INTO notifications (receiver_id, receiver_role, sender_id, sender_role, message)
        VALUES (%s, 'Patient', %s, 'Doctor', %s)
    """, (appt['patient_id'], doctor_id, message))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Appointment approved successfully.", "success")
    return redirect(url_for('doctor_dashboard'))


@app.route('/disapprove-appointment/<int:appointment_id>')
def disapprove_appointment(appointment_id):
    if 'doctor_id' not in session:
        flash("Please log in to perform this action.", "warning")
        return redirect(url_for('staff_login'))

    doctor_id = session['doctor_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get appointment info
    cursor.execute("""
        SELECT patient_id, appointment_date, start_time
        FROM appointments
        WHERE id = %s
    """, (appointment_id,))
    appt = cursor.fetchone()

    if not appt:
        flash("Appointment not found.", "danger")
        return redirect(url_for('doctor_dashboard'))

    # Disapprove (cancel) the appointment
    cursor.execute("""
        UPDATE appointments
        SET status = 'cancelled'
        WHERE id = %s
    """, (appointment_id,))

    # Insert notification to patient
    message = f"Your appointment on {appt['appointment_date']} at {appt['start_time']} was cancelled by the doctor."
    cursor.execute("""
        INSERT INTO notifications (receiver_id, receiver_role, sender_id, sender_role, message)
        VALUES (%s, 'Patient', %s, 'Doctor', %s)
    """, (appt['patient_id'], doctor_id, message))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Appointment disapproved and marked as cancelled.", "danger")
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/upcoming-appointments')
def doctor_upcoming_appointments():
    if 'doctor_id' not in session:
        flash("Please log in to view your appointments.", "warning")
        return redirect(url_for('staff_login'))

    doctor_id = session['doctor_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT a.id AS appointment_id, a.appointment_date, a.start_time, a.end_time,
               p.firstname AS patient_firstname, p.lastname AS patient_lastname
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = %s AND a.status = 'approved'
        ORDER BY a.appointment_date, a.start_time
    """
    cursor.execute(query, (doctor_id,))
    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('doctor_upcoming_appointments.html', appointments=appointments)


@app.route('/doctor/cancelled-appointments')
def doctor_cancelled_appointments():
    if 'doctor_id' not in session:
        flash("Please log in to view your appointments.", "warning")
        return redirect(url_for('staff_login'))

    doctor_id = session['doctor_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT a.id AS appointment_id, a.appointment_date, a.start_time, a.end_time, a.status AS appointment_status, 
        a.cancellation_reason AS cancellation_reason,
               p.firstname AS patient_firstname, p.lastname AS patient_lastname
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = %s AND a.status = 'cancelled'
        ORDER BY a.appointment_date, a.start_time
    """
    cursor.execute(query, (doctor_id,))
    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('doctor_cancelled_appointments.html', appointments=appointments)


@app.route('/add-notes/<int:appointment_id>', methods=['POST'])
def add_notes(appointment_id):
    if 'doctor_id' not in session:
        flash("Please log in to perform this action.", "warning")
        return redirect(url_for('staff_login'))

    notes = request.form['notes']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET doctor_notes = %s, status = 'completed'
        WHERE id = %s
    """, (notes, appointment_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Notes saved. Appointment marked as completed.", "success")
    return redirect(url_for('doctor_upcoming_appointments'))


@app.route('/cancel-appointment-doc/<int:appointment_id>', methods=['POST'])
def cancel_appointment_by_doctor(appointment_id):
    if 'doctor_id' not in session:
        flash("Please log in to perform this action.", "warning")
        return redirect(url_for('staff_login'))

    reason = request.form['reason']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET status = 'cancelled', cancellation_reason = %s
        WHERE id = %s
    """, (reason, appointment_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Appointment cancelled with reason.", "danger")
    return redirect(url_for('doctor_upcoming_appointments'))


@app.route('/doctor/appointment-history')
def doctor_appointment_history():
    if 'doctor_id' not in session:
        flash("Please log in to view your appointment history.", "warning")
        return redirect(url_for('staff_login'))

    doctor_id = session['doctor_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT a.id AS appointment_id, a.appointment_date, a.cancellation_reason,a.doctor_notes, a.start_time, a.end_time, a.status AS appointment_status,
               a.doctor_notes, a.cancellation_reason,
               p.firstname AS patient_firstname, p.lastname AS patient_lastname
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = %s AND a.status IN ('completed', 'cancelled')
        ORDER BY a.appointment_date DESC, a.start_time
    """
    cursor.execute(query, (doctor_id,))
    history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('doctor_appointment_history.html', history=history)


@app.route('/office-manager/staff')
def manage_staff():
    if 'officemanager_id' not in session:
        flash("Please log in to access staff management.", "warning")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, firstname, lastname, email, phone, role, specialization, status FROM staff")
    staff_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('manage_staff.html', staff_list=staff_list)


@app.route('/office-manager/block-staff/<int:staff_id>')
def block_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE staff SET status = 'blocked' WHERE id = %s", (staff_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Staff has been blocked.", "info")
    return redirect(url_for('manage_staff'))


@app.route('/office-manager/unblock-staff/<int:staff_id>')
def unblock_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE staff SET status = 'active' WHERE id = %s", (staff_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Staff has been unblocked.", "success")
    return redirect(url_for('manage_staff'))


@app.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    if 'officemanager_id' not in session:
        flash("Please log in to manage staff.", "warning")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        phone = request.form['phone']
        email = request.form['email']
        role = request.form['role']
        specialization = request.form.get('specialization') if role == "Doctor" else None

        update_sql = """
            UPDATE staff
            SET firstname = %s, lastname = %s, phone = %s, email = %s, role = %s, specialization = %s
            WHERE id = %s
        """
        cursor.execute(update_sql, (firstname, lastname, phone, email, role, specialization, staff_id))
        conn.commit()

        cursor.close()
        conn.close()

        flash("Staff details updated successfully!", "success")
        return redirect(url_for('manage_staff'))

    # GET: Load existing staff details
    cursor.execute("SELECT * FROM staff WHERE id = %s", (staff_id,))
    staff = cursor.fetchone()
    cursor.close()
    conn.close()

    if not staff:
        flash("Staff not found.", "danger")
        return redirect(url_for('manage_staff'))

    return render_template('edit_staff.html', staff=staff)


@app.route('/doctor/manage-availability')
def manage_doctor_availability():
    if 'officemanager_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, firstname, lastname, specialization, availability FROM staff WHERE role = 'Doctor'")
    doctors = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('manage_doctor_availability.html', doctors=doctors)


@app.route('/doctor/toggle-availability/<int:doctor_id>')
def toggle_availability(doctor_id):
    if 'officemanager_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT availability FROM staff WHERE id = %s", (doctor_id,))
    current_status = cursor.fetchone()[0]

    new_status = 'unavailable' if current_status == 'available' else 'available'

    cursor.execute("UPDATE staff SET availability = %s WHERE id = %s", (new_status, doctor_id))
    conn.commit()

    cursor.close()
    conn.close()

    flash(f"Doctor availability updated to {new_status}.", "success")
    return redirect(url_for('manage_doctor_availability'))


@app.route('/officemanager/upcoming-appointments')
def officemanager_upcoming_appointments():
    if 'officemanager_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    appointments = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.id AS appointment_id,
                a.appointment_date,
                a.start_time,
                a.end_time,
                a.status,
                d.firstname AS doctor_firstname,
                d.lastname AS doctor_lastname,
                p.firstname AS patient_firstname,
                p.lastname AS patient_lastname
            FROM appointments a
            JOIN staff d ON a.doctor_id = d.id
            LEFT JOIN patients p ON a.patient_id = p.id
            WHERE a.status = 'approved'
            ORDER BY a.appointment_date ASC, a.start_time ASC
        """
        cursor.execute(query)
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('officemanager_upcoming_appointments.html', appointments=appointments)

@app.route('/officemanager/cancelled-appointments')
def officemanager_cancelled_appointments():
    if 'officemanager_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    appointments = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.id AS appointment_id,
                a.appointment_date,
                a.cancellation_reason,
                a.start_time,
                a.end_time,
                a.status,
                d.firstname AS doctor_firstname,
                d.lastname AS doctor_lastname,
                p.firstname AS patient_firstname,
                p.lastname AS patient_lastname
            FROM appointments a
            JOIN staff d ON a.doctor_id = d.id
            LEFT JOIN patients p ON a.patient_id = p.id
            WHERE a.status = 'cancelled'
            ORDER BY a.appointment_date ASC, a.start_time ASC
        """
        cursor.execute(query)
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('officemanager_cancelled_appointments.html', appointments=appointments)


@app.route('/officemanager/completed-appointments')
def officemanager_completed_appointments():
    if 'officemanager_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    appointments = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.id AS appointment_id,
                a.appointment_date,
                a.start_time,
                a.end_time,
                a.status,
                d.firstname AS doctor_firstname,
                d.lastname AS doctor_lastname,
                p.firstname AS patient_firstname,
                p.lastname AS patient_lastname
            FROM appointments a
            JOIN staff d ON a.doctor_id = d.id
            LEFT JOIN patients p ON a.patient_id = p.id
            WHERE a.status = 'completed'
            ORDER BY a.appointment_date ASC, a.start_time ASC
        """
        cursor.execute(query)
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('officemanager_completed_appointments.html', appointments=appointments)


@app.route('/doctor/delete-availability/<int:availability_id>', methods=['POST'])
def delete_availability(availability_id):
    if 'doctor_id' not in session:
        flash("Please log in to manage your availability.", "warning")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctor_availability WHERE id = %s AND doctor_id = %s", (availability_id, session['doctor_id']))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Availability deleted successfully.", "success")
    return redirect(url_for('doctor_set_schedule'))

@app.route('/doctor/edit-availability/<int:availability_id>', methods=['GET', 'POST'])
def edit_availability(availability_id):
    if 'doctor_id' not in session:
        flash("Please log in to manage your availability.", "warning")
        return redirect(url_for('staff_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        day_of_week = request.form['day_of_week']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        slot_duration = request.form['slot_duration']

        cursor.execute("""
            UPDATE doctor_availability
            SET day_of_week = %s, start_time = %s, end_time = %s, slot_duration = %s
            WHERE id = %s AND doctor_id = %s
        """, (day_of_week, start_time, end_time, slot_duration, availability_id, session['doctor_id']))
        conn.commit()
        flash("Availability updated successfully.", "success")
        return redirect(url_for('doctor_set_schedule'))

    # GET request: fetch record to prefill form
    cursor.execute("SELECT * FROM doctor_availability WHERE id = %s AND doctor_id = %s", (availability_id, session['doctor_id']))
    record = cursor.fetchone()
    cursor.close()
    conn.close()

    if not record:
        flash("Record not found or unauthorized access.", "danger")
        return redirect(url_for('doctor_set_schedule'))

    return render_template('edit_availability.html', record=record)


@app.route('/doctor/notifications')
def doctor_notifications():
    if 'doctor_id' not in session:
        flash("Please log in to view notifications.", "warning")
        return redirect(url_for('staff_login'))

    doctor_id = session['doctor_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM notifications
        WHERE receiver_id = %s AND receiver_role ='Doctor'
        ORDER BY created_at DESC
    """, (doctor_id,))
    notifications = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('doctor_notifications.html', notifications=notifications)


@app.context_processor
def inject_doctor_notification_count():
    doctor_id = session.get('doctor_id')
    if doctor_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM notifications
            WHERE receiver_id = %s AND receiver_role = 'Doctor'
        """, (doctor_id,))
        unread_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return dict(doctor_unread_notifications=unread_count)
    return dict(doctor_unread_notifications=0)


@app.route('/patient/notifications')
def patient_notifications():
    if 'patient_id' not in session:
        flash("Please log in to view your notifications.", "warning")
        return redirect(url_for('patient_login'))

    patient_id = session['patient_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM notifications
        WHERE receiver_id = %s AND receiver_role = 'Patient'
        ORDER BY created_at DESC
    """, (patient_id,))
    notifications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('patient_notifications.html', notifications=notifications)

@app.context_processor
def inject_patient_notification_count():
    if 'patient_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM notifications
            WHERE receiver_id = %s AND receiver_role = 'Patient'
        """, (session['patient_id'],))

        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return dict(patient_notification_count=count)

    return dict(patient_notification_count=0)


@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')


if __name__ == '__main__':
    app.run(debug=True)
