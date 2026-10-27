import os

import psycopg
import requests
from flask import Flask, jsonify

app = Flask(__name__)
STUDENTS = [
    {"id": i, "name": f"Sinh viên mẫu {i}", "major": "Công nghệ thông tin", "gpa": 3.0}
    for i in range(1, 6)
]


@app.get('/hello')
def hello():
    return jsonify(message='Hello from MiniCloud!')


@app.get('/student')
def student():
    return jsonify(STUDENTS)


@app.get('/students-db')
def students_db():
    try:
        with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT student_id, fullname, dob, major FROM students ORDER BY id')
                return jsonify([dict(zip(('student_id', 'fullname', 'dob', 'major'), row)) for row in cur.fetchall()])
    except (psycopg.Error, KeyError):
        return jsonify(error='database unavailable'), 503


@app.get('/heteroes-health')
def heteroes_health():
    url = os.environ.get('HETEROES_HEALTH_URL', '')
    if not url:
        return jsonify(status='not configured'), 503
    try:
        response = requests.get(url, timeout=3, allow_redirects=False)
        return jsonify(status_code=response.status_code, reachable=response.ok), 200 if response.ok else 502
    except requests.RequestException:
        return jsonify(error='HeteroES unavailable'), 502
