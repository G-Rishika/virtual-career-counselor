from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_key"

# ================= ADMIN CREDENTIALS =================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# =====================================================

DB_NAME = "career.db"

# -------------------- DATABASE --------------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER,
        career_goal TEXT,
        current_level TEXT,
        interests TEXT,
        time_per_week INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)


    conn.commit()
    conn.close()


init_db()


# ================= ROADMAP ================= #

ROADMAPS = {
    "software developer": [
        "Learn Python or Java basics",
        "Understand data structures and algorithms",
        "Build small projects (calculator, todo app)",
        "Learn Git & GitHub",
        "Explore backend or frontend",
        "Do internships or freelance projects",
        "Apply for junior developer roles"
    ],
    "data scientist": [
        "Learn Python and statistics",
        "Master NumPy, Pandas, Matplotlib",
        "Learn SQL and data cleaning",
        "Understand machine learning basics",
        "Build real datasets projects",
        "Learn model deployment",
        "Apply for data roles"
    ],
    "ui ux designer": [
        "Understand design principles",
        "Learn Figma or Adobe XD",
        "Practice wireframing",
        "Build design case studies",
        "Learn user research",
        "Create portfolio",
        "Apply for design internships"
    ]
}


def generate_roadmap(goal):
    goal = goal.lower()
    for key in ROADMAPS:
        if key in goal:
            return ROADMAPS[key]
    return [
        "Understand basics of your chosen field",
        "Learn required core skills",
        "Build beginner projects",
        "Gain practical experience",
        "Create portfolio",
        "Apply for roles"
    ]


# ================= CHATBOT ================= #

def chatbot_reply(msg):
    msg = msg.lower()

    if "career" in msg:
        return "Tell me your interests and strengths. I’ll help you choose a career path."

    if "software" in msg:
        return "Software development is a solid choice. Want a roadmap?"

    if "data" in msg:
        return "Data science needs math + coding. Want a learning plan?"

    if "confused" in msg or "help" in msg:
        return "Totally normal. Career clarity takes time. Start with interests."

    if "roadmap" in msg:
        return "Go to Profile → enter your career goal → generate roadmap ✨"

    return "I’m here for career guidance 🌱 Ask me about careers, skills, or roadmaps."


# -------------------- ROUTES --------------------

# 🔥 LANDING PAGE LOGIC (IMPORTANT)
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
        except:
            return "User already exists"
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # 🚫 Already logged in? straight to dashboard
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))

        return "Invalid credentials"

    return render_template("login.html")


# 🎯 DASHBOARD (HOME)
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        career_goal = request.form["career_goal"]
        current_level = request.form["current_level"]
        interests = request.form["interests"]
        time = request.form["time_per_week"]

        cur.execute("DELETE FROM profiles WHERE user_id=?", (session["user_id"],))
        cur.execute("""
            INSERT INTO profiles VALUES (?, ?, ?, ?, ?)
        """, (session["user_id"], career_goal, current_level, interests, time))
        conn.commit()

        return redirect(url_for("roadmap"))

    cur.execute("SELECT * FROM profiles WHERE user_id=?", (session["user_id"],))
    profile = cur.fetchone()
    conn.close()

    return render_template("profile.html", profile=profile)


@app.route("/roadmap")
def roadmap():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT career_goal FROM profiles WHERE user_id=?", (session["user_id"],))
    data = cur.fetchone()
    conn.close()

    steps = generate_roadmap(data["career_goal"]) if data else []
    return render_template("roadmap.html", steps=steps)

SKILL_MAP = {
    "software developer": [
        "Python",
        "Data Structures",
        "OOP",
        "Git",
        "HTML",
        "CSS",
        "JavaScript",
        "Flask / Django",
        "SQL"
    ],
    "data scientist": [
        "Python",
        "Statistics",
        "NumPy",
        "Pandas",
        "Data Visualization",
        "SQL",
        "Machine Learning",
        "Model Evaluation"
    ],
    "ui ux designer": [
        "Design Principles",
        "Color Theory",
        "Typography",
        "Figma",
        "Wireframing",
        "User Research",
        "Prototyping"
    ]
}

@app.route("/skill-gap", methods=["GET", "POST"])
def skill_gap():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        role = request.form["role"]
        known_skills = request.form.getlist("skills")

        required_skills = SKILL_MAP.get(role, [])
        missing_skills = [s for s in required_skills if s not in known_skills]

        return render_template(
            "skill_gap_result.html",
            role=role,
            known=known_skills,
            missing=missing_skills
        )

    return render_template("skill_gap.html", skill_map=SKILL_MAP)

@app.route("/projects")
def projects():
    projects = [
        {
            "title": "Software Developer",
            "problem_statement": "Build applications, websites, and systems"
        },
        {
            "title": "Data Scientist",
            "problem_statement": "Analyze data and build predictive models"
        },
        {
            "title": "UI/UX Designer",
            "problem_statement": "Design user-friendly digital experiences"
        }
    ]
    return render_template("projects_list.html", projects=projects)


@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message")
    reply = chatbot_reply(msg)
    return jsonify({"reply": reply})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ================= ADMIN AUTH =================

@app.route("/admin")
def admin_home():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    return render_template("admin.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM admins WHERE email=? AND password=?",
            (email, password)
        )
        admin = cur.fetchone()
        conn.close()

        if admin:
            session["admin"] = admin["email"]
            return redirect(url_for("admin_home"))

        return "Invalid admin credentials"

    return render_template("admin_login.html")


@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO admins (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
        except:
            return "Admin already exists"
        finally:
            conn.close()

        return redirect(url_for("admin_login"))

    return render_template("admin_signup.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")

@app.route("/admin/users")
def admin_users():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users")
    users = cur.fetchall()
    conn.close()

    return render_template("admin_users.html", users=users)

@app.route("/admin/create-project", methods=["GET", "POST"])
def admin_create_project():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT
            )
        """)
        cur.execute(
            "INSERT INTO projects (title, description) VALUES (?, ?)",
            (title, description)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("admin_dashboard"))

    return render_template("admin_create_project.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ================= RESUME ANALYSIS ================= #

@app.route("/resume", methods=["GET", "POST"])
def resume():
    analysis = None

    if request.method == "POST":
        resume_text = request.form.get("resume_text", "").lower()
        target_role = request.form.get("role", "").lower()

        score = 0
        feedback = []
        strengths = []
        missing = []

        # ---------- BASIC CHECKS ----------
        sections = {
            "education": ["education", "degree", "college", "university"],
            "skills": ["skills", "technologies", "tools"],
            "projects": ["project", "projects"],
            "experience": ["experience", "internship", "work"]
        }

        for section, keywords in sections.items():
            if any(k in resume_text for k in keywords):
                score += 15
                strengths.append(section.capitalize())
            else:
                missing.append(section.capitalize())

        # ---------- SKILL GAP ----------
        role_skills = {
            "data scientist": ["python", "pandas", "numpy", "machine learning", "sql"],
            "web developer": ["html", "css", "javascript", "react", "flask"],
            "ai engineer": ["python", "machine learning", "deep learning", "tensorflow"]
        }

        required_skills = role_skills.get(target_role, [])
        missing_skills = [s for s in required_skills if s not in resume_text]

        score += max(0, 40 - len(missing_skills) * 8)

        if score > 100:
            score = 100

        analysis = {
            "score": score,
            "strengths": strengths,
            "missing_sections": missing,
            "missing_skills": missing_skills
        }

    return render_template("resume.html", analysis=analysis)


# ================= CAREER QUIZ ================= #

career_quiz = [
    {
        "question": "Do you enjoy logic or creativity more?",
        "options": {
            "Logic & problem solving": "developer",
            "Data & patterns": "data_scientist",
            "Creativity & design": "designer",
            "Security & investigation": "cybersecurity",
            "Planning & leadership": "product_manager"
        }
    },
    {
        "question": "How do you like to work?",
        "options": {
            "Independently with code": "developer",
            "Analyzing data deeply": "data_scientist",
            "Designing user experiences": "designer",
            "Protecting systems": "cybersecurity",
            "Coordinating teams": "product_manager"
        }
    },
    {
        "question": "Which tool excites you most?",
        "options": {
            "VS Code": "developer",
            "Python & Pandas": "data_scientist",
            "Figma": "designer",
            "Firewalls & Networks": "cybersecurity",
            "Roadmaps & Strategy": "product_manager"
        }
    }
]

@app.route("/career-quiz", methods=["GET", "POST"])
def career_quiz_page():
    if request.method == "POST":
        scores = {
            "developer": 0,
            "data_scientist": 0,
            "designer": 0,
            "cybersecurity": 0,
            "product_manager": 0
        }

        for answers in request.form.lists():
            for selected in answers[1]:
                scores[selected] += 1

        top_careers = sorted(scores, key=scores.get, reverse=True)[:3]

        career_names = {
            "developer": "Software Developer",
            "data_scientist": "Data Scientist",
            "designer": "UI/UX Designer",
            "cybersecurity": "Cybersecurity Analyst",
            "product_manager": "Product Manager"
        }

        personality = {
            "developer": "You love logic, structure, and building things from scratch.",
            "data_scientist": "You enjoy patterns, insights, and data-driven decisions.",
            "designer": "You’re creative, user-focused, and visually expressive.",
            "cybersecurity": "You think like a protector and love challenges.",
            "product_manager": "You’re a planner, leader, and big-picture thinker."
        }

        return render_template(
            "quiz_result.html",
            careers=[career_names[c] for c in top_careers],
            insight=personality[top_careers[0]]
        )

    return render_template("career_quiz.html", quiz=career_quiz)

# ================= INTERSHIP & PROJECTS RECOMMENDATION ================= #

CAREER_RECOMMENDATIONS = {
    "Data Analyst": {
        "internships": [
            "Data Analysis Internship",
            "Business Intelligence Intern",
            "Excel & SQL Intern"
        ],
        "projects": [
            "Sales Data Dashboard",
            "Customer Churn Analysis",
            "COVID Data Visualization"
        ]
    },
    "Software Developer": {
        "internships": [
            "Python Developer Intern",
            "Web Developer Intern",
            "Backend Developer Intern"
        ],
        "projects": [
            "Flask Web App",
            "Task Manager App",
            "REST API using Python"
        ]
    },
    "Machine Learning Engineer": {
        "internships": [
            "ML Internship",
            "AI Research Intern",
            "Data Science Intern"
        ],
        "projects": [
            "Spam Email Classifier",
            "Face Recognition System",
            "Movie Recommendation System"
        ]
    }
}

@app.route("/recommendations")
def recommendations():
    # For now, assume quiz result is stored in session
    career = session.get("quiz_result", "Data Analyst")

    data = CAREER_RECOMMENDATIONS.get(career)

    return render_template(
        "recommendations.html",
        career=career,
        internships=data["internships"],
        projects=data["projects"]
    )

import random

CAREER_TIPS = [
    {
        "tip": "Build projects, not just certificates.",
        "quote": "Your degree doesn’t define you. Your skills do."
    },
    {
        "tip": "Consistency beats talent when talent sleeps.",
        "quote": "Small steps every day lead to big wins."
    },
    {
        "tip": "Learn one new skill deeply instead of ten superficially.",
        "quote": "Depth creates confidence."
    },
    {
        "tip": "Your first project won’t be perfect — and that’s okay.",
        "quote": "Progress > Perfection."
    },
    {
        "tip": "Real learning starts when tutorials end.",
        "quote": "Struggle is a sign you’re growing."
    }
]

@app.context_processor
def inject_daily_tip():
    return {
        "daily_tip": random.choice(CAREER_TIPS)
    }

@app.route("/skill-confidence", methods=["GET", "POST"])
def skill_confidence():
    skills = [
        "Python",
        "Data Structures",
        "SQL",
        "HTML/CSS",
        "JavaScript",
        "Machine Learning",
        "Communication",
        "Problem Solving"
    ]

    results = []

    if request.method == "POST":
        for skill in skills:
            level = request.form.get(skill)

            score_map = {
                "Beginner": 33,
                "Intermediate": 66,
                "Confident": 100
            }

            score = score_map.get(level, 0)

            results.append({
                "skill": skill,
                "level": level,
                "score": score,
                "weak": score <= 33
            })

        return render_template("skill_confidence_result.html", results=results)

    return render_template("skill_confidence.html", skills=skills)

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True)
