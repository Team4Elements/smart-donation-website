from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3, random, hashlib

app = Flask(__name__)
app.secret_key = "super_secret_key_here"

# ==============================================================
# 📧 EMAIL CONFIGURATION
# ==============================================================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '4elements.fontys@gmail.com'
app.config['MAIL_PASSWORD'] = 'fojk hqsu ocwj qyid'
app.config['MAIL_DEFAULT_SENDER'] = '4elements.fontys@gmail.com'

mail = Mail(app)

# ==============================================================
# 🗂️ DATABASE SETUP
# ==============================================================
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL, message TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, feedback TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS donors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, food_bank_name TEXT NOT NULL, address TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS needed_items (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT NOT NULL, description TEXT, urgency TEXT DEFAULT 'Medium')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS dropoff_locations (id INTEGER PRIMARY KEY AUTOINCREMENT, location_name TEXT NOT NULL, address TEXT NOT NULL, hours TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS volunteer_roles (id INTEGER PRIMARY KEY AUTOINCREMENT, role_title TEXT NOT NULL, description TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS volunteers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT, role_id INTEGER, FOREIGN KEY (role_id) REFERENCES volunteer_roles(id))''')
    conn.commit()
    conn.close()

# ==============================================================
# 🔐 PASSWORD SECURITY
# ==============================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, given_password):
    return stored_password == hashlib.sha256(given_password.encode()).hexdigest()

# ==============================================================
# 🏠 CORE & STATIC PAGES
# ==============================================================
@app.route('/')
def home():
    user = session.get('user')
    user_type = session.get('user_type')
    return render_template('index.html', user=user, user_type=user_type)

@app.route('/about')
def about():
    user = session.get('user')
    user_type = session.get('user_type')
    return render_template('about.html', user=user, user_type=user_type)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash("💚 Your message has been sent successfully!", "success")
        return redirect(url_for('home'))
    user = session.get('user')
    user_type = session.get('user_type')
    return render_template('contact.html', user=user, user_type=user_type)

# ==============================================================
# 👤 USER LOGIN & REGISTER
# ==============================================================
@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = hash_password(request.form['password'])
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        conn.commit()
        flash("✅ Account created successfully! You can now log in.", "success")
    except sqlite3.IntegrityError:
        flash("⚠️ This email already exists.", "error")
    finally:
        conn.close()
    return redirect(url_for('login_page'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    if user and verify_password(user[3], password):
        session['user'] = user[1]
        session['email'] = user[2]
        session['user_type'] = 'user'
        flash(f"Welcome back, {user[1]}!", "success")
        return redirect(url_for('account'))
    else:
        flash("❌ Invalid email or password.", "error")
        return redirect(url_for('login_page'))

# ==============================================================
# 🏦 DONOR (FOOD BANK) LOGIN & REGISTER
# ==============================================================
@app.route('/login_page_donor')
def login_page_donor():
    return render_template('login_donor.html')

@app.route('/register_donor', methods=['GET', 'POST'])
def register_donor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hash_password(request.form['password'])
        food_bank_name = request.form['food_bank_name']
        address = request.form['address']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO donors (name, email, password, food_bank_name, address) VALUES (?, ?, ?, ?, ?)", (name, email, password, food_bank_name, address))
            conn.commit()
            flash("✅ Donor account created successfully!", "success")
        except sqlite3.IntegrityError:
            flash("⚠️ This email already exists.", "error")
        finally:
            conn.close()
        return redirect(url_for('login_page_donor'))
    return render_template('register_donor.html')

@app.route('/login_donor', methods=['POST'])
def login_donor():
    email = request.form['email']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM donors WHERE email=?", (email,))
    donor = c.fetchone()
    conn.close()
    if donor and verify_password(donor[3], password):
        session['user'] = donor[1]
        session['email'] = donor[2]
        session['user_type'] = 'donor'
        flash(f"Welcome back, {donor[4]}!", "success")
        return redirect(url_for('account_donor'))
    else:
        flash("❌ Invalid email or password.", "error")
        return redirect(url_for('login_page_donor'))

# ==============================================================
# 👤 ACCOUNT DASHBOARDS & LOGOUT
# ==============================================================
@app.route('/account')
def account():
    if 'user' in session and session.get('user_type') == 'user':
        dashboard_data = {
            "food_donations": 12, "money_donated": 247,
            "volunteer_hours": 28, "points": 1450,
            "activity": [("Donated 2kg vegetables", "2 days ago"), ("Volunteered 2 hours", "5 days ago")]
        }
        return render_template('account.html', name=session['user'], **dashboard_data)
    else:
        flash("Please log in first.", "error")
        return redirect(url_for('login_page'))

@app.route('/account_donor')
def account_donor():
    if 'user' in session and session.get('user_type') == 'donor':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM donors WHERE email=?", (session['email'],))
        donor_info = c.fetchone()
        conn.close()
        if not donor_info:
            flash("Could not find donor details.", "error")
            return redirect(url_for('home'))
        donor_dashboard_data = {
            "name": donor_info[1], "food_bank_name": donor_info[4], "address": donor_info[5],
            "food_received": "540 kg", "active_requests": 3, "donors_connected": 42, "volunteers_managed": 8,
            "donor_activity": [("Received Canned Goods from John D.", "1 hour ago"), ("Received 10kg Pasta from Jane S.", "5 hours ago")]
        }
        return render_template('account_donor.html', **donor_dashboard_data)
    else:
        flash("Please log in as a donor to access this page.", "error")
        return redirect(url_for('login_page_donor'))

# ✅ --- THIS IS THE MISSING FUNCTION --- ✅
@app.route('/logout')
def logout():
    session.clear()
    flash("You’ve been logged out successfully.", "info")
    return redirect(url_for('home'))

# ==============================================================
# 🗑️ DELETE ACCOUNT + FEEDBACK FLOW
# ==============================================================
@app.route('/delete_account_page')
def delete_account_page():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    user_type = session.get('user_type', 'user')
    cancel_url = url_for('account') if user_type == 'user' else url_for('account_donor')
    return render_template('delete_account.html', name=session['user'], cancel_url=cancel_url)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    email = session.get('email')
    user_type = session.get('user_type')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if email:
        if user_type == 'donor':
            c.execute("DELETE FROM donors WHERE email=?", (email,))
        else:
            c.execute("DELETE FROM users WHERE email=?", (email,))
    conn.commit()
    conn.close()
    session.clear()
    return redirect(url_for('feedback_page'))

@app.route('/feedback_page')
def feedback_page():
    return render_template('feedback.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    feedback_text = request.form['feedback']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO feedback (feedback) VALUES (?)", (feedback_text,))
    conn.commit()
    conn.close()
    flash("Thank you for your feedback 💚", "success")
    return redirect(url_for('home'))

# ==============================================================
# ❤️ DONATION WORKFLOW
# ==============================================================
@app.route('/contribution')
def contribution():
    return render_template('contribution.html')

@app.route('/donate/money', methods=['GET', 'POST'])
def donate_money():
    if request.method == 'POST':
        return redirect(url_for('thankyou'))
    return render_template('donate_money.html')

@app.route('/donate/food')
def donate_food():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT item_name, description, urgency FROM needed_items")
    items = c.fetchall()
    c.execute("SELECT location_name, address, hours FROM dropoff_locations")
    locations = c.fetchall()
    conn.close()
    return render_template('donate_food.html', items=items, locations=locations)

@app.route('/donate/time')
def donate_time():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, role_title, description FROM volunteer_roles")
    roles = c.fetchall()
    conn.close()
    return render_template('donate_time.html', roles=roles)

@app.route('/volunteer_signup', methods=['GET', 'POST'])
def volunteer_signup():
    if request.method == 'POST':
        flash("✅ Thank you for signing up to volunteer!", "success")
        return redirect(url_for('thankyou'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, role_title FROM volunteer_roles")
    roles = c.fetchall()
    conn.close()
    return render_template('volunteer_signup.html', roles=roles)

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

# ==============================================================
# 🔑 PASSWORD RESET FLOW
# ==============================================================
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        if user:
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['reset_email'] = email
            try:
                msg = Message("Password Reset Verification Code", recipients=[email])
                msg.body = f"Hello {user[1]},\n\nYour password reset verification code is: {otp}"
                mail.send(msg)
                flash("📩 A verification code has been sent to your email.", "info")
            except Exception as e:
                flash(f"⚠️ Failed to send email: {e}", "error")
            return redirect(url_for('verify_otp'))
        else:
            flash("⚠️ No account found with that email.", "error")
    return render_template('forgot.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'GET' and not session.get('otp'):
        flash("Please enter your email first.", "error")
        return redirect(url_for('forgot'))
    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == session.get('otp'):
            session['otp_ok'] = True
            session.pop('otp', None)
            flash("✅ Code verified. You can now change your password.", "success")
            return redirect(url_for('reset_password'))
        else:
            flash("❌ Invalid code. Try again.", "error")
    return render_template('verify.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('otp_ok') or not session.get('reset_email'):
        flash("Please verify your code first.", "error")
        return redirect(url_for('forgot'))
    if request.method == 'POST':
        new_password = hash_password(request.form['new_password'])
        email = session.get('reset_email')
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
        conn.commit()
        conn.close()
        session.pop('otp_ok', None)
        session.pop('reset_email', None)
        flash("🔐 Password updated successfully! Please log in again.", "success")
        return redirect(url_for('login_page'))
    return render_template('reset.html')

# ==============================================================
# 🚀 START APP
# ==============================================================
if __name__ == '__main__':
    init_db()
    app.run(debug=True)