from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import boto3
import uuid
import random
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load AWS credentials from the .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "aws_super_secret_key"

# ================= AWS CONFIG =================
# Pulls credentials from your .env file
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

users_table = dynamodb.Table("Users")
admins_table = dynamodb.Table("Admins")
projects_table = dynamodb.Table("Projects")

# ================= LANDING =================
@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ================= USER AUTH =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            users_table.put_item(
                Item={
                    "username": username,
                    "email": email,
                    "password": password
                },
                ConditionExpression="attribute_not_exists(username)"
            )
        except ClientError:
            return "User already exists"

        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        res = users_table.get_item(Key={"username": username})

        if "Item" in res and res["Item"]["password"] == password:
            session["username"] = username
            return redirect(url_for("home"))

        return "Invalid credentials"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ================= USER HOME =================
@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")

# ================= PROJECTS =================
@app.route("/projects")
def projects():
    res = projects_table.scan()
    return render_template("projects_list.html", projects=res.get("Items", []))

# ================= ADMIN SIGNUP =================
@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            admins_table.put_item(
                Item={
                    "email": email,
                    "name": name,
                    "password": password
                },
                ConditionExpression="attribute_not_exists(email)"
            )
        except ClientError:
            return "Admin already exists"

        return redirect(url_for("admin_login"))

    return render_template("admin_signup.html")

# ================= ADMIN AUTH =================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        res = admins_table.get_item(Key={"email": email})

        if "Item" in res and res["Item"]["password"] == password:
            session["admin"] = email
            return redirect(url_for("admin_dashboard"))

        return "Invalid admin credentials"

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ================= ADMIN DASHBOARD =================
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    users = users_table.scan().get("Items", [])
    projects = projects_table.scan().get("Items", [])

    return render_template(
        "admin_dashboard.html",
        users=users,
        projects=projects
    )

# ================= ADMIN CREATE PROJECT =================
@app.route("/admin/create-project", methods=["GET", "POST"])
def admin_create_project():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        project_id = str(uuid.uuid4())

        projects_table.put_item(
            Item={
                "id": project_id,
                "title": title,
                "description": description
            }
        )

        return redirect(url_for("admin_dashboard"))

    return render_template("admin_create_project.html")

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

@app.route("/roadmap")
def roadmap():
    if "username" not in session:
        return redirect(url_for("login"))

    res = profiles_table.get_item(Key={"user_id": session["username"]})
    data = res.get("Item")

    if data:
        # Reference code uses a more flexible 'in' check (software developer vs developer)
        goal = data["career_goal"].lower()
        steps = [ 
            "Understand basics of your chosen field",
            "Learn required core skills",
            "Build beginner projects",
            "Gain practical experience",
            "Create portfolio",
            "Apply for roles"
        ] # Default
        for key, value in ROADMAPS.items():
            if key in goal:
                steps = value
                break
    else:
        steps = []

    return render_template("roadmap.html", steps=steps)

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

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message")
    return jsonify({"reply": chatbot_reply(msg)})

# ================= SKILL CONFIDENCE ================= #
@app.route("/skill-confidence", methods=["GET", "POST"])
def skill_confidence():
    skills = [
        "Python", "SQL", "HTML/CSS", "JavaScript",
        "Machine Learning", "Communication"
    ]

    if request.method == "POST":
        results = []

        for skill in skills:
            level = request.form.get(skill)
            score = {"Beginner": 33, "Intermediate": 66, "Confident": 100}.get(level, 0)

            results.append({
                "skill": skill,
                "level": level,
                "score": score,
                "weak": score <= 33
            })

        return render_template("skill_confidence_result.html", results=results)

    return render_template("skill_confidence.html", skills=skills)

# ================= DAILY TIP =================
CAREER_TIPS = [
    {"tip": "Build projects, not certificates.", "quote": "Skills > Degrees"},
    {"tip": "Consistency wins.", "quote": "Small steps matter"},
    {"tip": "Learn deeply.", "quote": "Depth builds confidence"}
]

@app.context_processor
def inject_daily_tip():
    return {"daily_tip": random.choice(CAREER_TIPS)}

# ================= PROFILE ================= #
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        career_goal = request.form["career_goal"]
        current_level = request.form["current_level"]
        interests = request.form["interests"]
        time = request.form["time_per_week"]

        # Saving user data to AWS DynamoDB Profiles table
        profiles_table.put_item(
            Item={
                "user_id": session["username"],
                "career_goal": career_goal,
                "current_level": current_level,
                "interests": interests,
                "time_per_week": time
            }
        )
        return redirect(url_for("roadmap"))

    res = profiles_table.get_item(Key={"user_id": session["username"]})
    profile_data = res.get("Item")
    
    return render_template("profile.html", profile=profile_data)


# ================= SKILL GAP ================= #
@app.route("/skill-gap", methods=["GET", "POST"])
def skill_gap():
    if "username" not in session:
        return redirect(url_for("login"))

    SKILL_MAP_DATA = {
    "software developer": ["Python", "Data Structures", "OOP", "Git", "HTML", "CSS", "JavaScript", "Flask / Django", "SQL"],
    "data scientist": ["Python", "Statistics", "NumPy", "Pandas", "Data Visualization", "SQL", "Machine Learning", "Model Evaluation"],
    "ui ux designer": ["Design Principles", "Color Theory", "Typography", "Figma", "Wireframing", "User Research", "Prototyping"]
    }

    if request.method == "POST":
        role = request.form["role"]
        known_skills = request.form.getlist("skills")
        required_skills = SKILL_MAP_DATA.get(role, [])
        missing_skills = [s for s in required_skills if s not in known_skills]

        return render_template("skill_gap_result.html", role=role, known=known_skills, missing=missing_skills)

    return render_template("skill_gap.html", skill_map=SKILL_MAP_DATA)

# ================= RESUME ANALYSIS ================= #
@app.route("/resume", methods=["GET", "POST"])
def resume():
    analysis = None
    if request.method == "POST":
        resume_text = request.form.get("resume_text", "").lower()
        target_role = request.form.get("role", "").lower() # Ensure your HTML has this input
        
        score = 0
        strengths = []
        
        # Section checks (Sync with reference logic)
        sections = {"education": 15, "skills": 15, "projects": 15, "experience": 15}
        for sec, pts in sections.items():
            if sec in resume_text:
                score += pts
                strengths.append(f"{sec.capitalize()} Section Found")

        # Role-based skill check (This makes it 'smart')
        role_skills = {
            "data scientist": ["python", "pandas", "sql", "machine learning"],
            "software developer": ["python", "git", "flask", "css"]
        }
        
        required = role_skills.get(target_role, [])
        missing_skills = [s for s in required if s not in resume_text]
        score += max(0, 40 - (len(missing_skills) * 10))

        analysis = {"score": min(score, 100), "strengths": strengths, "missing_skills": missing_skills}

    return render_template("resume.html", analysis=analysis)

# ================= CAREER QUIZ ================= #

CAREER_QUIZ_DATA = [
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
        # Updated to include all 5 categories from your app.py
        scores = {
            "developer": 0, "data_scientist": 0, "designer": 0, 
            "cybersecurity": 0, "product_manager": 0
        }
        
        # Logic to count votes
        for key in request.form:
            answer = request.form.get(key)
            if answer in scores:
                scores[answer] += 1
        
        # Get the highest score
        winner = max(scores, key=scores.get)
        
        career_names = {
            "developer": "Software Developer",
            "data_scientist": "Data Scientist",
            "designer": "UI/UX Designer",
            "cybersecurity": "Cybersecurity Analyst",
            "product_manager": "Product Manager"
        }
        
        session["quiz_result"] = career_names[winner]
        return render_template("quiz_result.html", careers=[session["quiz_result"]], insight="Based on your interests!")
    
    # Passing the new dictionary to your template
    return render_template("career_quiz.html", quiz=CAREER_QUIZ_DATA)

# ================= RECOMMENDATIONS ================= #

@app.route("/recommendations")
def recommendations():
    career = session.get("quiz_result", "Software Developer")
    
    recs = {
        "Software Developer": {"internships": ["Web Intern", "Backend Intern"], "projects": ["E-commerce Site"]},
        "Data Scientist": {"internships": ["Analytics Intern"], "projects": ["Weather Predictor"]}
    }
    
    data = recs.get(career)
    return render_template("recommendations.html", career=career, internships=data["internships"], projects=data["projects"])

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)