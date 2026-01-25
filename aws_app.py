from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aws_secret")

REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

users_table = dynamodb.Table("Users")
profiles_table = dynamodb.Table("Profiles")
roadmaps_table = dynamodb.Table("Roadmaps")

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

def notify(subject, message):
    if SNS_TOPIC_ARN:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)

# ================= ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        name = request.form["name"]

        if "Item" in users_table.get_item(Key={"email": email}):
            flash("User already exists")
            return redirect(url_for("signup"))

        users_table.put_item(Item={
            "email": email,
            "name": name,
            "password": password
        })

        notify("New Signup", email)
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users_table.get_item(Key={"email": email}).get("Item")

        if user and check_password_hash(user["password"], password):
            session["user"] = user
            notify("Login", email)
            return redirect(url_for("home"))

        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ================= PROFILE =================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]["email"]

    if request.method == "POST":
        profiles_table.put_item(Item={
            "email": email,
            "career_goal": request.form["career_goal"],
            "current_level": request.form["current_level"],
            "interests": request.form["interests"],
            "time_per_week": request.form["time_per_week"]
        })

    profile = profiles_table.get_item(Key={"email": email}).get("Item")
    return render_template("profile.html", user=session["user"], profile=profile)

# ================= ROADMAP =================

@app.route("/generate_roadmap", methods=["POST"])
def generate_roadmap():
    email = session["user"]["email"]

    profile = profiles_table.get_item(Key={"email": email}).get("Item")
    if not profile:
        flash("Complete your profile first")
        return redirect(url_for("profile"))

    steps = [
        "Build fundamentals",
        "Learn core tools",
        "Build projects",
        "Apply for roles"
    ]

    roadmaps_table.put_item(Item={
        "email": email,
        "steps": steps,
        "created_at": datetime.utcnow().isoformat()
    })

    return redirect(url_for("roadmap"))

@app.route("/roadmap")
def roadmap():
    email = session["user"]["email"]
    data = roadmaps_table.get_item(Key={"email": email}).get("Item")
    steps = data["steps"] if data else []
    return render_template("roadmap.html", steps=steps)

# ================= CHATBOT =================

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "").lower()

    if "ai" in msg:
        reply = "AI loves Python, ML, and math."
    elif "data" in msg:
        reply = "Data science = stats + Python + SQL."
    else:
        reply = "Ask me about AI, Data, or Web careers."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
