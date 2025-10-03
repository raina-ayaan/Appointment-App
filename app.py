from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from datetime import timedelta, date
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# MySQL Config
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
mysql_port = os.getenv('MYSQL_PORT')
app.config['MYSQL_PORT'] = int(mysql_port)

# Mail Config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
mail_port = os.getenv('MAIL_PORT')
app.config['MAIL_PORT'] = int(mail_port)
mail_use_tls = os.getenv('MAIL_USE_TLS')
if isinstance(mail_use_tls, str):
    app.config['MAIL_USE_TLS'] = mail_use_tls.lower() in ['true', '1', 'yes']
else:
    app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mysql = MySQL(app)
mail = Mail(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        slot = request.form['slot']
        interview_date = request.form['interview_date']
        
        # Validate date format
        try:
            selected_date = datetime.datetime.strptime(interview_date, '%Y-%m-%d').date()
            # Don't allow bookings in the past
            if selected_date < date.today():
                flash("Cannot book appointments in the past!", "danger")
                return redirect(url_for('index'))
        except ValueError:
            flash("Invalid date format!", "danger")
            return redirect(url_for('index'))

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM bookings WHERE slot=%s AND interview_date=%s", (slot, interview_date))
        if cur.fetchone():
            flash("Slot already booked for this date!", "danger")
            return redirect(url_for('index'))

        cur.execute("INSERT INTO bookings (name, email, phone, slot, interview_date) VALUES (%s, %s, %s, %s, %s)", 
                    (name, email, phone, slot, interview_date))
        mysql.connection.commit()

        msg = Message('Interview Slot Confirmation',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        formatted_date = datetime.datetime.strptime(interview_date, '%Y-%m-%d').strftime('%A, %B %d, %Y')
        msg.body = f"Hello {name},\n\nYour interview is scheduled on {formatted_date} at {slot}.\n\nBest of luck!"
        mail.send(msg)

        flash("Appointment booked and email sent!", "success")
        return redirect(url_for('index'))    # Default to today's date for initial slot display
    today = date.today().strftime('%Y-%m-%d')
    
    slots = generate_slots()
    booked = get_booked_slots(today)
    
    # Calculate date 3 months from now for max date
    max_date = (date.today() + timedelta(days=90)).strftime('%Y-%m-%d')
    
    return render_template('index.html', slots=slots, booked=booked, 
                         default_date=today, max_date=max_date,
                         title="Book a Mock Interview")

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin' not in session:
        return redirect(url_for('login'))

    # Handle cancellation POST
    if request.method == 'POST' and 'cancel_id' in request.form:
        cancel_id = request.form['cancel_id']
        cur = mysql.connection.cursor()
        cur.execute("SELECT name, email, slot, interview_date FROM bookings WHERE id=%s", (cancel_id,))
        booking = cur.fetchone()
        if booking:
            name, email, slot, interview_date = booking
            cur.execute("DELETE FROM bookings WHERE id=%s", (cancel_id,))
            mysql.connection.commit()
            try:
                formatted_date = interview_date
                if isinstance(interview_date, (datetime.date, datetime.datetime)):
                    formatted_date = interview_date.strftime('%A, %B %d, %Y')
                msg = Message('Interview Slot Cancelled',
                              sender=app.config['MAIL_USERNAME'],
                              recipients=[email])
                msg.body = f"Hello {name},\n\nYour interview scheduled on {formatted_date} at {slot} has been cancelled by the admin.\nIf you have any questions, please contact us."
                mail.send(msg)
                flash(f"Interview for {name} on {formatted_date} at {slot} cancelled and email sent.", "success")
            except Exception as e:
                flash(f"Interview cancelled, but failed to send email: {str(e)}", "danger")
        else:
            flash("Booking not found.", "danger")
        return redirect(url_for('admin'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bookings ORDER BY interview_date, slot")
    bookings = cur.fetchall()

    today = datetime.date.today()
    upcoming = []
    completed = []
    for booking in bookings:
        booking_list = list(booking)
        # booking[5] is interview_date
        # Handle different possible date formats
        if isinstance(booking[5], str):
            try:
                date_obj = datetime.datetime.strptime(booking[5], '%Y-%m-%d').date()
            except ValueError:
                date_obj = booking[5]
        else:
            date_obj = booking[5]
        # Format the date for display
        if isinstance(date_obj, str):
            booking_list[5] = date_obj  # Already formatted
        else:
            booking_list[5] = date_obj.strftime('%A, %B %d, %Y')
        # Separate upcoming and completed
        if isinstance(date_obj, str):
            try:
                date_cmp = datetime.datetime.strptime(date_obj, '%A, %B %d, %Y').date()
            except Exception:
                date_cmp = today
        else:
            date_cmp = date_obj
        if date_cmp >= today:
            upcoming.append(booking_list)
        else:
            completed.append(booking_list)

    return render_template('admin.html', upcoming_bookings=upcoming, completed_bookings=completed, title="Admin Dashboard")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM admin WHERE username='admin'")
        stored_hash = cur.fetchone()
        if stored_hash and check_password_hash(stored_hash[0], password):
            session['admin'] = True
            flash("Login successful!", "success")
            return redirect(url_for('admin'))
        else:
            flash("Invalid password", "danger")
    return render_template('login.html', title="Admin Login")

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

def generate_slots():
    base = datetime.datetime.strptime("08:00", "%H:%M")
    slots = [(base + datetime.timedelta(minutes=40*i)).strftime("%H:%M") 
             for i in range(12)]  # From 8:00 to 15:20
    return slots

def get_booked_slots(selected_date=None):
    cur = mysql.connection.cursor()
    if selected_date:
        cur.execute("SELECT slot FROM bookings WHERE interview_date=%s", (selected_date,))
    else:
        cur.execute("SELECT slot FROM bookings")
    result = cur.fetchall()
    return [r[0] for r in result]

# Function removed as we now use a native calendar input

@app.route('/get_available_slots', methods=['GET'])
def get_available_slots():
    """API endpoint to get available slots for a specific date"""
    selected_date = request.args.get('date')
    
    if not selected_date:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        # Validate date format
        datetime.datetime.strptime(selected_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    slots = generate_slots()
    booked = get_booked_slots(selected_date)
    
    available_slots = []
    for slot in slots:
        available_slots.append({
            'time': slot,
            'available': slot not in booked
        })
    
    return jsonify({'slots': available_slots})
if __name__ == '__main__':
    app.run(debug=True)