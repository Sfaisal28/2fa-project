from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# Database Create
def init_db():
    conn = sqlite3.connect('queries.db')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            contact TEXT NOT NULL,
            query TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# Home Page
@app.route('/')
def home():
    return render_template("login.html")

# Login Route

@app.route('/login', methods=['POST'])
def login():

    username = request.form.get('username')
    password = request.form.get('password')

    print("Username:", username)
    print("Password:", password)

    if username == "syed" and password == "2802":

        otp = "0113"
        session['otp'] = otp

        print("================================")
        print("OTP GENERATED =", otp)
        print("================================")

        return redirect('/otp')

    return "Invalid Username or Password"

# OTP Page
@app.route('/otp')
def otp():
    return render_template("otp.html")

# Verify OTP
@app.route('/verify', methods=['POST'])
def verify():

    entered_otp = request.form.get('otp')

    if entered_otp == session.get('otp'):
        return redirect('/dashboard')

    return "Wrong OTP"

# Dashboard
@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

# Ask Anything Form Submit
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

# View Saved Queries
@app.route('/view_queries')
def view_queries():

    conn = sqlite3.connect('queries.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM queries")
    data = cur.fetchall()

    conn.close()

    return str(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
  