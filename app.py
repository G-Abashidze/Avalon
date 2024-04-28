from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import json
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash, check_password_hash
import os



app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", 'supersecretkey')

# Database connection details
DB_NAME = "avalon"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"

# Connect to the PostgreSQL database
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        return conn
    except Exception as e:
        app.logger.error(f"Database connection failed: {e}")
        return None


@app.route('/')
def index():
    return 'Welcome to the Home Page'


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password, method='sha256')

        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed. Please try again later.", 'error')
            return render_template('register.html')

        with conn.cursor() as cur:
            try:
                insert_query = sql.SQL("INSERT INTO users (username, password) VALUES (%s, %s)")
                cur.execute(insert_query, (username, hashed_password))
                conn.commit()
                flash('Registration successful!', 'success')
                # Here, you could set a session variable to indicate incomplete authorization
                session['authorized'] = False  # User registered but not authorized
                return redirect(url_for('complete_authorization'))  # Redirect to complete authorization
            except Exception as e:
                conn.rollback()
                app.logger.error(f"Registration error: {e}")
                flash("Registration failed. Please try again.", 'error')

        conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed. Please try again later.", 'error')
            return render_template('login.html')

        with conn.cursor() as cur:
            select_query = sql.SQL("SELECT password FROM users WHERE username = %s")
            cur.execute(select_query, (username,))
            result = cur.fetchone()

        conn.close()

        if result:
            stored_hash = result[0]
            if check_password_hash(stored_hash, password):
                # After successful login, set session to track authorization
                session['username'] = username
                session['authorized'] = True  # Example: User is authorized after login
                flash("Login successful!", 'success')
                return redirect(url_for('home'))
            else:
                flash("Incorrect password. Please try again.", 'error')
        else:
            flash("Username not found. Please register first.", 'error')
    session["activeSessions"] = pd.read_sql("select * from avalonsessions", get_db_connection()).to_json()
    
    return render_template('login.html')



@app.route('/home')
def home():
    # Redirect if the user is not authorized
    if 'authorized' not in session or not session['authorized']:
        flash("You must complete authorization to access this page.", 'error')
        return redirect(url_for('complete_authorization'))
    
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT SessionName FROM AvalonSessions")
        sessions = cur.fetchall()  # Fetch all results
        

    conn.close()
    username = session['username']
    
    


    return render_template('home.html', username=username)  # Pass the username to the template


@app.route('/complete_authorization', methods=['GET', 'POST'])
def complete_authorization():
    if request.method == 'POST':
        # Example authorization step, like email verification, profile completion, etc.
        # After completing authorization, set 'authorized' to True
        session['authorized'] = True
        flash("Authorization complete!", 'success')
        return redirect(url_for('home'))

    return render_template('complete_authorization.html')  # Provide a form to complete authorization


@app.route('/logout')
def logout():
    # Clear session to log out the user
    session.pop('username', None)
    session.pop('authorized', None)  # Clear authorization status
    flash("Logged out successfully.", 'success')
    return redirect(url_for('login'))


@app.route('/create-session', methods=['POST'])
def create_session():
    session_name = request.form['sessionName']  # Get the submitted session name

    conn = get_db_connection()
    if conn is None:
        flash("Database connection failed. Please try again later.", 'error')
        return redirect(url_for('index'))

    with conn.cursor() as cur:
        try:
            insert_query = sql.SQL("insert into avalonSessions (guid, sessionname, eventtime) VALUES (gen_random_uuid (), %s, NOW() );")  # Insert session into SQL
            cur.execute(insert_query, (session_name,))
            conn.commit()  # Commit the transaction
            flash(f"Session '{session_name}' created successfully!", 'success')
        except Exception as e:
            conn.rollback()  # Rollback on error
            app.logger.error(f"Error creating session: {e}")
            flash("Could not create session. Please try again.", 'error')

    conn.close()

    return redirect(url_for('home'))  # Redirect to the desired page after creation


if __name__ == '__main__':
    app.run(debug=True)
