from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3, random, hashlib

app = Flask(__name__)
app.secret_key = "super_secret_key_here"

# ==============================================================
# 📧 EMAIL CONFIGURATION (Gmail App Password Required)
# ==============================================================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '4elements.fontys@gmail.com'
app.config['MAIL_PASSWORD'] = 'fojk hqsu ocwj qyid'  # App Password from Google
app.config['MAIL_DEFAULT_SENDER'] = '4elements.fontys@gmail.com'

mail = Mail(app)

# ==============================================================
# 🗂️ DATABASE SETUP
# ==============================================================

def init_db():
    """Create database tables if they don’t exist."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        message TEXT NOT NULL
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        feedback TEXT NOT NULL
                    )''')

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
# 🏠 HOME PAGE
# ==============================================================

@app.route('/')
def home():
    user = session.get('user')
    return render_template('index.html', user=user)

# ==============================================================
# 👤 LOGIN & REGISTER
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
        c.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
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
        flash(f"Welcome back, {user[1]}!", "success")
        return redirect(url_for('account'))
    else:
        flash("❌ Invalid email or password.", "error")
        return redirect(url_for('login_page'))

# ==============================================================
# 👤 ACCOUNT + DASHBOARD
# ==============================================================

@app.route('/account')
def account():
    if 'user' in session:
        dashboard_data = {
            "food_donations": 12,
            "money_donated": 247,
            "volunteer_hours": 28,
            "points": 1450,
            "activity": [
                ("Donated 2kg vegetables", "2 days ago"),
                ("Volunteered 2 hours", "5 days ago"),
                ("Donated €25", "1 week ago"),
                ("Donated 5kg canned goods", "1 week ago"),
                ("Volunteered 4 hours", "2 weeks ago"),
            ]
        }
        return render_template(
            'account.html',
            name=session['user'],
            **dashboard_data
        )
    else:
        flash("Please log in first.", "error")
        return redirect(url_for('login_page'))

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
        flash("Please log in first.", "error")
        return redirect(url_for('login_page'))
    return render_template('delete_account.html', name=session['user'])

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user' not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('login_page'))

    email = session.get('email')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if email:
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
# 💌 CONTACT PAGE
# ==============================================================

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )
        conn.commit()
        conn.close()

        try:
            msg_admin = Message(
                "New Contact Form Submission",
                recipients=['4elements.fontys@gmail.com']
            )
            msg_admin.body = f"New message from {name} ({email}):\n\n{message}"
            mail.send(msg_admin)

            msg_user = Message(
                "Thanks for contacting 4 Elements 💚",
                recipients=[email]
            )
            msg_user.body = f"Hello {name},\n\nWe received your message:\n{message}"
            mail.send(msg_user)

            flash("💚 Your message has been sent successfully!", "success")

        except Exception as e:
            flash(f"⚠️ Failed to send email: {e}", "error")

        return redirect(url_for('home'))

    return render_template('contact.html', user=session.get('user'))

# ==============================================================
# 🌱 ABOUT PAGE
# ==============================================================

@app.route('/about')
def about():
    user = session.get('user')
    return render_template('about.html', user=user)

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
                msg = Message(
                    "Password Reset Verification Code",
                    recipients=[email]
                )
                msg.body = f"""
                Hello {user[1]},
                Your password reset verification code is: {otp}
                """
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
        new_password = request.form['new_password']
        hashed_password = hash_password(new_password)
        email = session.get('reset_email')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hashed_password, email)
        )
        conn.commit()
        conn.close()

        session.pop('otp_ok', None)
        session.pop('reset_email', None)

        flash("🔐 Password updated successfully!", "success")
        return redirect(url_for('login_page'))

    return render_template('reset.html')

# ==============================================================
# ⭐⭐⭐ PROJECTS ROUTE (ONLY ADDITION REQUESTED) ⭐⭐⭐
# ==============================================================

@app.route('/projects')
def projects():
    return render_template('projects.html')

# ==============================================================
# 🚀 START APP
# ==============================================================

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

# ==============================================================