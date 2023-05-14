import uuid
import enum

from sqlalchemy import Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
from device_detector import DeviceDetector

from datetime import datetime

from database.db import db


def create_hisotory_partitions(target, connection, **kw) -> None:
    """ creating partition by history """
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "history_smartphone" PARTITION OF "histories" FOR VALUES IN ('smartphone')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "history_desktop" PARTITION OF "histories" FOR VALUES IN ('desktop')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "history_tv" PARTITION OF "histories" FOR VALUES IN ('tv')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "history_other" PARTITION OF "histories" FOR VALUES IN ('other')"""
    )


def create_user_partitions(target, connection, **kw) -> None:
    """ creating partition by user """
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "users_age_undefined" PARTITION OF "users" FOR VALUES IN ('undefined')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "users_age_0_17" PARTITION OF "users" FOR VALUES IN ('0-17')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "users_age_18_24" PARTITION OF "users" FOR VALUES IN ('18-24')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "users_age_25_34" PARTITION OF "users" FOR VALUES IN ('25-34')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "users_age_35_44" PARTITION OF "users" FOR VALUES IN ('35-44')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "users_age_45_64" PARTITION OF "users" FOR VALUES IN ('45-64')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "users_age_65_inf" PARTITION OF "users" FOR VALUES IN ('65+')"""
    )


class User(db.Model):
    """ Model for User """
    __tablename__ = 'users'
    __table_args__ = (
        {
            'postgresql_partition_by': 'LIST (age_group)',
            'listeners': [('after_create', create_user_partitions)],
        }
    )

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True,
                   nullable=False)
    login = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    age_group = db.Column(db.Enum('undefined', '0-17', '18-24', '25-34', '35-44', '45-64', '65+', name='age_groups'), 
                          nullable=False, default='undefined')
    roles = db.Column(db.PickleType(), nullable=False)

    def __repr__(self):
        return f'<User {self.login}>'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class ActionType(enum.Enum):
    """ Action types for UserHistory """
    login = 'login'
    logout = 'logout'


class UserHistory(db.Model):
    """ Model for recording user login history """
    __tablename__ = 'histories'
    __table_args__ = (
        UniqueConstraint('id', 'user_device_type'),
        {
            'postgresql_partition_by': 'LIST (user_device_type)',
            'listeners': [('after_create', create_hisotory_partitions)],
        }
    )

    id = db.Column(UUID(as_uuid=True),
                   primary_key=True,
                   default=uuid.uuid4,
                   unique=True,
                   nullable=False)
    user_device_type = db.Column(db.Text, primary_key=True, nullable=False)
    useragent = db.Column(db.String(500), nullable=False)
    remote_addr = db.Column(db.String(500), nullable=False)
    referrer = db.Column(db.String(500), nullable=True)
    action = db.Column(Enum(ActionType))
    timestamp = db.Column(db.DateTime, default=datetime.now())
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<UserHistory {self.user_id}>'
    
    def set_device_type(self):
        device = DeviceDetector(self.useragent, skip_bot_detection=True).parse()
        device_type = device.device_type()

        if device_type in {'smartphone', 'desktop', 'tv'}:
            self.user_device_type = device_type
        else:
            self.user_device_type = 'other'