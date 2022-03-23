import random
import string

from flask import Flask, render_template, redirect, send_from_directory, \
    jsonify, request

from flask_login import LoginManager, login_required, login_user, logout_user, \
    current_user
from flask_restful import Api

from werkzeug.utils import secure_filename

from data import db_session
from data.users import User
from data.tasks import Task

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from flask_wtf.file import FileField
from wtforms.validators import DataRequired

import tasks_resources

from settings import *

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = SECRET_KEY

api = Api(app)
api.add_resource(tasks_resources.TaskListResource, '/api/tasks')
api.add_resource(tasks_resources.TaskResource, '/api/tasks/<int:task_id>')

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    check_password = PasswordField('Повторить пароль',
                                   validators=[DataRequired()])
    submit = SubmitField('Войти')


class TaskForm(FlaskForm):
    name = StringField('Короткое имя', validators=[DataRequired()])
    description = StringField('Описание')
    is_important = BooleanField('Это важно')
    is_urgent = BooleanField('Это срочно')
    file = FileField('Дополнительные файлы')

    submit = SubmitField('Создать задачу')


@app.route('/')
def index():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        user_tasks = db_sess.query(Task).filter(Task.user_id == current_user.id,
                                                Task.status == 0)

        groups = {
            'important_urgent': [],
            'non_important_urgent': [],
            'important_non_urgent': [],
            'non_important_non_urgent': []
        }

        for t in user_tasks:
            if t.is_urgent:
                if t.is_important:
                    groups['important_urgent'].append([t.id, t.name])
                else:
                    groups['non_important_urgent'].append([t.id, t.name])
            else:
                if t.is_important:
                    groups['important_non_urgent'].append([t.id, t.name])
                else:
                    groups['non_important_non_urgent'].append([t.id, t.name])

        return render_template('index.html', groups=groups)
    else:
        return redirect('/login')


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return render_template('settings.html')
    else:
        if request.form['submit'] == 'get_key':
            db_sess = db_session.create_session()

            user = current_user.id
            user = db_sess.query(User).filter(User.id == user).first()

            token = [random.choice(string.ascii_lowercase +
                                   string.digits) for _ in range(30)]
            token = ''.join(token)

            user.tokens += token + ', '
            db_sess.commit()

            return render_template('settings.html', token=token)

        elif request.form['submit'] == 'delete_key':
            db_sess = db_session.create_session()

            user = current_user.id
            user = db_sess.query(User).filter(User.id == user).first()

            user.tokens = ''
            db_sess.commit()

            return render_template('settings.html', deleted=True)

        elif request.form['submit'] == 'delete_news':
            db_sess = db_session.create_session()

            user = current_user.id
            tasks = db_sess.query(Task).filter(Task.user_id == user).all()

            for i in tasks:
                db_sess.delete(i)

            db_sess.commit()
            return render_template('settings.html', news_deleted=True)

        else:
            return redirect('/logout')


@app.route('/finished')
def finished():
    db_sess = db_session.create_session()
    finished_tasks = db_sess.query(Task).filter(Task.user_id == current_user.id,
                                                Task.status == 1).all()

    return render_template('finished.html', finished_tasks=finished_tasks)


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = TaskForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        check_tasks = db_sess.query(Task).filter(Task.name == form.name.data,
                                                 Task.user_id ==
                                                 current_user.id).first()
        if check_tasks:
            return render_template('add.html',
                                   message='Кажется, задача с таким '
                                           'именем у вас уже есть',
                                   form=form)

        task_to_add = Task()
        task_to_add.name = form.name.data.capitalize()
        if form.description.data:
            task_to_add.description = form.description.data.capitalize()
        task_to_add.is_important = form.is_important.data
        task_to_add.is_urgent = form.is_urgent.data
        task_to_add.user_id = current_user.id

        if form.file.data:
            f = form.file.data
            filename = secure_filename(f.filename)
            task_to_add.filename = filename
            f.save('db/user_files/' + filename)

        db_sess.add(task_to_add)
        db_sess.commit()

        return redirect('/')

    return render_template('add.html', form=form)


@app.route('/task/<int:task_id>')
def task(task_id):
    db_sess = db_session.create_session()
    task_to_file = db_sess.query(Task).filter(Task.id == task_id,
                                              Task.user_id ==
                                              current_user.id).first()
    if task_to_file:
        status = f'это {"важно" if task_to_file.is_important else "не важно"}' \
                 f' и {"срочно" if task_to_file.is_urgent else "не срочно"}'
        return render_template('task.html', task=task_to_file, status=status)
    return redirect('/')


@app.route('/attachment/<int:task_id>')
def attachments(task_id):
    db_sess = db_session.create_session()
    task_to_file = db_sess.query(Task).filter(Task.id == task_id,
                                              Task.user_id ==
                                              current_user.id).first()
    if task_to_file:
        return send_from_directory(f'db/user_files/', task_to_file.filename)
    return redirect('/')


@app.route('/delete/<int:task_id>')
def delete(task_id):
    db_sess = db_session.create_session()
    task_to_delete = db_sess.query(Task).filter(Task.id == task_id,
                                                Task.user_id ==
                                                current_user.id).first()

    if task_to_delete:
        db_sess.delete(task_to_delete)
        db_sess.commit()
        if task_to_delete.status == 1:
            return redirect('/finished')
    return redirect('/')


@app.route('/finish/<int:task_id>')
def finish(task_id):
    db_sess = db_session.create_session()
    task_to_finish = db_sess.query(Task).filter(Task.id == task_id,
                                                Task.user_id ==
                                                current_user.id).first()

    if task_to_finish:
        task_to_finish.status = 1
        db_sess.commit()

    return redirect('/')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == form.login.data).first()
        if form.password.data == form.check_password.data and not user:
            user = User()
            user.login = form.login.data
            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.commit()
            login_user(user)
            return redirect("/")
        elif user:
            return render_template('register.html',
                                   message="Данный логин занят",
                                   form=form)

        return render_template('register.html',
                               message="Пароли не совпадают",
                               form=form)
    return render_template('register.html', form=form)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


def main():
    db_session.global_init(DB_PATH)
    app.run(APP_TO_RUN)


if __name__ == '__main__':
    main()
