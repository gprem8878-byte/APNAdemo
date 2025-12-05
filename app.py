from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime
from werkzeug.security import check_password_hash

# ----------- RENDER-FRIENDLY DATA DIRECTORY -----------
DATA_DIR = "/opt/render/project/src/data"

STUDENTS_FILE = os.path.join(DATA_DIR, "students.json")
FAQ_FILE = os.path.join(DATA_DIR, "faq.json")
ADMIN_FILE = os.path.join(DATA_DIR, "admin.json")
UNKNOWN_FILE = os.path.join(DATA_DIR, "unknown_queries.json")

# auto create data folder
os.makedirs(DATA_DIR, exist_ok=True)

# auto create missing json files
for file in [STUDENTS_FILE, FAQ_FILE, ADMIN_FILE, UNKNOWN_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            f.write("[]")  # default empty list

app = Flask(__name__)
app.secret_key = os.urandom(24)


# ------------ JSON LOAD/SAVE HELPERS ------------

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ------------ STUDENT & FAQ HELPERS ------------

def get_student(student_id):
    students = load_json(STUDENTS_FILE, [])
    for stu in students:
        if stu["id"] == student_id:
            return stu
    return None


def get_admin():
    admins = load_json(ADMIN_FILE, {})
    return admins


def find_faq_answer(dept, user_text):
    faqs = load_json(FAQ_FILE, [])
    user_text = user_text.lower()

    dept_faqs = [f for f in faqs if f["department"] == dept]
    global_faqs = [f for f in faqs if f["department"] == "ALL"]

    all_rows = dept_faqs + global_faqs
    best_score = 0
    best_answer = None

    for row in all_rows:
        keywords = row["question_keywords"].lower().split(",")
        score = sum(1 for kw in keywords if kw.strip() in user_text)
        if score > best_score:
            best_score = score
            best_answer = row["answer"]

    return best_answer


def save_unknown_query(student_id, dept, question):
    unknowns = load_json(UNKNOWN_FILE, [])
    unknowns.append({
        "student_id": student_id,
        "department": dept,
        "question": question,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_json(UNKNOWN_FILE, unknowns)


# ------------ ROUTES ------------

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        student_id = request.form["student_id"]
        password = request.form["password"]

        student = get_student(student_id)
        if student and check_password_hash(student["password"], password):
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]
            session["department"] = student["department"]
            session["section"] = student["section"]
            return redirect(url_for("chat"))

        error = "Invalid Student ID or Password"

    return render_template("login.html", error=error)


@app.route("/chat")
def chat():
    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "chat.html",
        student_id=session["student_id"],
        dept=session["department"]
    )


@app.route("/get")
def chatbot_response():
    if "student_id" not in session:
        return jsonify({"response": "Session expired, login again."})

    text = request.args.get("msg", "").strip()
    text_lower = text.lower()

    dept = session["department"]
    section = session["section"]
    name = session["student_name"]

    # Greetings
    if text_lower in ["hi", "hello", "hey"]:
        return jsonify({"response": f"Hello {name}! 😊 How can I help you today?"})

    if "how are you" in text_lower:
        return jsonify({"response": "I'm doing great! How can I assist you today?"})

    # Block other section timetables
    all_sections = ["A1","A2","A3","A4","A5",
                    "E1","E2","E3","E4","E5",
                    "B1","B2","B3","B4","B5"]

    for sec in all_sections:
        if sec.lower() in text_lower:
            if sec != section:
                return jsonify({"response":
                    f"Sorry {name}, you cannot view timetable of {sec}. "
                    f"I can only show YOUR section ({section})."
                })

    # Holiday / Academic Calendar
    holiday_keys = [
        "holiday","holidays","vacation","next semester",
        "semester start","academic calendar","calendar"
    ]

    if any(key in text_lower for key in holiday_keys):
        return jsonify({
            "response": "Here is the Academic Calendar:<br>"
                        "<img src='/static/academic/holiday.png' style='max-width:90%;border-radius:10px;'>"
        })

    # Subject-specific syllabus
    if "syllabus" in text_lower and not any(sub in text_lower for sub in ["dbms","ai","ds"]):
        return jsonify({"response":
            "Please mention the subject 😊<br>Available: <b>DBMS, AI, DS</b>"
        })

    for sub in ["dbms", "ai", "ds"]:
        if sub in text_lower:
            return jsonify({
                "response": (
                    f"Syllabus for {sub.upper()} ({dept}):<br>"
                    f"<img src='/static/syllabus/{dept}/{sub.upper()}.png' style='max-width:90%;border-radius:10px;'>"
                )
            })

    # Timetable
    if "timetable" in text_lower or "time table" in text_lower:
        return jsonify({
            "response": (
                f"Timetable for {dept} - {section}:<br>"
                f"<img src='/static/timetable/{dept}/{section}.png' style='max-width:90%;border-radius:10px;'>"
            )
        })

    # FAQ text answers
    ans = find_faq_answer(dept, text_lower)
    if ans:
        return jsonify({"response": ans})

    # Unknown question
    save_unknown_query(session["student_id"], dept, text)
    return jsonify({"response": "I am not sure about that 🤔<br>Your question has been forwarded to the admin."})


# ------------ ADMIN PANEL ------------

@app.route("/admin", methods=["GET","POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin = get_admin()
        if (admin.get("username") == username and
            check_password_hash(admin.get("password"), password)):
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))

        error = "Invalid admin credentials"

    return render_template("admin_login.html", error=error)


@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin"))

    unknown = load_json(UNKNOWN_FILE, [])
    return render_template("admin_dashboard.html", unknowns=unknown)


@app.route("/admin/add_faq", methods=["POST"])
def admin_add_faq():
    if "admin" not in session:
        return redirect(url_for("admin"))

    dept = request.form["department"]
    keywords = request.form["keywords"]
    answer = request.form["answer"]

    faqs = load_json(FAQ_FILE, [])
    faqs.append({
        "department": dept,
        "question_keywords": keywords,
        "answer": answer
    })
    save_json(FAQ_FILE, faqs)

    return redirect(url_for("admin_dashboard"))


# ------------ MAIN ------------

if __name__ == "__main__":
    app.run()
