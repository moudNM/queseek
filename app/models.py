from datetime import datetime
import pytz
from app import db, Base
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey

import random


class User(UserMixin, Base):
    __tablename__ = "users"

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=datetime.now(pytz.timezone('Asia/Singapore')))


class UserProfile(UserMixin, Base):
    __tablename__ = "userProfile"

    id = db.Column(db.String, ForeignKey('users.id'), primary_key=True)
    level = db.Column(db.Integer, nullable=False, default=1)
    coinsBalance = db.Column(db.Integer, nullable=False, default=50)
    coinsCollected = db.Column(db.Integer, nullable=False, default=0)
    coinsToNext = db.Column(db.Integer, nullable=False, default=20)
    avatarId = db.Column(db.String, ForeignKey('Avatars.avatarId'), default='0000')


class Quest(UserMixin, Base):
    __tablename__ = "quests"

    questId = db.Column(db.String, primary_key=True)
    reward = db.Column(db.Integer, nullable=False)
    item = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    userId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)
    posted_at = db.Column(DateTime(timezone=True), default=datetime.now(pytz.timezone('Asia/Singapore')))

    # State of quest. 0 for active, 1 for completed, 2 for deleted
    state = db.Column(db.Integer, nullable=False, default=0)
    # Type of quest. 0 for hero, 1 for side
    type = db.Column(db.Integer, nullable=False, default=0)
    # Is a featured quest. 0 for false, 1 for true
    featured = db.Column(db.Integer, nullable=False, default=0)

    # Number of users before quest marked as completed
    totalSeekers = db.Column(db.Integer, nullable=False, default=1)


class Seek(UserMixin, Base):
    __tablename__ = "seeks"

    seekId = db.Column(db.String, primary_key=True)
    reward = db.Column(db.Integer, nullable=False)
    item = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    userId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)
    # 0 is active, 1 is completed, 2 is deleted/incomplete
    state = db.Column(db.Integer, nullable=False, default=0)
    posted_at = db.Column(DateTime(timezone=True), default=datetime.now(pytz.timezone('Asia/Singapore')))


class QuestsAccepted(UserMixin, Base):
    __tablename__ = "questsAccepted"

    questId = db.Column(db.String, ForeignKey('quests.questId'), primary_key=True)
    userId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)


class SeeksAccepted(UserMixin, Base):
    __tablename__ = "seeksAccepted"

    seekId = db.Column(db.String, ForeignKey('seeks.seekId'), primary_key=True)
    userId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)


class QuestCoinsTransaction(UserMixin, Base):
    __tablename__ = "questCoinsTransaction"

    questId = db.Column(db.String, ForeignKey('quests.questId'), primary_key=True)
    userId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)
    coins = db.Column(db.Integer, nullable=False, default=0)
    completed_at = db.Column(DateTime(timezone=True), default=datetime.now(pytz.timezone('Asia/Singapore')))


class SeekCoinsTransaction(UserMixin, Base):
    __tablename__ = "seekCoinsTransaction"

    seekId = db.Column(db.String, ForeignKey('seeks.seekId'), primary_key=True)
    userId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)
    coins = db.Column(db.Integer, nullable=False, default=0)
    completed_at = db.Column(DateTime(timezone=True), default=datetime.now(pytz.timezone('Asia/Singapore')))


class QuestComments(UserMixin, Base):
    __tablename__ = "questComments"

    commentId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)
    questId = db.Column(db.String, ForeignKey('quests.questId'), primary_key=True)
    userId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)

    description = db.Column(db.String(255), nullable=False)
    # 0 is false, # 1 is true
    is_creator = db.Column(db.Integer, nullable=False, default=0)
    posted_at = db.Column(DateTime(timezone=True), default=datetime.now(pytz.timezone('Asia/Singapore')))


class SeekComments(UserMixin, Base):
    __tablename__ = "seekComments"

    commentId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)
    seekId = db.Column(db.String, ForeignKey('quests.questId'), primary_key=True)
    userId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)

    description = db.Column(db.String(255))
    # 0 is false, # 1 is true
    is_creator = db.Column(db.Integer, nullable=False, default=0)
    posted_at = db.Column(DateTime(timezone=True), default=datetime.now(pytz.timezone('Asia/Singapore')))


class Avatars(UserMixin, Base):
    __tablename__ = "Avatars"

    avatarId = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    coinsRequired = db.Column(db.Integer, default=0)


class UserAvatars(UserMixin, Base):
    __tablename__ = "userAvatars"

    avatarId = db.Column(db.String, primary_key=True)
    userId = db.Column(db.String, ForeignKey('users.id'), primary_key=True)
