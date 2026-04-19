import sqlite3
import os
import time
import json
from questions import QUESTIONS

DB_PATH = "math_challenge.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Create competitions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            admin_password TEXT NOT NULL,
            status TEXT DEFAULT 'pending', -- 'pending', 'started', 'finished'
            start_time REAL,
            time_limit INTEGER DEFAULT 1800 -- 30 minutes in seconds
        )
    ''')
    
    # Create students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            password TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            solved_questions TEXT DEFAULT '[]',
            FOREIGN KEY (competition_id) REFERENCES competitions (id) ON DELETE CASCADE
        )
    ''')
    
    # Create questions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            score INTEGER DEFAULT 10,
            FOREIGN KEY (competition_id) REFERENCES competitions (id) ON DELETE CASCADE
        )
    ''')
    
    # Check if a default competition exists
    c.execute('SELECT COUNT(*) FROM competitions')
    if c.fetchone()[0] == 0:
        # Create a default competition for migration/initial setup
        c.execute('''
            INSERT INTO competitions (name, code, admin_password, status) 
            VALUES ("Asosiy Musobaqa", "0000", "admin", "pending")
        ''')
        default_id = c.lastrowid
        
        # Seed questions for the default competition
        for i, q in enumerate(QUESTIONS):
            score = (i + 1) * 10
            c.execute('INSERT INTO questions (competition_id, topic, question, answer, score) VALUES (?, ?, ?, ?, ?)',
                      (default_id, q['topic'], q['question'], q['answer'], score))
                      
    conn.commit()
    conn.close()

# --- Competition Management ---

def create_competition(name, code, admin_password, time_limit_min=30):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO competitions (name, code, admin_password, time_limit) 
            VALUES (?, ?, ?, ?)
        ''', (name, code, admin_password, time_limit_min * 60))
        comp_id = c.lastrowid
        
        # Seed with default questions for new competitions too
        for i, q in enumerate(QUESTIONS):
            score = (i + 1) * 10
            c.execute('INSERT INTO questions (competition_id, topic, question, answer, score) VALUES (?, ?, ?, ?, ?)',
                      (comp_id, q['topic'], q['question'], q['answer'], score))
                      
        conn.commit()
        return comp_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def delete_competition(comp_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM competitions WHERE id = ?', (comp_id,))
    conn.commit()
    conn.close()

def get_all_competitions():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM competitions ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_competition_by_code(code):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM competitions WHERE code = ?', (code,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_competition_by_id(comp_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM competitions WHERE id = ?', (comp_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def update_competition_status(comp_id, status, start_time=None):
    conn = get_connection()
    c = conn.cursor()
    if start_time:
        c.execute('UPDATE competitions SET status = ?, start_time = ? WHERE id = ?', (status, start_time, comp_id))
    else:
        c.execute('UPDATE competitions SET status = ? WHERE id = ?', (status, comp_id))
    conn.commit()
    conn.close()

# --- Question Management ---

def get_all_questions(competition_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM questions WHERE competition_id = ? ORDER BY id ASC', (competition_id,))
    questions = c.fetchall()
    conn.close()
    return [dict(q) for q in questions]

def add_question(competition_id, topic, question, answer, score=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO questions (competition_id, topic, question, answer, score) VALUES (?, ?, ?, ?, ?)',
              (competition_id, topic, question, answer, score))
    conn.commit()
    conn.close()

def delete_question(question_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()

# --- Student Management ---

def add_student(competition_id, first_name, last_name, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO students (competition_id, first_name, last_name, password) 
        VALUES (?, ?, ?, ?)
    ''', (competition_id, first_name, last_name, password))
    student_id = c.lastrowid
    conn.commit()
    conn.close()
    return student_id

def get_student_by_login(competition_id, first_name, last_name, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM students 
        WHERE competition_id = ? AND first_name = ? AND last_name = ? AND password = ?
    ''', (competition_id, first_name, last_name, password))
    row = c.fetchone()
    conn.close()
    if row:
        st_dict = dict(row)
        st_dict['solved_questions'] = json.loads(st_dict['solved_questions'])
        return st_dict
    return None

def get_student(student_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = c.fetchone()
    conn.close()
    if student:
        st_dict = dict(student)
        try:
            st_dict['solved_questions'] = json.loads(st_dict['solved_questions'])
        except:
            st_dict['solved_questions'] = []
        return st_dict
    return None

def get_all_students(competition_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE competition_id = ? ORDER BY score DESC', (competition_id,))
    students = c.fetchall()
    conn.close()
    
    result = []
    for s in students:
        d = dict(s)
        try:
            d['solved_questions'] = json.loads(d['solved_questions'])
        except:
            d['solved_questions'] = []
        result.append(d)
    return result

def update_score(student_id, new_score, solved_questions_list):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE students SET score = ?, solved_questions = ? WHERE id = ?', 
              (new_score, json.dumps(solved_questions_list), student_id))
    conn.commit()
    conn.close()

def reset_scores(competition_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE students SET score = 0, solved_questions = '[]' WHERE competition_id = ?", (competition_id,))
    c.execute('UPDATE competitions SET status = "pending", start_time = NULL WHERE id = ?', (competition_id,))
    conn.commit()
    conn.close()

