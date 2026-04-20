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
            failed_questions TEXT DEFAULT '[]',
            ticket_number INTEGER,
            last_active REAL,
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
            options TEXT, -- JSON list of options for MCQ
            type TEXT DEFAULT 'test', -- 'test' (MCQ) or 'yopiq' (Open)
            score INTEGER DEFAULT 10,
            FOREIGN KEY (competition_id) REFERENCES competitions (id) ON DELETE CASCADE
        )
    ''')

    # Create ticket_questions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS ticket_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
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
                      
    # Migration: Add columns if they don't exist
    try:
        c.execute('ALTER TABLE students ADD COLUMN last_active REAL')
    except sqlite3.OperationalError: pass
        
    try:
        c.execute('ALTER TABLE students ADD COLUMN ticket_number INTEGER')
    except sqlite3.OperationalError: pass

    try:
        c.execute('ALTER TABLE students ADD COLUMN failed_questions TEXT DEFAULT "[]"')
    except sqlite3.OperationalError: pass

    try:
        c.execute('ALTER TABLE questions ADD COLUMN type TEXT DEFAULT "test"')
    except sqlite3.OperationalError: pass

    try:
        c.execute('ALTER TABLE questions ADD COLUMN options TEXT')
    except sqlite3.OperationalError: pass
        
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
            score = 10 # Default score
            options = json.dumps(q.get('options', []))
            c.execute('INSERT INTO questions (competition_id, topic, question, answer, options, type, score) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (comp_id, q['topic'], q['question'], q['answer'], options, q.get('type', 'test'), score))
                      
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

def update_competition_time_limit(comp_id, limit_seconds):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE competitions SET time_limit = ? WHERE id = ?', (limit_seconds, comp_id))
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
        try:
            st_dict['failed_questions'] = json.loads(st_dict['failed_questions'])
        except:
            st_dict['failed_questions'] = []
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
        try:
            st_dict['failed_questions'] = json.loads(st_dict['failed_questions'])
        except:
            st_dict['failed_questions'] = []
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
        try:
            d['failed_questions'] = json.loads(d['failed_questions'])
        except:
            d['failed_questions'] = []
        result.append(d)
    return result

def update_student_progress(student_id, solved_list, failed_list):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE students SET solved_questions = ?, failed_questions = ?, score = ? WHERE id = ?', 
              (json.dumps(solved_list), json.dumps(failed_list), len(solved_list), student_id))
    conn.commit()
    conn.close()

def reset_scores(competition_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE students SET score = 0, solved_questions = '[]', failed_questions = '[]', ticket_number = NULL WHERE competition_id = ?", (competition_id,))
    c.execute('UPDATE competitions SET status = "pending", start_time = NULL WHERE id = ?', (competition_id,))
    conn.commit()
    conn.close()

def update_last_active(student_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE students SET last_active = ? WHERE id = ?', (time.time(), student_id))
    conn.commit()
    conn.close()

def delete_inactive_students(competition_id):
    conn = get_connection()
    c = conn.cursor()
    # Delete students with 0 score
    c.execute('DELETE FROM students WHERE competition_id = ? AND score = 0', (competition_id,))
    conn.commit()
    conn.close()

# --- Ticket Management ---

def assign_tickets_randomly(competition_id):
    conn = get_connection()
    c = conn.cursor()
    # Ensure tickets are generated for this competition if they don't exist
    c.execute('SELECT COUNT(*) FROM ticket_questions WHERE question_id IN (SELECT id FROM questions WHERE competition_id = ?)', (competition_id,))
    if c.fetchone()[0] == 0:
        generate_tickets_for_competition(competition_id)

    # Get all students in the competition
    c.execute('SELECT id FROM students WHERE competition_id = ?', (competition_id,))
    students = c.fetchall()
    
    import random
    for student in students:
        ticket_num = random.randint(1, 20)
        c.execute('UPDATE students SET ticket_number = ? WHERE id = ?', (ticket_num, student['id']))
    
    conn.commit()
    conn.close()

def generate_tickets_for_competition(competition_id):
    conn = get_connection()
    c = conn.cursor()
    
    # Get all questions for this competition
    c.execute('SELECT id, type FROM questions WHERE competition_id = ?', (competition_id,))
    questions = [dict(r) for r in c.fetchall()]
    
    test_qs = [q['id'] for q in questions if q['type'] == 'test']
    yopiq_qs = [q['id'] for q in questions if q['type'] == 'yopiq']
    
    import random
    
    for ticket_num in range(1, 21):
        # Pick 15 test questions (if enough, otherwise repeat)
        selected_test = random.sample(test_qs, min(15, len(test_qs)))
        while len(selected_test) < 15 and test_qs:
             selected_test.append(random.choice(test_qs))
             
        # Pick 5 yopiq questions
        selected_yopiq = random.sample(yopiq_qs, min(5, len(yopiq_qs)))
        while len(selected_yopiq) < 5 and yopiq_qs:
            selected_yopiq.append(random.choice(yopiq_qs))
            
        all_selected = selected_test + selected_yopiq
        for q_id in all_selected:
            c.execute('INSERT INTO ticket_questions (ticket_number, question_id) VALUES (?, ?)', (ticket_num, q_id))
            
    conn.commit()
    conn.close()

def get_ticket_questions(competition_id, ticket_number):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT q.* FROM questions q
        JOIN ticket_questions tq ON q.id = tq.question_id
        WHERE q.competition_id = ? AND tq.ticket_number = ?
        ORDER BY q.id ASC
    ''', (competition_id, ticket_number))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def setup_tickets(competition_id, tickets_data):
    """
    tickets_data: dict {ticket_num: [question_ids]}
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM ticket_questions WHERE question_id IN (SELECT id FROM questions WHERE competition_id = ?)', (competition_id,))
    for ticket_num, q_ids in tickets_data.items():
        for q_id in q_ids:
            c.execute('INSERT INTO ticket_questions (ticket_number, question_id) VALUES (?, ?)', (ticket_num, q_id))
    conn.commit()
    conn.close()
