from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import webbrowser
import threading
import os
from werkzeug.security import check_password_hash

DB_PATH = "students.db"

app = Flask(__name__)
app.secret_key = os.urandom(24)


# ------------------ DB helper ------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def find_faq_answer(dept, user_text):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT question_keywords, answer FROM faq WHERE department = ?", (dept,))
    dept_rows = cursor.fetchall()

    cursor.execute("SELECT question_keywords, answer FROM faq WHERE department = 'ALL'")
    global_rows = cursor.fetchall()

    all_rows = list(dept_rows) + list(global_rows)

    best_score = 0
    best_answer = None
    user_text = user_text.lower()

    for row in all_rows:
        keywords = row["question_keywords"].lower().split(",")
        score = sum(1 for kw in keywords if kw.strip() in user_text)
        if score > best_score:
            best_score = score
            best_answer = row["answer"]

    conn.close()
    return best_answer


def save_unknown_query(student_id, department, question):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO unknown_queries (student_id, department, question) VALUES (?, ?, ?)",
        (student_id, department, question)
    )
    conn.commit()
    conn.close()


# ------------------ ROUTES ------------------

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']

        student = get_student(student_id)
        if student and check_password_hash(student["password"], password):
            session['student_id'] = student["id"]
            session['student_name'] = student["name"]
            session['department'] = student["department"]
            session['section'] = student["section"]
            return redirect(url_for("chat"))
        else:
            error = "Invalid Student ID or Password"

    return render_template("login.html", error=error)


@app.route('/chat')
def chat():
    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "chat.html",
        student_id=session["student_id"],
        dept=session["department"]
    )


@app.route('/get')
def chatbot_response():
    if "student_id" not in session:
        return jsonify({"response": "Session expired, please login again."})

    text = request.args.get("msg", "").strip()
    if not text:
        return jsonify({"response": "Please type something."})

    text_lower = text.lower()
    dept = session["department"]
    section = session["section"]
    stu_name = session["student_name"]

    # -------------------- GREETINGS --------------------
    if text_lower in ["hi", "hello", "hey"]:
        return jsonify({"response": f"Hello {stu_name}! 😊 How can I assist you today?"})

    if "how are you" in text_lower:
        return jsonify({"response": "I'm doing great! What can I help you with today?"})

    # -------------------- BLOCK OTHER SECTIONS' TIMETABLES --------------------
    sections = ["A1","A2","A3","A4","A5","E1","E2","E3","E4","E5","B1","B2","B3","B4","B5"]

    for sec in sections:
        if sec.lower() in text_lower:
            if sec != section:  
                return jsonify({
                    "response": f"Sorry {stu_name}, you are not allowed to view timetable of {sec}. "
                                f"I can only show your section ({section}) timetable."
                })

    # -------------------- ACADEMIC CALENDAR / HOLIDAYS --------------------
    holiday_keywords = [
        "holiday", "holidays", "vacation", "next semester",
        "semester start", "academic calendar", "calendar",
        "when will semester start", "when does semester start"
    ]

    for key in holiday_keywords:
        if key in text_lower:
            img_path = "/static/academic/holiday.png"
            return jsonify({
                "response": f"Here is the Academic Calendar (Holidays & Semester Schedule):<br>"
                            f"<img src='{img_path}' style='max-width:90%; border-radius:10px;'>"
            })

    # -------------------- ASK SUBJECT IF ONLY SYLLABUS IS MENTIONED --------------------
    if "syllabus" in text_lower and not any(sub in text_lower for sub in ["dbms", "ai", "ds"]):
        return jsonify({
            "response": "Please mention the subject 😊<br>Available subjects: <b>DBMS, AI, DS</b>"
        })

    # -------------------- SUBJECT-WISE SYLLABUS (AI / DBMS / DS) --------------------
    subjects = ["dbms", "ai", "ds"]

    for sub in subjects:
        if sub in text_lower:   # Now works even if user writes only "AI"
            img_path = f"/static/syllabus/{dept}/{sub.upper()}.png"
            return jsonify({
                "response": f"Syllabus for {sub.upper()} ({dept}):<br>"
                            f"<img src='{img_path}' style='max-width:90%; border-radius:10px;'>"
            })

    # -------------------- SECTION-WISE TIMETABLE --------------------
    if "timetable" in text_lower or "time table" in text_lower:
        img_path = f"/static/timetable/{dept}/{section}.png"
        return jsonify({
            "response": f"Timetable for {dept} - Section {section}:<br>"
                        f"<img src='{img_path}' style='max-width:90%; border-radius:10px;'>"
        })

    # -------------------- FAQ TEXT ANSWERS --------------------
    answer = find_faq_answer(dept, text_lower)
    if answer:
        return jsonify({"response": answer})

    # -------------------- SAVE UNKNOWN QUESTION --------------------
    save_unknown_query(session["student_id"], dept, text)
    return jsonify({"response": "I am not sure about that 🤔<br>Your question has been forwarded to the admin."})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------ ADMIN PANEL ------------------

@app.route("/admin", methods=['GET', 'POST'])
def admin_login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username = ?", (username,))
        admin = cursor.fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid admin credentials"

    return render_template("admin_login.html", error=error)


@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM unknown_queries ORDER BY created_at DESC")
    unknowns = cursor.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", unknowns=unknowns)


@app.route("/admin/add_faq", methods=['POST'])
def admin_add_faq():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    dept = request.form["department"]
    keywords = request.form["keywords"]
    answer = request.form["answer"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO faq (department, question_keywords, answer) VALUES (?, ?, ?)",
        (dept, keywords, answer)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))


# ------------------ MAIN ------------------

if __name__ == "__main__":
    port = 5000

    def open_browser():
        webbrowser.open_new(f"http://127.0.0.1:{port}/")

    threading.Timer(1, open_browser).start()
    app.run(debug=True, port=port, use_reloader=False)
