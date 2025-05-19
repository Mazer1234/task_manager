from flask import Flask, render_template, request, redirect, flash, session
import sqlite3
import datetime

DATABASE_FILE = "tasks.db"
USER_DATABASE_FILE = "users.db"

# Функция для установления соединения с БД
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

def get_user_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(USER_DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Ошибка при подключении к бд {e}")
        return None


def create_table():
    """"Создает таблицу 'tasks', если её нет"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                status TEXT CHECK (status IN ('todo', 'in_progress', 'done')), --Статус задачи
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP, --дата создания задачи
                user_id INTEGER
            )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT
                )
            """)
            conn.commit()
            print("Таблица 'tasks' создана или уже существует")
        except sqlite3.Error as e:
            print(f"Ошибка при создании таблицы: {e}")
        finally:
            conn.close()

create_table()

#Создает приложение фласк
app = Flask(__name__)

app.secret_key = "Password123"

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
                    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                    user = cursor.fetchone()
                    conn.commit()

                    session['user_id'] = user["id"]
                    session["username"] = username
                    flash("Вы успешно вошли в систему")

                    return redirect("/todolist")
                except sqlite3.Error as e:
                    print(f"Ошибка при работе с БД {e}")
                    conn.rollback()
                finally:
                    conn.close()
        flash("Пожалуйста, введите имя пользователя", "error")
        return render_template("login.html")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("Вы вышли из системы", "info")
    return redirect("/")
@app.route("/todolist")   #Обозначение пути на сайте(Здесь task-manager)
def index():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE status = 'todo'")
            tasks = cursor.fetchall() # Получаем задачи со статусом todo
            cursor.execute("SELECT * FROM tasks WHERE status = 'done'")
            done_tasks = cursor.fetchall() # Получаем задачи со статусом сделанные

            tasks_with_index = list(enumerate(tasks))
            done_tasks_with_index = list(enumerate(done_tasks))
            return render_template('index.html', tasks=tasks_with_index, done_tasks=done_tasks_with_index)
        except sqlite3.Error as e:
            print(f"Ошибка при получении задач: {e}")
            return "Ошибка при загрузке задач", 500
        finally:
            conn.close()
    else:
        return "Ошибка подключении к базе данных", 500

@app.route("/todolist/add", methods=["POST"]) #Здесь добавление
def add():
    if "user_id" not in session:
        return redirect("/login")

    task_text = request.form.get("task")

    if task_text:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO tasks (title, status, user_id) VALUES (?, 'todo', ?)", (task_text,session["user_id"])) # по умолчанию статус todo
                conn.commit()
                flash("Задача добавлена в бд", "info")
            except sqlite3.Error as e:
                print(f"Ошибка при добавлении задачи {e}")
                conn.rollback() #Откат изменений
            finally:
                conn.close()
    return redirect('/todolist')


@app.route("/todolist/delete/<int:task_id>")
def delete(task_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE (id = ?, user_id = ?)", (task_id,session["user_id"]))
            conn.commit()
            print("Задача успешно удалена")
        except sqlite3.Error as e:
            print(f"Ошибка удаления задачи: {e}")
            conn.rollback()
        finally:
            conn.close()
    return redirect('/todolist')


@app.route("/todolist/done/<int:task_id>")
def done(task_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status = 'done' WHERE ID = ?", (task_id,))
            conn.commit()
            print("Задача успешно помечена как сделанная")
        except sqlite3.Error as e:
            print(f"Ошибка при смене статуса задачи: {e}")
            conn.rollback()
        finally:
            conn.close()
    return redirect("/todolist")


@app.route("/show_user")
def show_user():
    if "username" in session:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (session["user_id"],))
                user_tasks = cursor.fetchall()
                return render_template("show_user.html", username=session["username"], tasks=user_tasks)
            except sqlite3.Error as e:
                print(f"Ошибка при получении задач {e}")
                return "Ошибка при загрузке данных", 500
            finally:
                conn.close()
    flash("Пожалуйста, войдите в систему", "error")
    return redirect("/login")

@app.errorhandler(404)
def page_not_found(e):
    return "Страница не найдена :(", 404

@app.route("/")
def first_page():
    return render_template("first_page.html")
def validete_date(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

if (__name__=="__main__"):
    app.run(debug=True)