from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# ================= DATABASE =================
DB_PATH = os.path.join(os.path.dirname(__file__), "career.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create all necessary tables if they don't exist."""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            career_goal TEXT,
            current_level TEXT,
            interests TEXT,
            time_per_week INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            roadmap TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    db.commit()
    db.close()

# Initialize DB at startup
init_db()

# ================= ROADMAP LOGIC =================
def generate_roadmap_logic(profile):
    goal = profile["career_goal"].lower()
    level = profile["current_level"].lower()
    time = int(profile["time_per_week"])

    steps = []

    if "data" in goal:
        steps = [
            "Python fundamentals",
            "Statistics & Probability",
            "Pandas, NumPy, SQL",
            "Data visualization",
            "Mini data projects",
            "Internship preparation"
        ]
    elif "ai" in goal:
        steps = [
            "Python & math foundations",
            "Machine Learning basics",
            "Neural Networks",
            "TensorFlow / PyTorch",
            "AI projects"
        ]
    elif "web" in goal:
        steps = [
            "HTML, CSS, JavaScript",
            "React fundamentals",
            "Flask backend",
            "Databases",
            "Deploy full-stack apps"
        ]
    else:
        steps = [
            "Learn field basics",
            "Build core skills",
            "Create projects",
            "Apply for roles"
        ]

    if level == "beginner":
        steps.insert(0, "Programming fundamentals")

    if time < 5:
        steps.append("Follow a slow-paced learning plan")

    return steps

# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for("signup"))

        password_hash = generate_password_hash(password)
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, password_hash, "user")
            )
            db.commit()
            flash("Signup successful. Login now.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already exists", "danger")
            return redirect(url_for("signup"))
        finally:
            db.close()

    return render_template("signup.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password are required!", "danger")
            return redirect(url_for("login"))

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = dict(user)
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(url_for("home"))

        flash("Invalid credentials", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("index"))

# ================= HOME =================
@app.route("/home")
def home():
    if "user" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))
    return render_template("home.html", user=session["user"])

# ================= PROFILE =================
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    user_id = session["user"]["id"]
    db = get_db()

    if request.method == "POST":
        career_goal = request.form.get("career_goal")
        current_level = request.form.get("current_level")
        interests = request.form.get("interests")
        time_per_week = request.form.get("time_per_week")

        if not career_goal or not current_level or not interests or not time_per_week:
            flash("All profile fields are required!", "danger")
            db.close()
            return redirect(url_for("profile"))

        db.execute("""
            INSERT OR REPLACE INTO profiles
            (user_id, career_goal, current_level, interests, time_per_week)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, career_goal, current_level, interests, time_per_week))
        db.commit()
        flash("Profile saved successfully", "success")

    profile = db.execute(
        "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
    ).fetchone()
    db.close()
    return render_template("profile.html", user=session["user"], profile=profile)

# ================= ROADMAP =================
@app.route("/generate_roadmap", methods=["POST"])
def generate_roadmap():
    if "user" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    user_id = session["user"]["id"]
    db = get_db()

    profile = db.execute(
        "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
    ).fetchone()

    if not profile:
        flash("Complete your profile first", "warning")
        db.close()
        return redirect(url_for("profile"))

    steps = generate_roadmap_logic(profile)
    db.execute("""
        INSERT INTO roadmaps (user_id, roadmap, created_at)
        VALUES (?, ?, ?)
    """, (user_id, "\n".join(steps), datetime.now().strftime("%Y-%m-%d %H:%M")))
    db.commit()
    db.close()
    return redirect(url_for("roadmap"))

@app.route("/roadmap")
def roadmap():
    if "user" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    user_id = session["user"]["id"]
    db = get_db()
    data = db.execute(
        "SELECT roadmap FROM roadmaps WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    ).fetchone()
    db.close()

    steps = data["roadmap"].split("\n") if data else []
    return render_template("roadmap.html", steps=steps)

# ================= CHATBOT PAGE =================
@app.route("/chat_page")
def chat_page():
    if "user" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login"))
    return render_template("chat.html", user=session["user"])

# ================= CHATBOT API =================
@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "").lower()

    # Simple AI reply logic
    if "ai" in msg:
        reply = "AI needs Python, ML, and projects."
    elif "data" in msg:
        reply = "Data science mixes stats, Python, and SQL."
    elif "web" in msg:
        reply = "Web dev = frontend + backend + deployment."
    else:
        reply = "Ask me about AI, Data Science, or Web Dev."

    return jsonify({"reply": reply})

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
