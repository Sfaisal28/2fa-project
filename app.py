from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import secrets
import time

from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "secret123"


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_db():

    conn = sqlite3.connect('queries.db')
    cur = conn.cursor()

    # Queries table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            contact TEXT NOT NULL,
            query TEXT NOT NULL
        )
    ''')

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


init_db()


# ==========================================
# HOME / LOGIN PAGE
# ==========================================

@app.route('/')
def home():
    return render_template("login.html")


# ==========================================
# REGISTER
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check empty fields
        if not name or not email or not password or not confirm_password:
            return "Please fill all fields"

        # Check password match
        if password != confirm_password:
            return "Passwords do not match"

        conn = sqlite3.connect('queries.db')
        cur = conn.cursor()

        # Check whether email already exists
        cur.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        existing_user = cur.fetchone()

        if existing_user:
            conn.close()
            return "Email already registered. Please login."

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert user
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('register.html')


# ==========================================
# LOGIN
# ==========================================

# ==========================================
# LOGIN
# ==========================================

@app.route('/login', methods=['POST'])
def login():

    username = request.form.get('username')
    password = request.form.get('password')

    conn = sqlite3.connect('queries.db')
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email = ?",
        (username,)
    )

    user = cur.fetchone()

    conn.close()

    if user and check_password_hash(user[3], password):

        session['user_id'] = user[0]
        session['user_name'] = user[1]
        session['user_email'] = user[2]

        # Generate random 6-digit OTP
        otp = str(secrets.randbelow(900000) + 100000)

        # Store OTP and generation time
        session['otp'] = otp
        session['otp_time'] = time.time()

        print("================================")
        print("OTP GENERATED =", otp)
        print("================================")

        return redirect('/otp')

    return "Invalid Email or Password"


# ==========================================
# OTP PAGE
# ==========================================

@app.route('/otp')
def otp():

    if 'user_id' not in session:
        return redirect('/')

    return render_template("otp.html")


# ==========================================
# VERIFY OTP
# ==========================================

@app.route('/verify', methods=['POST'])
def verify():

    entered_otp = request.form.get('otp')

    saved_otp = session.get('otp')
    otp_time = session.get('otp_time')
    attempts = session.get('otp_attempts', 0)

    # OTP exists?
    if not saved_otp or not otp_time:
        return "OTP not found. Please login again."

    # OTP expired?
    if time.time() - otp_time > 60:

        session.pop('otp', None)
        session.pop('otp_time', None)
        session.pop('otp_attempts', None)

        return "OTP expired. Please login again."

    # Check maximum attempts
    if attempts >= 3:

        session.pop('otp', None)
        session.pop('otp_time', None)
        session.pop('otp_attempts', None)

        return "Too many incorrect attempts. Please login again."

    # Correct OTP
    if entered_otp == saved_otp:

        session['authenticated'] = True

        # OTP can be used only once
        session.pop('otp', None)
        session.pop('otp_time', None)
        session.pop('otp_attempts', None)

        return redirect('/dashboard')

    # Wrong OTP
    session['otp_attempts'] = attempts + 1

    remaining = 3 - session['otp_attempts']

    return f"Wrong OTP. Attempts remaining: {remaining}"

# ==========================================
# RESEND OTP
# ==========================================

@app.route('/resend-otp', methods=['POST'])
def resend_otp():

    if 'user_id' not in session:
        return redirect('/')

    mobile = session.get('mobile')

    if not mobile:
        return redirect('/otp')

    # Generate new OTP
    otp = str(secrets.randbelow(900000) + 100000)

    # Store new OTP and new timestamp
    session['otp'] = otp
    session['otp_time'] = time.time()

    print("================================")
    print("NEW OTP GENERATED =", otp)
    print("MOBILE =", mobile)
    print("================================")

    return render_template("verify_otp.html")
# ==========================================
# SEND OTP
# ==========================================

@app.route('/send-otp', methods=['POST'])
def send_otp():

    mobile = request.form.get('mobile')

    # Check mobile number
    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return "Please enter a valid 10-digit mobile number."

    # Store mobile number in session
    session['mobile'] = mobile

    # Generate random 6-digit OTP
    otp = str(secrets.randbelow(900000) + 100000)

    # Store OTP and time
    session['otp'] = otp
    session['otp_time'] = time.time()

    print("================================")
    print("MOBILE =", mobile)
    print("OTP =", otp)
    print("================================")

    return render_template("verify_otp.html")
# ==========================================
# DASHBOARD
# ==========================================

@app.route('/dashboard')
def dashboard():

    if 'authenticated' not in session:
        return redirect('/')

    return render_template("dashboard.html")


# ==========================================
# ASK ANYTHING FORM
# ==========================================

@app.route('/submit_query', methods=['POST'])
def submit_query():

    name = request.form['name']
    email = request.form['email']
    contact = request.form['contact']
    query = request.form['query']

    conn = sqlite3.connect('queries.db')
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO queries (name, email, contact, query) VALUES (?, ?, ?, ?)",
        (name, email, contact, query)
    )

    conn.commit()
    conn.close()

    flash("Query Submitted Successfully!")

    return redirect('/dashboard')


# ==========================================
# VIEW SAVED QUERIES
# ==========================================

@app.route('/view_queries')
def view_queries():

    conn = sqlite3.connect('queries.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM queries")

    data = cur.fetchall()

    conn.close()

    return str(data)


# ==========================================
# LOGOUT
# ==========================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ==========================================
# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )