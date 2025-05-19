from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import numpy as np
import sklearn
import os
import pickle
import warnings
import sqlite3
from datetime import datetime

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'your-secret-key-here'  # Required for flash messages and session

loaded_model = pickle.load(open("model.pkl", 'rb'))

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE,
                  password TEXT,
                  username TEXT,
                  dob TEXT,
                  mobile TEXT,
                  favorite_color TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if user and user[2] == password:  # Check if password matches
            session['user_id'] = user[0]
            session['username'] = user[3]  # Store username in session
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        username = request.form.get('username')
        dob = request.form.get('dob')
        mobile = request.form.get('mobile')
        favorite_color = request.form.get('favorite_color')
        
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('signup'))
        
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (email, password, username, dob, mobile, favorite_color) VALUES (?, ?, ?, ?, ?, ?)',
                     (email, password, username, dob, mobile, favorite_color))
            conn.commit()
            conn.close()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'error')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        dob = request.form.get('dob')
        mobile = request.form.get('mobile')
        favorite_color = request.form.get('favorite_color')
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ? AND dob = ? AND mobile = ? AND favorite_color = ?',
                 (email, dob, mobile, favorite_color))
        user = c.fetchone()
        conn.close()
        
        if user:
            # Here you would typically send a password reset email
            # For now, we'll just show a success message
            flash('Security questions verified. Please check your email for password reset instructions.', 'success')
            session['user_id'] = user[0]
            session['username'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            flash('Security details do not match. Please try again.', 'error')
        return redirect(url_for('forgot_password'))
    
    return render_template('forgot_password.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    N = int(request.form['Nitrogen'])
    P = int(request.form['Phosporus'])
    K = int(request.form['Potassium'])
    temp = float(request.form['Temperature'])
    humidity = float(request.form['Humidity'])
    ph = float(request.form['pH'])
    rainfall = float(request.form['Rainfall'])

    feature_list = [N, P, K, temp, humidity, ph, rainfall]
    single_pred = np.array(feature_list).reshape(1, -1)

    prediction = loaded_model.predict(single_pred)
    crop = prediction[0]
    result = f"{crop} is the best crop to be cultivated right there"

    return render_template('home.html', prediction=result)

if __name__ == '__main__':
    # Ensure the static/images directory exists
    os.makedirs('static/images', exist_ok=True)
    app.run(debug=True)
