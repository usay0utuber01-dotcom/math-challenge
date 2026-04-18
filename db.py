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
    # Create students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            solved_questions TEXT DEFAULT '[]'
        )
    ''')
    # Create state table
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    # Create questions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            score INTEGER DEFAULT 10
        )
    ''')
    
    # Initialize competition state if not exists
    c.execute('INSERT OR IGNORE INTO app_state (key, value) VALUES ("competition_started", "false")')
    
    # Seed questions if table is empty
    c.execute('SELECT COUNT(*) FROM questions')
    if c.fetchone()[0] == 0:
        for q in QUESTIONS:
            c.execute('INSERT INTO questions (topic, question, answer, score) VALUES (?, ?, ?, ?)',
                      (q['topic'], q['question'], q['answer'], 10))
                      
    conn.commit()
    conn.close()

def get_all_questions():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM questions ORDER BY id ASC')
    questions = c.fetchall()
    conn.close()
    return [dict(q) for q in questions]

def add_question(topic, question, answer, score=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO questions (topic, question, answer, score) VALUES (?, ?, ?, ?)',
              (topic, question, answer, score))
    conn.commit()
    conn.close()

def delete_question(question_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()

def add_student(first_name, last_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO students (first_name, last_name) VALUES (?, ?)', (first_name, last_name))
    student_id = c.lastrowid
    conn.commit()
    conn.close()
    return student_id

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

def get_all_students():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM students ORDER BY score DESC')
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

def is_competition_started():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT value FROM app_state WHERE key = "competition_started"')
    row = c.fetchone()
    conn.close()
    if row:
        return row['value'] == 'true'
    return False

def get_competition_start_time():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT value FROM app_state WHERE key = "competition_start_time"')
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return float(row['value'])
        except ValueError:
            return None
    return None

def set_competition_started(started: bool):
    conn = get_connection()
    c = conn.cursor()
    val = "true" if started else "false"
    c.execute('INSERT OR REPLACE INTO app_state (key, value) VALUES ("competition_started", ?)', (val,))
    
    if started:
        c.execute('INSERT OR REPLACE INTO app_state (key, value) VALUES ("competition_start_time", ?)', (str(time.time()),))
    else:
        # Reset start time if stopped
        c.execute('DELETE FROM app_state WHERE key = "competition_start_time"')
        
    conn.commit()
    conn.close()
    
def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM students')
    c.execute('UPDATE app_state SET value = "false" WHERE key = "competition_started"')
    c.execute('DELETE FROM app_state WHERE key = "competition_start_time"')
    conn.commit()
    conn.close()
