from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import hashlib
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'секретный-ключ-123'

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            patronymic TEXT,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            deadline DATE,
            priority TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            folder_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (folder_id) REFERENCES folders (id)
        )
    ''')
    
    db.commit()
    db.close()

def hash_password(password):
    return hashlib.sha256((password + "соль123").encode()).hexdigest()

def check_password(password, password_hash):
    return hash_password(password) == password_hash

init_db()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        patronymic = request.form.get('patronymic', '')
        email = request.form['email']
        phone = request.form.get('phone', '')
        password = request.form['password']
        confirm = request.form['confirm_password']
        
        if password != confirm:
            flash('Пароли не совпадают!', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 4:
            flash('Пароль должен быть минимум 4 символа', 'danger')
            return redirect(url_for('register'))
        
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, first_name, last_name, patronymic, email, phone, password_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, first_name, last_name, patronymic, email, phone, hash_password(password)))
            db.commit()
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('login'))
        except:
            flash('Такое имя пользователя или email уже существует!', 'danger')
            return redirect(url_for('register'))
        finally:
            db.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        db.close()
        
        if user and check_password(password, user['password_hash']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Добро пожаловать, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль!', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Сначала войдите в систему!', 'warning')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', (session['user_id'],))
    recent_notes = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) as count FROM notes WHERE user_id = ?', (session['user_id'],))
    notes_count = cursor.fetchone()['count']

    cursor.execute('SELECT * FROM tasks WHERE user_id = ? AND status = "pending" ORDER BY deadline ASC LIMIT 5', (session['user_id'],))
    active_tasks = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) as count FROM tasks WHERE user_id = ?', (session['user_id'],))
    tasks_count = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM tasks WHERE user_id = ? AND status = "pending" AND deadline < date("now")', (session['user_id'],))
    overdue_count = cursor.fetchone()['count']
    
    db.close()
    
    return render_template('dashboard.html', 
                         recent_notes=recent_notes,
                         notes_count=notes_count,
                         active_tasks=active_tasks,
                         tasks_count=tasks_count,
                         overdue_count=overdue_count)


@app.route('/notes')
def notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
    all_notes = cursor.fetchall()
    db.close()
    
    return render_template('notes.html', notes=all_notes)

@app.route('/add_note', methods=['GET', 'POST'])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form.get('content', '')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)',
                      (session['user_id'], title, content))
        db.commit()
        db.close()
        flash('Заметка создана!', 'success')
        return redirect(url_for('notes'))
    
    return render_template('add_note.html')

@app.route('/delete_note/<int:note_id>')
def delete_note(note_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', (note_id, session['user_id']))
    db.commit()
    db.close()
    flash('Заметка удалена!', 'success')
    return redirect(url_for('notes'))


@app.route('/tasks')
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY deadline ASC, created_at DESC', (session['user_id'],))
    all_tasks = cursor.fetchall()
    db.close()
    
    return render_template('tasks.html', tasks=all_tasks)

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        deadline = request.form.get('deadline', '')
        priority = request.form.get('priority', 'normal')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO tasks (user_id, title, description, deadline, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], title, description, deadline, priority))
        db.commit()
        db.close()
        flash('Задача добавлена!', 'success')
        return redirect(url_for('tasks'))
    
    return render_template('add_task.html')

@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE tasks SET status = "completed" WHERE id = ? AND user_id = ?', 
                  (task_id, session['user_id']))
    db.commit()
    db.close()
    flash('Задача выполнена! Отлично!', 'success')
    return redirect(url_for('tasks'))

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, session['user_id']))
    db.commit()
    db.close()
    flash('Задача удалена', 'success')
    return redirect(url_for('tasks'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    db.close()
    
    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if request.method == 'POST':
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        patronymic = request.form.get('patronymic', '')
        phone = request.form.get('phone', '')
        email = request.form['email']
        
        cursor.execute('''
            UPDATE users 
            SET first_name = ?, last_name = ?, patronymic = ?, phone = ?, email = ?
            WHERE id = ?
        ''', (first_name, last_name, patronymic, phone, email, session['user_id']))
        db.commit()
        db.close()
        flash('Профиль обновлён!', 'success')
        return redirect(url_for('profile'))
    
    db.close()
    return render_template('edit_profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/timer')
def timer():
    if 'user_id' not in session:
        flash('Сначала войдите в систему!', 'warning')
        return redirect(url_for('login'))
    
    return render_template('timer.html')
@app.route('/library')
def library():
    if 'user_id' not in session:
        flash('Сначала войдите в систему!', 'warning')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM folders WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
    folders = cursor.fetchall()
    
    cursor.execute('SELECT * FROM links WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
    links = cursor.fetchall()
    
    db.close()
    
    return render_template('library.html', folders=folders, links=links)

@app.route('/add_folder', methods=['GET', 'POST'])
def add_folder():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        
        if name:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('INSERT INTO folders (user_id, name) VALUES (?, ?)',
                          (session['user_id'], name))
            db.commit()
            db.close()
            flash('Папка создана!', 'success')
        return redirect(url_for('library'))
    
    return render_template('add_folder.html')

@app.route('/add_link', methods=['GET', 'POST'])
def add_link():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        folder_id = request.form.get('folder_id')
        title = request.form.get('title')
        url = request.form.get('url')
        description = request.form.get('description', '')
        
        if title and url and folder_id:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('INSERT INTO links (user_id, folder_id, title, url, description) VALUES (?, ?, ?, ?, ?)',
                          (session['user_id'], folder_id, title, url, description))
            db.commit()
            db.close()
            flash('Ссылка добавлена!', 'success')
        return redirect(url_for('library'))
    
    folder_id = request.args.get('folder_id')
    return render_template('add_link.html', folder_id=folder_id)

@app.route('/delete_folder/<int:folder_id>')
def delete_folder(folder_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM links WHERE folder_id = ? AND user_id = ?', (folder_id, session['user_id']))
    cursor.execute('DELETE FROM folders WHERE id = ? AND user_id = ?', (folder_id, session['user_id']))
    db.commit()
    db.close()
    flash('Папка и все ссылки в ней удалены!', 'success')
    return redirect(url_for('library'))

@app.route('/delete_link/<int:link_id>')
def delete_link(link_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM links WHERE id = ? AND user_id = ?', (link_id, session['user_id']))
    db.commit()
    db.close()
    flash('Ссылка удалена!', 'success')
    return redirect(url_for('library'))

if __name__ == '__main__':
    app.run(debug=True)