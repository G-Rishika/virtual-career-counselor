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

# ================= CHATBOT =================
def chatbot_reply(msg):
    msg = msg.lower()

    if "career" in msg:
        return "Tell me your interests — I’ll guide you."
    if "software" in msg:
        return "Software dev is solid. Want a roadmap?"
    if "data" in msg:
        return "Data roles need Python + stats."
    return "Ask me about careers, skills, or projects 🌱"

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message")
    return jsonify({"reply": chatbot_reply(msg)})

# ================= SKILL CONFIDENCE =================
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

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)