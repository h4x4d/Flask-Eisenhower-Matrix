import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from sqlalchemy import orm


class Task(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'tasks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    filename = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_important = sqlalchemy.Column(sqlalchemy.Boolean)
    is_urgent = sqlalchemy.Column(sqlalchemy.Boolean)
    status = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')