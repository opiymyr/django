import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

print("=" * 50)
print("ТАБЛИЦЫ В БАЗЕ ДАННЫХ:")
print("=" * 50)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"📁 {table[0]}")

print("\n" + "=" * 50)
print("ПОЛЬЗОВАТЕЛИ:")
print("=" * 50)
cursor.execute("SELECT id, username, email, first_name, last_name, phone FROM users")
users = cursor.fetchall()
for user in users:
    print(f"ID: {user[0]}, Имя: {user[1]}, Email: {user[2]}, Телефон: {user[5]}")

print("\n" + "=" * 50)
print("ЗАМЕТКИ:")
print("=" * 50)
cursor.execute("SELECT id, user_id, title, content FROM notes")
notes = cursor.fetchall()
for note in notes:
    print(f"ID: {note[0]}, Пользователь: {note[1]}, Заголовок: {note[2]}")
    print(f"   Текст: {note[3][:50]}...")
print("\n" + "=" * 50)
print("ЗАДАЧИ:")
print("=" * 50)
cursor.execute("SELECT id, user_id, title, deadline, priority FROM tasks")
tasks = cursor.fetchall()
for task in tasks:
    print(f"ID: {task[0]}, Пользователь: {task[1]}, Задача: {task[2]}, Дедлайн: {task[3]}, Важность: {task[4]}")

conn.close()