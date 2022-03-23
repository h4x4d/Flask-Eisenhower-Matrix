from flask import jsonify, request

from flask_restful import Resource, abort, reqparse
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from data import db_session
from data.tasks import Task
from data.users import User

status_parser = reqparse.RequestParser()
status_parser.add_argument('new_status', required=True)


def abort_if_task_not_found(task_id, user_id):
    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == task_id,
                                      Task.user_id == user_id).first()
    if not task:
        abort(404, message=f'Task №{task_id} not found.')


def authorize(token):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.tokens.like(f'%{token}%')).first()
    if user:
        return user.id
    else:
        abort(403, message=f'User auth token is not valid')


class TaskResource(Resource):
    def get(self, task_id):
        user_id = authorize(request.headers['token'])
        abort_if_task_not_found(task_id, user_id)

        db_sess = db_session.create_session()
        task = db_sess.query(Task).filter(Task.id == task_id,
                                          Task.user_id == user_id).first()

        return jsonify({'tasks': task.to_dict(only=('name', 'description',
                                                    'filename', 'is_urgent',
                                                    'is_important'))})

    def delete(self, task_id):
        user_id = authorize(request.headers['token'])
        abort_if_task_not_found(task_id, user_id)

        db_sess = db_session.create_session()
        task = db_sess.query(Task).filter(Task.id == task_id,
                                          Task.user_id == user_id).first()

        if task:
            db_sess.delete(task)
            db_sess.commit()

            return jsonify({'success': True})

    def post(self, task_id):
        user_id = authorize(request.headers['token'])
        args = status_parser.parse_args()

        abort_if_task_not_found(task_id, user_id)
        db_sess = db_session.create_session()
        task = db_sess.query(Task).filter(Task.id == task_id,
                                          Task.user_id == user_id).first()

        task.status = args['new_status']
        db_sess.commit()

        return self.get(task_id)


parser = reqparse.RequestParser()
parser.add_argument('name', required=True)
parser.add_argument('description')
parser.add_argument('is_important', default=False, type=bool)
parser.add_argument('is_urgent', default=False, type=bool)
parser.add_argument('file', type=FileStorage, location='files')


class TaskListResource(Resource):
    def get(self):
        user_id = authorize(request.headers['token'])
        db_sess = db_session.create_session()
        tasks = db_sess.query(Task).filter(Task.user_id == user_id).all()
        return jsonify({'news': [i.to_dict(only=('name', 'description',
                                                 'filename', 'is_urgent',
                                                 'is_important'))
                                 for i in tasks]})

    def post(self):
        user_id = authorize(request.headers['token'])
        args = parser.parse_args()
        db_sess = db_session.create_session()

        task = Task()
        task.user_id = user_id

        task_check = db_sess.query(Task).filter(Task.user_id == user_id,
                                                Task.name == args['name']
                                                ).first()
        if task_check:
            abort(404, message='Repeated name. Change it to create task')

        task.name = args['name'].capitalize()
        if args['description']:
            task.description = args['description']

        task.is_important = args['is_important']
        task.is_urgent = args['is_urgent']

        if args['file']:
            file = args['file']
            filename = secure_filename(file.filename)
            file.save('db/user_files/' + filename)
            task.filename = filename

        db_sess.add(task)
        db_sess.commit()

        return jsonify({'tasks': task.to_dict(only=('name', 'description',
                                                 'filename', 'is_urgent',
                                                 'is_important'))})
