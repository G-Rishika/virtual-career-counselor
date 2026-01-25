from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# ================= DATABASE =================

def get_db():
    conn = sqlite3.connect("career.db")
    conn.row_factory = sqlite3.Row
    return conn

# ================= ROADMAP LOGIC =================

def generate_roadmap_logic(profile):
    steps = []
    goal = profile["career_goal"].lower()
    level = profile["current_level"].lower()
    time = int(profile["time_per_week"])

    if "data" in goal:
        steps = [
            "Learn Python basics",
            "Statistics & Probability",
            "Pandas, NumPy, Matplotlib",
            "SQL & Databases",
            "Mini Data Projects",
            "Internship preparation"
        ]
    elif "ai" in goal:
        steps = [
            "Python fundamentals",
            "Linear Algebra & Calculus",
            "Machine Learning basics",
            "Neural Networks",
            "TensorFlow / PyTorch",
            "AI Projects"
        ]
    elif "web" in goal:
        steps = [
            "HTML, CSS, JavaScript",
            "Frontend frameworks (React)",
            "Backend with Flask",
            "Databases",
            "Deploy full-stack projects"
        ]
    else:
        steps = [
            "Understand field basics",
            "Learn core skills",
            "Build projects",
            "Apply for entry-level roles"
        ]

    if level == "beginner":
        steps.insert(0, "Computer & programming basics")

    if time < 5:
        steps.append("Follow a slow-paced learning schedule")

    return steps

# ================= ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            db.commit()
        except:
            flash("Email already exists", "danger")
            return redirect(url_for("signup"))

        flash("Signup successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user"] = dict(user)
            flash("Logged in successfully", "success")
            return redirect(url_for("home"))

        flash("Invalid credentials", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("index"))

@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")

# ================= PROFILE =================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    user_id = session["user"]["id"]

    if request.method == "POST":
        db.execute(
            """
            INSERT OR REPLACE INTO profiles
            (user_id, career_goal, current_level, interests, time_per_week)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                request.form["career_goal"],
                request.form["current_level"],
                request.form["interests"],
                request.form["time_per_week"]
            )
        )
        db.commit()
        flash("Profile saved successfully", "success")

    profile = db.execute(
        "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
    ).fetchone()

    return render_template("profile.html", user=session["user"], profile=profile)

# ================= ROADMAP =================

@app.route("/generate-roadmap", methods=["POST"])
def generate_roadmap():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    user_id = session["user"]["id"]

    profile = db.execute(
        "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
    ).fetchone()

    if not profile:
        flash("Complete your profile first", "warning")
        return redirect(url_for("profile"))

    steps = generate_roadmap_logic(profile)

    db.execute(
        "INSERT INTO roadmaps (user_id, roadmap, created_at) VALUES (?, ?, ?)",
        (user_id, "\n".join(steps), datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    db.commit()

    return redirect(url_for("roadmap"))

@app.route("/roadmap")
def roadmap():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    roadmap = db.execute(
        "SELECT * FROM roadmaps WHERE user_id = ? ORDER BY id DESC",
        (session["user"]["id"],)
    ).fetchone()

    steps = roadmap["roadmap"].split("\n") if roadmap else []

    return render_template("roadmap.html", steps=steps)

# ================= CHATBOT =================

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "").lower()

    reply = "Ask me about Data Science, AI, or Web Development."

    if "data" in msg:
        reply = "Data Science needs Python, statistics, SQL, and ML."
    elif "ai" in msg:
        reply = "AI focuses on machine learning and neural networks."
    elif "web" in msg:
        reply = "Web dev involves frontend, backend, and databases."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
