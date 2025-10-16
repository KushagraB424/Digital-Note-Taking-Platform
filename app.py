from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notes.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    date TEXT,
                    user_id INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash("Signup successful! Please log in.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists. Please try another.")
        finally:
            conn.close()

    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = username
            session['user_id'] = user['id']
            flash("Login successful!")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.")

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    flash("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    # Show only user's own notes
    notes = conn.execute("SELECT * FROM notes WHERE user_id=? ORDER BY date DESC", 
                         (session['user_id'],)).fetchall()
    conn.close()
    return render_template("index.html", notes=notes, user=session['user'])

@app.route('/add_note', methods=['GET', 'POST'])
def add_note():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form['tags']
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = get_db_connection()
        conn.execute("INSERT INTO notes (title, content, tags, date, user_id) VALUES (?, ?, ?, ?, ?)",
                     (title, content, tags, date, session['user_id']))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template("add_note.html")

@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form['tags']
        c.execute("UPDATE notes SET title=?, content=?, tags=?, date=? WHERE id=? AND user_id=?",
                  (title, content, tags, datetime.now().strftime("%Y-%m-%d %H:%M"), note_id, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        c.execute("SELECT * FROM notes WHERE id=? AND user_id=?", (note_id, session['user_id']))
        note = c.fetchone()
        conn.close()
        if note is None:
            flash("Note not found or unauthorized.")
            return redirect(url_for('index'))
        return render_template("edit_note.html", note=note)

@app.route('/delete/<int:note_id>')
def delete_note(note_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("DELETE FROM notes WHERE id=? AND user_id=?", (note_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user' not in session:
        return redirect(url_for('login'))

    results = []
    if request.method == 'POST':
        query = request.form['query']
        conn = get_db_connection()
        results = conn.execute("""SELECT * FROM notes 
                                  WHERE (title LIKE ? OR content LIKE ? OR tags LIKE ?) 
                                  AND user_id=?""",
                               ('%' + query + '%', '%' + query + '%', '%' + query + '%', session['user_id'])).fetchall()
        conn.close()

    return render_template("search.html", results=results, user=session['user'])

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
