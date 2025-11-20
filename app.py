from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
import sqlite3, random, hashlib, requests

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
# 🗂️ DATABASE SETUP (FINAL + ALL FIXES)
# ==============================================================
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # ----------------------------------------------------------
    # USERS TABLE
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            level_progress INTEGER DEFAULT 0,
            next_level_target INTEGER DEFAULT 100,
            badge TEXT DEFAULT 'bronze'
        )
    ''')

    cursor.execute("PRAGMA table_info(users)")
    user_cols = [row[1] for row in cursor.fetchall()]

    if "points" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    if "level" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1")
    if "level_progress" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN level_progress INTEGER DEFAULT 0")
    if "next_level_target" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN next_level_target INTEGER DEFAULT 100")
    if "badge" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN badge TEXT DEFAULT 'bronze'")

    # ----------------------------------------------------------
    # CONTACT MESSAGES
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')

    # ----------------------------------------------------------
    # FEEDBACK
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback TEXT NOT NULL
        )
    ''')

    # ----------------------------------------------------------
    # FOOD BANK ACCOUNTS
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            food_bank_name TEXT NOT NULL,
            address TEXT NOT NULL,
            latitude REAL,
            longitude REAL
        )
    ''')

    cursor.execute("PRAGMA table_info(donors)")
    donor_cols = [row[1] for row in cursor.fetchall()]

    if "latitude" not in donor_cols:
        cursor.execute("ALTER TABLE donors ADD COLUMN latitude REAL")
    if "longitude" not in donor_cols:
        cursor.execute("ALTER TABLE donors ADD COLUMN longitude REAL")

    # ⭐ أهم شي: إضافة أعمدة التبرعات الغذائية
    if "food_received" not in donor_cols:
        cursor.execute("ALTER TABLE donors ADD COLUMN food_received INTEGER DEFAULT 0")

    if "food_donations" not in donor_cols:
        cursor.execute("ALTER TABLE donors ADD COLUMN food_donations INTEGER DEFAULT 0")

    # ----------------------------------------------------------
    # DONOR SETTINGS
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donor_settings (
            donor_id INTEGER PRIMARY KEY,
            auto_accept INTEGER DEFAULT 0,
            open_status INTEGER DEFAULT 1,
            phone TEXT,
            website TEXT,
            opening_hours TEXT,
            FOREIGN KEY (donor_id) REFERENCES donors(id)
        )
    ''')

    # ----------------------------------------------------------
    # NEEDED ITEMS
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS needed_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            description TEXT,
            urgency TEXT DEFAULT 'Medium'
        )
    ''')

    # ----------------------------------------------------------
    # INVENTORY
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            current_quantity INTEGER DEFAULT 0,
            minimum_required INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES donors(id)
        )
    ''')

    # ----------------------------------------------------------
    # DROP-OFF LOCATIONS
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dropoff_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            address TEXT NOT NULL,
            hours TEXT NOT NULL
        )
    ''')

    # ----------------------------------------------------------
    # VOLUNTEER ROLES
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volunteer_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_title TEXT NOT NULL,
            description TEXT NOT NULL
        )
    ''')

    # ----------------------------------------------------------
    # VOLUNTEERS
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            role_id INTEGER,
            FOREIGN KEY (role_id) REFERENCES volunteer_roles(id)
        )
    ''')

    # ----------------------------------------------------------
    # DONATIONS
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            donation_type TEXT NOT NULL,
            amount REAL,
            quantity INTEGER,
            hours INTEGER,
            donor_id INTEGER,
            status TEXT DEFAULT 'completed',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute("PRAGMA table_info(donations)")
    donation_cols = [row[1] for row in cursor.fetchall()]

    if "donor_id" not in donation_cols:
        cursor.execute("ALTER TABLE donations ADD COLUMN donor_id INTEGER")
    if "status" not in donation_cols:
        cursor.execute("ALTER TABLE donations ADD COLUMN status TEXT DEFAULT 'completed'")

    # ----------------------------------------------------------
    # DONATION PROMISES
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donation_promises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            donor_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            urgency TEXT NOT NULL,
            remaining_need INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            earned_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (donor_id) REFERENCES donors(id)
        )
    ''')

    # ----------------------------------------------------------
    # NOTIFICATIONS
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            donor_id INTEGER,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (donor_id) REFERENCES donors(id)
        )
    ''')

    # ----------------------------------------------------------
    # VOLUNTEER REQUESTS
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volunteer_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER NOT NULL,
            task_title TEXT NOT NULL,
            needed_people INTEGER NOT NULL,
            task_date TEXT NOT NULL,
            duration TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES donors(id)
        )
    ''')

    # ----------------------------------------------------------
    # REQUESTED ITEMS
    # ----------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requested_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            description TEXT,
            quantity INTEGER,
            urgency TEXT,
            status TEXT DEFAULT 'pending',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES donors(id)
        )
    ''')

    conn.commit()
    conn.close()


def update_user_level(c, user_id):
    # Fetch user level data
    c.execute("""
        SELECT level, level_progress, next_level_target
        FROM users
        WHERE id=?
    """, (user_id,))
    level, progress, target = c.fetchone()

    # Fetch earned points ONLY from confirmed donation_promises
    c.execute("""
        SELECT COALESCE(SUM(earned_points), 0)
        FROM donation_promises
        WHERE user_id=? AND status='confirmed'
    """, (user_id,))
    earned_total = c.fetchone()[0]

    # Progress within current level
    progress = earned_total

    leveled_up = False

    # Level-up loop
    while progress >= target:
        progress -= target
        level += 1
        target = int(target * 1.6)
        leveled_up = True

    # Badge rules
    if level >= 10:
        badge = "gold"
    elif level >= 5:
        badge = "silver"
    else:
        badge = "bronze"

    # Update DB
    c.execute("""
        UPDATE users
        SET level=?, level_progress=?, next_level_target=?, badge=?
        WHERE id=?
    """, (level, progress, target, badge, user_id))

    progress_percent = int((progress / target) * 100) if target > 0 else 0

    return progress_percent, badge, level


# ==============================================================
# ⚙️ USER SETTINGS PAGE
# ==============================================================
@app.route("/settings")
def settings_page():
    if "user" not in session or session.get("user_type") != "user":
        return redirect(url_for("login_page"))

    return render_template("settings.html", name=session["user"])

# ============================================================
# 🧮 POINTS, LEVEL & BADGE SYSTEM (FINAL VERSION)
# ============================================================
def get_badge_for_level(level):
    if level >= 20:
        return "elite"
    elif level >= 15:
        return "platinum"
    elif level >= 10:
        return "gold"
    elif level >= 5:
        return "silver"
    return "bronze"


def calculate_points(item_quantity, urgency, remaining_need):
    urgency = urgency.lower().strip()

    base = 3
    urgency_mult = {
        "low": 1,
        "medium": 1.5,
        "high": 2.5,
        "critical": 4
    }.get(urgency, 1)

    # shortage bonus
    if remaining_need <= 5:
        shortage_bonus = 1
    elif remaining_need <= 15:
        shortage_bonus = 3
    else:
        shortage_bonus = 5

    points_per_item = (base * urgency_mult) + shortage_bonus
    total_points = points_per_item * item_quantity

    return int(total_points)


def update_user_points(user_id, earned):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Get current user data
    c.execute("""
        SELECT points, level, level_progress, next_level_target
        FROM users WHERE id=?
    """, (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False

    current_points, level, progress, target = row

    # Step 1: Add points
    new_points = current_points + earned
    new_progress = progress + earned

    leveled_up = False

    # Step 2: Level-up loop
    while new_progress >= target:
        new_progress -= target
        level += 1
        target = int(target * 1.6)
        leveled_up = True

    # Step 3: Update badge
    badge = get_badge_for_level(level)

    # Step 4: Save
    c.execute("""
        UPDATE users
        SET points=?, level=?, level_progress=?, next_level_target=?, badge=?
        WHERE id=?
    """, (new_points, level, new_progress, target, badge, user_id))

    conn.commit()
    conn.close()

    return leveled_up

# ==============================================================
# 🔐 PASSWORD SECURITY
# ==============================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(stored_password: str, given_password: str) -> bool:
    return stored_password == hashlib.sha256(given_password.encode()).hexdigest()

# ==============================================================
# ⭐ DONATION HELPER FUNCTIONS
# ==============================================================
def add_donation(user_email, donation_type, amount=None, quantity=None, hours=None, donor_id=None):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO donations (user_email, donation_type, amount, quantity, hours, donor_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_email, donation_type, amount, quantity, hours, donor_id))

    conn.commit()
    conn.close()


def get_user_stats(email):
    """Return totals + recent activity for a given user email."""
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Total money
    c.execute(
        "SELECT SUM(amount) FROM donations WHERE user_email=? AND donation_type='money'",
        (email,),
    )
    row = c.fetchone()
    money = row[0] if row and row[0] is not None else 0

    # Total food quantity
    c.execute(
        "SELECT SUM(quantity) FROM donations WHERE user_email=? AND donation_type='food'",
        (email,),
    )
    row = c.fetchone()
    food = row[0] if row and row[0] is not None else 0

    # Total volunteer hours
    c.execute(
        "SELECT SUM(hours) FROM donations WHERE user_email=? AND donation_type='time'",
        (email,),
    )
    row = c.fetchone()
    hours = row[0] if row and row[0] is not None else 0

    # Simple points system
    points = int(money * 1 + food * 2 + hours * 5)

    # Recent activity
    c.execute(
        """
        SELECT donation_type, amount, quantity, hours, timestamp
        FROM donations
        WHERE user_email=?
        ORDER BY timestamp DESC
        LIMIT 5
        """,
        (email,),
    )
    rows = c.fetchall()
    conn.close()

    activity = []
    for donation_type, amount, quantity, d_hours, ts in rows:
        if donation_type == "money" and amount is not None:
            desc = f"Donated €{amount:.2f}"
        elif donation_type == "food" and quantity is not None:
            desc = f"Donated {int(quantity)} food items"
        elif donation_type == "time" and d_hours is not None:
            desc = f"Volunteered {int(d_hours)} hours"
        else:
            desc = "Donation activity"
        activity.append((desc, ts))

    return money, food, hours, points, activity


def get_donor_stats(donor_id):
    """Stats for a specific donor (food bank / organisation)."""
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Total money received
    c.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM donations
        WHERE donor_id=? AND donation_type='money' AND status='completed'
        """,
        (donor_id,),
    )
    total_money = c.fetchone()[0] or 0

    # Total food items received
    c.execute(
        """
        SELECT COALESCE(SUM(quantity), 0)
        FROM donations
        WHERE donor_id=? AND donation_type='food' AND status='completed'
        """,
        (donor_id,),
    )
    total_food = c.fetchone()[0] or 0

    # Total volunteer hours received
    c.execute(
        """
        SELECT COALESCE(SUM(hours), 0)
        FROM donations
        WHERE donor_id=? AND donation_type='time' AND status='completed'
        """,
        (donor_id,),
    )
    total_hours = c.fetchone()[0] or 0

    # Total donations count
    c.execute(
        """
        SELECT COUNT(*)
        FROM donations
        WHERE donor_id=? AND status='completed'
        """,
        (donor_id,),
    )
    total_donations = c.fetchone()[0] or 0

    # Last 5 donations
    c.execute(
        """
        SELECT user_email, donation_type, amount, quantity, hours, timestamp
        FROM donations
        WHERE donor_id=?
        ORDER BY timestamp DESC
        LIMIT 5
        """,
        (donor_id,),
    )
    rows = c.fetchall()
    conn.close()

    activity = []
    for email, typ, amount, quantity, h, ts in rows:
        if typ == "money" and amount is not None:
            desc = f"Received €{amount:.2f} from {email}"
        elif typ == "food" and quantity is not None:
            desc = f"Received {int(quantity)} food items from {email}"
        elif typ == "time" and h is not None:
            desc = f"{email} volunteered {int(h)} hours"
        else:
            desc = f"New contribution from {email}"
        activity.append((desc, ts))

    return {
        "total_money": total_money,
        "total_food": total_food,
        "total_hours": total_hours,
        "total_donations": total_donations,
        "activity": activity,
    }

# ==============================================================
# 📌 Geocoding Function (Nominatim API)
# ==============================================================
def geocode(address: str):
    """
    Converts an address into latitude and longitude using Nominatim.
    Returns (lat, lng) or (None, None) if fail.
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }

        headers = {
            "User-Agent": "4ElementsDonationApp/1.0 (contact: 4elements.fontys@gmail.com)"
        }

        resp = requests.get(url, params=params, headers=headers, timeout=10)

        if resp.status_code != 200:
            return None, None

        data = resp.json()
        if not data:
            return None, None

        lat = float(data[0]["lat"])
        lng = float(data[0]["lon"])
        return lat, lng

    except Exception as e:
        print("Geocoding error:", e)
        return None, None

# ==============================================================
# 🏠 CORE & STATIC PAGES
# ==============================================================
@app.route("/")
def home():
    user = session.get("user")
    user_type = session.get("user_type")
    return render_template("index.html", user=user, user_type=user_type)


@app.route("/about")
def about():
    user = session.get("user")
    user_type = session.get("user_type")
    return render_template("about.html", user=user, user_type=user_type)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("💚 Your message has been sent successfully!", "success")
        return redirect(url_for("home"))
    user = session.get("user")
    user_type = session.get("user_type")
    return render_template("contact.html", user=user, user_type=user_type)


# real contact form (DB + email)
@app.route("/contact_form", methods=["POST"])
def contact_form():
    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
        (name, email, message),
    )
    conn.commit()
    conn.close()

    try:
        msg_admin = Message(
            "New Contact Form Submission",
            recipients=["4elements.fontys@gmail.com"],
        )
        msg_admin.body = f"New message from {name} ({email}):\n\n{message}"
        mail.send(msg_admin)

        msg_user = Message(
            "Thanks for contacting 4 Elements 💚",
            recipients=[email],
        )
        msg_user.body = f"Hello {name},\n\nWe received your message:\n{message}"
        mail.send(msg_user)

        flash("💚 Your message has been sent successfully!", "success")
    except Exception as e:
        flash(f"⚠️ Failed to send email: {e}", "error")

    return redirect(url_for("home"))

# ==============================================================
# 👤 USER LOGIN & REGISTER
# ==============================================================
@app.route("/login_page")
def login_page():
    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    password = hash_password(request.form["password"])

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password),
        )
        conn.commit()
        flash("✅ Account created successfully! You can now log in.", "success")
    except sqlite3.IntegrityError:
        flash("⚠️ This email already exists.", "error")
    finally:
        conn.close()

    return redirect(url_for("login_page"))


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Check normal user
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()

    # Check donor
    c.execute("SELECT * FROM donors WHERE email=?", (email,))
    donor = c.fetchone()

    conn.close()

    # Normal user login
    if user and verify_password(user[3], password):
        session["user"] = user[1]
        session["email"] = user[2]
        session["user_type"] = "user"
        session["user_id"] = user[0]
        return redirect(url_for("account"))

    # Donor login
    if donor and verify_password(donor[3], password):
        session["user"] = donor[1]
        session["email"] = donor[2]
        session["user_type"] = "donor"
        session["donor_id"] = donor[0]
        return redirect(url_for("account_donor"))

    flash("Invalid email or password.", "error")
    return redirect(url_for("login_page"))

# ==============================================================
# 🏦 DONOR (FOOD BANK) LOGIN & REGISTER
# ==============================================================
@app.route("/login_page_donor")
def login_page_donor():
    return render_template("login_donor.html")


@app.route("/register_donor", methods=["GET", "POST"])
def register_donor():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = hash_password(request.form["password"])
        food_bank_name = request.form["food_bank_name"]
        address = request.form["address"]

        # ✨ GET LAT + LNG
        lat, lng = geocode(address)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO donors (name, email, password, food_bank_name, address, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, email, password, food_bank_name, address, lat, lng))
            conn.commit()
            flash("✅ Donor account created successfully!", "success")
        except sqlite3.IntegrityError:
            flash("⚠️ This email already exists.", "error")
        finally:
            conn.close()

        return redirect(url_for("login_page_donor"))

    return render_template("register_donor.html")


@app.route("/login_donor", methods=["POST"])
def login_donor():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM donors WHERE email=?", (email,))
    donor = c.fetchone()
    conn.close()

    if donor and verify_password(donor[3], password):
        session["user"] = donor[1]
        session["email"] = donor[2]
        session["user_type"] = "donor"
        session["donor_id"] = donor[0]

        flash(f"Welcome back, {donor[4]}!", "success")
        return redirect(url_for("account_donor"))

    flash("❌ Invalid email or password.", "error")
    return redirect(url_for("login_page_donor"))


@app.route("/account_donor")
def account_donor():
    if "user" in session and session.get("user_type") == "donor":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM donors WHERE email=?", (session["email"],))
        donor_info = c.fetchone()

        if not donor_info:
            conn.close()
            flash("Donor account not found.", "error")
            return redirect(url_for("home"))

        donor_id = donor_info[0]

        # Fetch stats
        c.execute("""
            SELECT food_received, food_donations
            FROM donors
            WHERE id = ?
        """, (donor_id,))
        stats = c.fetchone()

        food_received = stats[0] if stats else 0
        food_donations = stats[1] if stats else 0

        # Count pending promises
        c.execute("""
            SELECT COUNT(*)
            FROM donation_promises
            WHERE donor_id=? AND status='pending'
        """, (donor_id,))
        pending_count = c.fetchone()[0]

        conn.close()

        return render_template(
            "account_donor.html",
            name=donor_info[1],
            food_bank_name=donor_info[4],
            address=donor_info[5],
            food_donations=food_received,
            food_received=food_received,
            volunteer_hours=0,
            money_donated=0,
            points=food_received * 2,
            pending_count=pending_count,
            activity=[]
        )

    flash("Please log in as a donor to continue.", "error")
    return redirect(url_for("login_page_donor"))
# ==============================================================
# 👤 USER ACCOUNT (WITH LEVEL + FOOD FIX)
# ==============================================================
@app.route("/account")
def account():
    if "user" not in session or session.get("user_type") != "user":
        return redirect(url_for("login_page"))

    user_id = session["user_id"]
    email = session["email"]

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ----------------------------------------------------------
    # 🍏 1) Count confirmed food donations (NEW FIX)
    # ----------------------------------------------------------
    c.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM donation_promises
        WHERE user_id=? AND status='confirmed'
    """, (user_id,))
    food = c.fetchone()[0] or 0

    # ----------------------------------------------------------
    # 💰 2) Money + Hours from donations table
    # ----------------------------------------------------------
    money, _, hours, _, activity = get_user_stats(email)

    # ----------------------------------------------------------
    # ⭐ 3) Total Points = money + food*2 + hours*5
    # ----------------------------------------------------------
    total_points = money + (food * 2) + (hours * 5)

    # ----------------------------------------------------------
    # 🏅 4) Level Information
    # ----------------------------------------------------------
    c.execute("""
        SELECT level, level_progress, next_level_target, badge
        FROM users WHERE id=?
    """, (user_id,))
    level, progress, target, badge = c.fetchone()

    progress_percent = int((progress / target) * 100) if target > 0 else 0

    # ----------------------------------------------------------
    # 📜 5) Donation History (only confirmed)
    # ----------------------------------------------------------
    c.execute("""
        SELECT item_name, quantity, urgency, earned_points, created_at
        FROM donation_promises
        WHERE user_id=? AND status='confirmed'
        ORDER BY created_at DESC
    """, (user_id,))
    history = c.fetchall()

    conn.close()

    # ----------------------------------------------------------
    # 🎨 6) Render Page
    # ----------------------------------------------------------
    return render_template(
        "account.html",
        name=session["user"],
        food_donations=food,
        money_donated=money,
        volunteer_hours=hours,
        points=total_points,
        level=level,
        badge=badge,
        progress_percent=progress_percent,
        activity=activity,
        history=history
    )


# ----------------------------------------------------------
# PENDING DONATIONS PAGE
# ----------------------------------------------------------
@app.route("/pending_promises")
def pending_promises():
    donor_id = session.get("donor_id")
    if not donor_id:
        flash("Please login as a food bank.", "danger")
        return redirect(url_for("login_donor"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT 
            dp.id,
            u.name,
            dp.item_name,
            dp.quantity,
            dp.urgency,
            dp.remaining_need,
            dp.created_at
        FROM donation_promises dp
        JOIN users u ON dp.user_id = u.id
        WHERE dp.donor_id = ? AND dp.status = 'pending'
        ORDER BY dp.created_at DESC
    """, (donor_id,))

    promises = c.fetchall()
    conn.close()

    return render_template("pending_promises.html", promises=promises)


# 🔁 Alias route used في accept/decline
@app.route("/donor/pending_promises")
def donor_pending_promises():
    return pending_promises()

# ----------------------------------------------------------
# CONFIRMED DONATIONS HISTORY
# ----------------------------------------------------------
@app.route("/confirmed_donations")
def confirmed_donations():
    if session.get("user_type") != "donor":
        return redirect(url_for("home"))

    donor_email = session.get("email")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Get donor_id
    c.execute("SELECT id FROM donors WHERE email=?", (donor_email,))
    donor = c.fetchone()

    if not donor:
        conn.close()
        return "Donor not found"

    donor_id = donor[0]

    # Fetch confirmed + completed donations
    c.execute("""
        SELECT id, user_id, item_name, quantity, urgency, earned_points, created_at
        FROM donation_promises
        WHERE donor_id=? AND (status='confirmed' OR status='completed')
        ORDER BY created_at DESC
    """, (donor_id,))
    
    donations = c.fetchall()
    conn.close()

    return render_template("confirmed_donations.html", donations=donations)

# ----------------------------------------------------------
# CONFIRM DONATION (Award Points + Reduce Remaining Need)
# ----------------------------------------------------------
@app.route('/confirm_donation/<int:donation_id>', methods=['POST'])
def confirm_donation(donation_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Fetch donation info
    c.execute("""
        SELECT user_id, item_name, quantity, urgency, remaining_need, donor_id
        FROM donation_promises
        WHERE id=?
    """, (donation_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return "Donation not found", 404

    user_id, item_name, quantity, urgency, remaining_need, donor_id = row

    # Calculate points
    points = calculate_points(quantity, urgency, remaining_need)

    # Update user points
    update_user_points(user_id, points)

    # NEW remaining need
    new_remaining = max(remaining_need - quantity, 0)

    # Update donation
    c.execute("""
        UPDATE donation_promises
        SET earned_points=?, status='confirmed', remaining_need=?
        WHERE id=?
    """, (points, new_remaining, donation_id))

    conn.commit()
    conn.close()

    flash("Donation confirmed. Points added & inventory updated.", "success")
    return redirect(url_for("pending_promises"))


@app.route("/request-items")
def request_items_page():
    if session.get("user_type") != "donor":
        return redirect(url_for("home"))
    return render_template("request_items.html")

# ----------------------------------------------------------
# LOGOUT
# ----------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You’ve been logged out successfully.", "info")
    return redirect(url_for("home"))

# ==============================================================
# 🗑️ DELETE ACCOUNT + FEEDBACK FLOW
# ==============================================================
@app.route("/delete_account_page")
def delete_account_page():
    if "user" not in session:
        return redirect(url_for("login_page"))
    user_type = session.get("user_type", "user")
    cancel_url = url_for("account") if user_type == "user" else url_for("account_donor")
    return render_template("delete_account.html", name=session["user"], cancel_url=cancel_url)


@app.route("/delete_account", methods=["POST"])
def delete_account():
    if "user" not in session:
        return redirect(url_for("login_page"))

    email = session.get("email")
    user_type = session.get("user_type")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if email:
        if user_type == "donor":
            c.execute("DELETE FROM donors WHERE email=?", (email,))
        else:
            c.execute("DELETE FROM users WHERE email=?", (email,))

    conn.commit()
    conn.close()
    session.clear()
    return redirect(url_for("feedback_page"))


@app.route("/feedback_page")
def feedback_page():
    return render_template("feedback.html")


@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    feedback_text = request.form["feedback"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO feedback (feedback) VALUES (?)", (feedback_text,))
    conn.commit()
    conn.close()
    flash("Thank you for your feedback 💚", "success")
    return redirect(url_for("home"))

# ==============================================================
# ❤️ DONATION WORKFLOW (SELECT TYPE + MONEY → SELECT BANK)
# ==============================================================
@app.route("/contribution")
def contribution():
    user_type = session.get("user_type")

    if user_type == "user":
        return render_template("contribution.html")

    if user_type == "donor":
        return redirect(url_for("account_donor"))

    flash("Please log in to continue.", "error")
    return redirect(url_for("login_page"))


@app.route("/donate/select-bank")
def select_bank_money():
    """Show list of food banks for money donations."""
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, food_bank_name, address FROM donors")
    rows = c.fetchall()
    conn.close()

    banks = []
    for row in rows:
        distance = round(random.uniform(0.5, 12.0), 1)
        banks.append((row[0], row[1], row[2], distance))

    return render_template("money_select_bank.html", banks=banks)


@app.route('/donate/money/bank/<int:donor_id>', methods=['GET', 'POST'])
def donate_money_bank(donor_id):
    if 'email' not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for('login_page'))

    if request.method == "POST":
        try:
            amount = float(request.form.get('amount', 0))
        except:
            amount = 0

        if amount <= 0:
            flash("Please enter a valid amount.", "error")
            return redirect(url_for('donate_money_bank', donor_id=donor_id))

        user_email = session['email']
        user_id = session['user_id']

        # 1) Save donation
        add_donation(
            user_email=user_email,
            donation_type="money",
            amount=amount,
            donor_id=donor_id
        )

        # 2) Calculate money points
        earned_points = int(amount)

        # 3) Update user points + level + badge
        update_user_points(user_id, earned_points)

        flash("💚 Thank you for your donation!", "success")
        return redirect(url_for("account"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT food_bank_name, address FROM donors WHERE id=?", (donor_id,))
    donor = c.fetchone()
    conn.close()

    if not donor:
        flash("Food bank not found.", "error")
        return redirect(url_for('select_bank_money'))

    return render_template(
        "donate_money.html",
        donor_id=donor_id,
        donor_name=donor[0],
        donor_address=donor[1]
    )

# ==============================================================
# VOLUNTEER REQUEST PAGES (ORGANIZATION)
# ==============================================================
@app.route('/request-volunteers')
def request_volunteers_page():
    if session.get("user_type") != "donor":
        return redirect(url_for("home"))
    return render_template('request_volunteers.html')


@app.route('/submit_request_volunteers', methods=['POST'])
def submit_request_volunteers():
    if session.get("user_type") != "donor":
        return redirect(url_for("home"))

    donor_id = session.get("donor_id")
    task_title = request.form["task_title"]
    needed_people = request.form["needed_people"]
    task_date = request.form["task_date"]
    duration = request.form["duration"]
    description = request.form["description"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO volunteer_requests 
        (donor_id, task_title, needed_people, task_date, duration, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (donor_id, task_title, needed_people, task_date, duration, description))

    conn.commit()
    conn.close()

    flash("Volunteer request submitted successfully!", "success")
    return redirect(url_for('account_donor'))


@app.route('/organization/requests')
def organization_requests():
    if session.get("user_type") != "donor":
        return redirect(url_for("home"))

    donor_id = session.get("donor_id")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, task_title, needed_people, task_date, duration, status, created_at
        FROM volunteer_requests
        WHERE donor_id=?
        ORDER BY created_at DESC
    """, (donor_id,))
    
    requests_list = c.fetchall()
    conn.close()

    return render_template("organization_requests.html", requests=requests_list)


@app.route('/request/approve/<int:req_id>')
def approve_request(req_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE volunteer_requests SET status='approved' WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    flash("Request approved!", "success")
    return redirect(url_for('organization_requests'))


@app.route('/request/reject/<int:req_id>')
def reject_request(req_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE volunteer_requests SET status='rejected' WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    flash("Request rejected!", "error")
    return redirect(url_for('organization_requests'))


@app.route("/submit_request_item", methods=["POST"])
def submit_request_item():
    if session.get("user_type") != "donor":
        return redirect(url_for("home"))

    donor_id = session.get("donor_id")
    item_name = request.form["item_name"]
    description = request.form["description"]
    quantity = request.form["quantity"]
    urgency = request.form["urgency"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO requested_items (donor_id, item_name, description, quantity, urgency)
        VALUES (?, ?, ?, ?, ?)
    """, (donor_id, item_name, description, quantity, urgency))

    conn.commit()
    conn.close()

    flash("Request submitted successfully!", "success")
    return redirect(url_for("account_donor"))

# ==============================================================
# DONATION SUB-PAGES (FOOD, TIME)
# ==============================================================
@app.route("/donate/food")
def donate_food():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT id, donor_id, item_name, description, quantity, urgency 
        FROM requested_items
        WHERE status='pending'
    """)
    items = c.fetchall()

    conn.close()
    return render_template("donate_food.html", items=items)

# ==============================================================  
# DONATION SUB-PAGES (FOOD, TIME)  
# ==============================================================
@app.route('/donate/time')
def donate_time():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        SELECT id, task_title, description, needed_people, task_date, duration
        FROM volunteer_requests
        WHERE status='approved'
    """)

    roles = c.fetchall()
    conn.close()

    return render_template('donate_time.html', roles=roles)


# ==============================================================
# 🌿 FOOD DONATION - PROMISE PAGE
# ==============================================================
@app.route("/donate/food/promise")
def promise_food():
    item_id = request.args.get("item_id")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT donor_id, item_name, description, quantity, urgency
        FROM requested_items
        WHERE id=?
    """, (item_id,))
    
    row = c.fetchone()
    conn.close()

    if not row:
        flash("Item not found.", "danger")
        return redirect(url_for("donate_food"))

    donor_id, item_name, description, quantity, urgency = row

    return render_template(
        "promise_food.html",
        donor_id=donor_id,
        item_name=item_name,
        description=description,
        quantity=quantity,
        urgency=urgency
    )

# ==============================================================
# 🍏 ACCEPT / COMPLETE PROMISE
# ==============================================================
@app.route("/accept_promise/<int:promise_id>", methods=["POST"])
def accept_promise(promise_id):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1) Read promise
    c.execute("""
        SELECT user_id, donor_id, quantity, urgency, remaining_need, item_name
        FROM donation_promises
        WHERE id = ?
    """, (promise_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        flash("Promise not found.", "error")
        return redirect(url_for("donor_pending_promises"))

    user_id       = row["user_id"]
    donor_id      = row["donor_id"]
    qty           = row["quantity"]
    urgency       = row["urgency"].lower()
    remaining     = row["remaining_need"]
    item_name     = row["item_name"]

    # Get user email
    c2 = conn.cursor()
    c2.execute("SELECT email FROM users WHERE id=?", (user_id,))
    user_email = c2.fetchone()[0]

    # 2) Calculate points
    earned = calculate_points(
        item_quantity=qty,
        urgency=urgency,
        remaining_need=remaining
    )

    # 3) Update user points + level
    update_user_points(user_id, earned)

    # 4) Mark promise as completed
    new_remaining = max(remaining - qty, 0)

    c.execute("""
        UPDATE donation_promises
        SET status='completed', earned_points=?, remaining_need=?
        WHERE id=?
    """, (earned, new_remaining, promise_id))

    # 5) Update requested_items
    c.execute("""
        UPDATE requested_items
        SET quantity = quantity - ?
        WHERE donor_id=? AND item_name=?
    """, (qty, donor_id, item_name))

    # Remove item when fully satisfied
    c.execute("""
        DELETE FROM requested_items
        WHERE donor_id=? AND item_name=? AND quantity <= 0
    """, (donor_id, item_name))

    # 6) Update donor food received
    c.execute("""
        UPDATE donors
        SET food_received = COALESCE(food_received, 0) + ?
        WHERE id=?
    """, (qty, donor_id))

    # 7) Add REAL FOOD DONATION in "donations" table
    c.execute("""
        INSERT INTO donations (user_email, donation_type, quantity, donor_id, status)
        VALUES (?, 'food', ?, ?, 'completed')
    """, (user_email, qty, donor_id))

    # 8) Ensure Dashboard updates user stats properly
    c.execute("""
        UPDATE users
        SET points = points + ?, level_progress = level_progress + ?
        WHERE id=?
    """, (earned, earned, user_id))

    conn.commit()
    conn.close()

    flash(f"Promise accepted successfully (+{earned} points) 💚", "success")
    return redirect(url_for("donor_pending_promises"))

# ==============================================================
# ❌ DECLINE PROMISE
# ==============================================================
@app.route("/decline_promise/<int:promise_id>", methods=["POST"])
def decline_promise(promise_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id FROM donation_promises WHERE id=?", (promise_id,))
    if not c.fetchone():
        conn.close()
        flash("Promise not found.", "error")
        return redirect(url_for("donor_pending_promises"))

    c.execute("""
        UPDATE donation_promises
        SET status='declined'
        WHERE id=?
    """, (promise_id,))

    conn.commit()
    conn.close()

    flash("Promise declined ❌", "info")
    return redirect(url_for("donor_pending_promises"))

# ==============================================================
# 🌟 CONFIRM DONATION PROMISE (FOOD BANK ACTION)
# ==============================================================
@app.route("/donor/confirm_promise/<int:promise_id>")
def confirm_promise(promise_id):
    donor_id = session.get("donor_id")
    if not donor_id:
        flash("Please login as a food bank.", "danger")
        return redirect(url_for("login_donor"))

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1) Fetch promise details
    c.execute("""
        SELECT user_id, donor_id, item_name, quantity, urgency, remaining_need
        FROM donation_promises
        WHERE id = ?
    """, (promise_id,))
    
    promise = c.fetchone()

    if not promise:
        flash("Promise not found.", "danger")
        conn.close()
        return redirect(url_for("pending_promises"))

    user_id         = promise["user_id"]
    donor_id        = promise["donor_id"]
    item_name       = promise["item_name"]
    user_quantity   = promise["quantity"]
    urgency         = promise["urgency"]
    remaining_need  = promise["remaining_need"]

    # Get user email
    c2 = conn.cursor()
    c2.execute("SELECT email FROM users WHERE id=?", (user_id,))
    user_email = c2.fetchone()[0]

    # 2) Calculate points
    points = calculate_points(
        item_quantity=user_quantity,
        urgency=urgency,
        remaining_need=remaining_need
    )

    # 3) Update user points
    update_user_points(user_id, points)

    # 4) Mark promise as confirmed
    new_remaining = max(remaining_need - user_quantity, 0)

    c.execute("""
        UPDATE donation_promises
        SET status = 'confirmed',
            earned_points = ?,
            remaining_need = ?
        WHERE id = ?
    """, (points, new_remaining, promise_id))

    # 5) Update donor food stats
    c.execute("""
        UPDATE donors
        SET food_received = COALESCE(food_received, 0) + ?,
            food_donations = COALESCE(food_donations, 0) + ?
        WHERE id=?
    """, (user_quantity, user_quantity, donor_id))

    # 6) Insert into donations table
    c.execute("""
        INSERT INTO donations (user_email, donation_type, quantity, donor_id, status)
        VALUES (?, 'food', ?, ?, 'completed')
    """, (user_email, user_quantity, donor_id))

    # 7) Log notification
    c.execute("""
        INSERT INTO notifications (user_id, donor_id, message)
        VALUES (?, ?, ?)
    """, (
        user_id,
        donor_id,
        f"Your donation of {user_quantity} × {item_name} has been confirmed! (+{points} points)"
    ))

    conn.commit()
    conn.close()

    flash("Promise confirmed successfully 💛", "success")
    return redirect(url_for("pending_promises"))

# ==============================================================
# 🌿 SUBMIT FOOD DONATION PROMISE
# ==============================================================
@app.route("/donate/food/submit", methods=["POST"])
def submit_food_promise():

    # 1) تأكد إن المستخدم مسجل دخول
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))

    # 2) البيانات القادمة من صفحة promise_food
    donor_id = int(request.form.get("donor_id"))
    item_name = request.form.get("item_name")

    urgency = request.form.get("urgency", "").lower().strip()
    remaining_need = int(request.form.get("remaining_need"))
    user_quantity = int(request.form.get("user_quantity"))

    # 3) منع إدخال كمية أكبر من الحاجة
    if user_quantity > remaining_need:
        flash("Quantity exceeds remaining need.", "danger")
        return redirect(url_for("donate_food"))

    # 4) حفظ الوعد بالداتا بيس
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        INSERT INTO donation_promises 
        (user_id, donor_id, item_name, quantity, urgency, remaining_need, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    """, (
        user_id,
        donor_id,
        item_name,
        user_quantity,
        urgency,
        remaining_need
    ))

    # 5) تقليل الكمية من جدول requested_items
    c.execute("""
        UPDATE requested_items
        SET quantity = quantity - ?
        WHERE donor_id=? AND item_name=? AND status='pending'
    """, (user_quantity, donor_id, item_name))

    # 6) حذف الطلب إذا انتهت الكمية
    c.execute("""
        DELETE FROM requested_items
        WHERE donor_id=? AND item_name=? AND quantity <= 0
    """, (donor_id, item_name))

    conn.commit()
    conn.close()

    # 7) رجوع لصفحة donate_food
    flash("Your donation promise has been sent 💛", "success")
    return redirect(url_for("donate_food"))

# ==============================================================
# 🔑 PASSWORD RESET FLOW
# ==============================================================
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form["email"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user:
            otp = str(random.randint(100000, 999999))
            session["otp"] = otp
            session["reset_email"] = email
            try:
                msg = Message(
                    "Password Reset Verification Code",
                    recipients=[email],
                )
                msg.body = f"Hello {user[1]},\n\nYour password reset verification code is: {otp}"
                mail.send(msg)
                flash("📩 A verification code has been sent to your email.", "info")
            except Exception as e:
                flash(f"⚠️ Failed to send email: {e}", "error")
            return redirect(url_for("verify_otp"))

        flash("⚠️ No account found with that email.", "error")

    return render_template("forgot.html")


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "GET" and not session.get("otp"):
        flash("Please enter your email first.", "error")
        return redirect(url_for("forgot"))

    if request.method == "POST":
        user_otp = request.form["otp"]
        if user_otp == session.get("otp"):
            session["otp_ok"] = True
            session.pop("otp", None)
            flash("✅ Code verified. You can now change your password.", "success")
            return redirect(url_for("reset_password"))

        flash("❌ Invalid code. Try again.", "error")

    return render_template("verify.html")


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if not session.get("otp_ok") or not session.get("reset_email"):
        flash("Please verify your code first.", "error")
        return redirect(url_for("forgot"))

    if request.method == "POST":
        new_password = hash_password(request.form["new_password"])
        email = session.get("reset_email")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
        conn.commit()
        conn.close()

        session.pop("otp_ok", None)
        session.pop("reset_email", None)

        flash("🔐 Password updated successfully!", "success")
        return redirect(url_for("login_page"))

    return render_template("reset.html")

# ==============================================================
# ⭐ PROJECTS PAGE
# ==============================================================
@app.route("/projects")
def projects():
    return render_template("projects.html")

# ==============================================================
# 🌍 API: Food Banks for the Map
# ==============================================================
@app.route("/api/foodbanks")
def api_foodbanks():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT food_bank_name, address, latitude, longitude FROM donors")
    banks = c.fetchall()
    conn.close()

    result = []
    for name, address, lat, lng in banks:
        result.append({
            "name": name,
            "address": address,
            "lat": lat,
            "lng": lng
        })

    return jsonify(result)


@app.route("/help")
def help_page():
    return render_template("help_page.html")

# ==============================================================
# 🚀 START APP
# ==============================================================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

# ==============================================================