from flask import Flask, render_template, request, redirect

#Создает приложение фласк
app = Flask(__name__)

#Виртуальное хранение задач
tasks = []
done_tasks = []

@app.route("/")   #Обозначение пути на сайте(Здесь главная страница)
def index():
    tasks_with_index = list(enumerate(tasks))
    done_tasks_with_index = list(enumerate(done_tasks))
    return render_template('index.html', tasks=tasks_with_index, done_tasks=done_tasks_with_index)

@app.route("/add", methods=["POST"]) #Здесь добавление
def add():
    task_text = request.form.get("task")
    if task_text:
        tasks.append(task_text)
    return redirect("/")

@app.route("/delete/<int:index>")
def delete(index):
    if 0 <= index < len(tasks):
        tasks.pop(index)
    return redirect("/")

@app.route("/done/<int:index>")
def done(index):
    if 0 <= index < len(tasks):
        done_tasks.append(tasks[index]);
        delete(index);
    return redirect("/")

@app.route("/show/<username>")
def show_user(username):
    return render_template("show_user.html", user=username)

@app.route("/show/<username>/back")
def back(username):
    return redirect("/")

@app.errorhandler(404)
def page_not_found(e):
    return "Страница не найдена :(", 404

if (__name__=="__main__"):
    app.run(debug=True)