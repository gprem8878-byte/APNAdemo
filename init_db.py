import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "students.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ---------- Students table with SECTION ----------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            department TEXT NOT NULL,
            section TEXT NOT NULL
        )
    ''')

    # ---------- Admin table ----------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')

    # ---------- FAQ table ----------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT NOT NULL,
            question_keywords TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    ''')

    # ---------- Unknown Queries ----------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unknown_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            department TEXT,
            question TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ---------- Students (5 per department) ----------
    students = [
        # ---------------- BCA STUDENTS ----------------
        ('bca001', 'Rishabh Gupta', generate_password_hash('12345'), 'BCA', 'A1'),
        ('bca002', 'Shreya Mehta', generate_password_hash('23456'), 'BCA', 'A2'),
        ('bca003', 'Karan Singh', generate_password_hash('34567'), 'BCA', 'A3'),
        ('bca004', 'Priya Rawat', generate_password_hash('45678'), 'BCA', 'A4'),
        ('bca005', 'Manish Verma', generate_password_hash('56789'), 'BCA', 'A5'),

        # ---------------- CSE STUDENTS ----------------
        ('cse001', 'Anuj Kumar', generate_password_hash('11111'), 'CSE', 'E1'),
        ('cse002', 'Rahul Verma', generate_password_hash('22222'), 'CSE', 'E2'),
        ('cse003', 'Ayushi Sharma', generate_password_hash('33333'), 'CSE', 'E3'),
        ('cse004', 'Harshit Chauhan', generate_password_hash('44444'), 'CSE', 'E4'),
        ('cse005', 'Neeraj Joshi', generate_password_hash('55555'), 'CSE', 'E5'),

        # ---------------- ECE STUDENTS ----------------
        ('ece001', 'Neha Sharma', generate_password_hash('99999'), 'ECE', 'B1'),
        ('ece002', 'Sakshi Joshi', generate_password_hash('88888'), 'ECE', 'B2'),
        ('ece003', 'Ravi Singh', generate_password_hash('77777'), 'ECE', 'B3'),
        ('ece004', 'Aditya Rana', generate_password_hash('66666'), 'ECE', 'B4'),
        ('ece005', 'Pooja Thakur', generate_password_hash('55555'), 'ECE', 'B5'),
    ]

    cursor.executemany(
        "INSERT OR REPLACE INTO students VALUES (?, ?, ?, ?, ?)", students
    )

    # ---------- Admin Account ----------
    cursor.execute(
        "INSERT OR REPLACE INTO admin VALUES (?, ?)",
        ("admin", generate_password_hash("admin123"))
    )

    # ---------- FAQ Answers ----------
    faq_entries = [
        ('ALL', 'erp, portal, login', 'GEHU ERP Portal: https://student.gehu.ac.in'),
        ('ALL', 'holiday, holidays, notice', 'Latest GEHU Notices: https://gehu.ac.in/content/gehu/en/news-events.html'),
        ('ALL', 'your name, bot name', 'I am GEHU Helper Bot 🤖'),
        ('ALL', 'who made you, creator', 'I was created by a student of GEHU.'),
        ('ALL', 'thanks, thank you', 'You’re welcome! 😊'),
    ]

    cursor.executemany(
        "INSERT INTO faq (department, question_keywords, answer) VALUES (?, ?, ?)",
        faq_entries
    )

    conn.commit()
    conn.close()
    print("\n🎉 Database initialized successfully with 15 students + admin + FAQ + section support!\n")


if __name__ == "__main__":
    init_db()
