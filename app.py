from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ---------- Routes ----------
@app.route('/')
def index():
    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute("SELECT * FROM notes ORDER BY date DESC")
    notes = c.fetchall()
    conn.close()
    return render_template("index.html", notes=notes)

@app.route('/add_note', methods=['GET', 'POST'])
def add_note():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form['tags']
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect("notes.db")
        c = conn.cursor()
        c.execute("INSERT INTO notes (title, content, tags, date) VALUES (?, ?, ?, ?)",
                  (title, content, tags, date))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template("add_note.html")

@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form['tags']
        c.execute("UPDATE notes SET title=?, content=?, tags=?, date=? WHERE id=?",
                  (title, content, tags, datetime.now().strftime("%Y-%m-%d %H:%M"), note_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        c.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        note = c.fetchone()
        conn.close()
        return render_template("edit_note.html", note=note)

@app.route('/delete/<int:note_id>')
def delete_note(note_id):
    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        query = request.form['query']
        conn = sqlite3.connect("notes.db")
        c = conn.cursor()
        c.execute("SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?",
                  ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
        results = c.fetchall()
        conn.close()
    return render_template("search.html", results=results)
    
if __name__ == "__main__":
    app.run(debug=True)
