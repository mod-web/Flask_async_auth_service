from flask_jwt_extended import get_jwt
from flask import current_app

from core.errors import UserIdException
from database.models import User


def user_description(body_json):
    current_app.logger.info('Reading JWT')
    jwt_roles = get_jwt()['roles']

    current_app.logger.info('Assessing roles')
    if 'admin' in jwt_roles or 'superUser' in jwt_roles:
        user_id = body_json.get('id')
    else:
        user_id = get_jwt()['userid']

    current_app.logger.info('Searching for user in DB')
    user = User.query.filter_by(id=user_id).first()

    if not user:
        current_app.logger.error('Invalid ID')
        raise UserIdException('invalid ID')
    else:
        return {
            'id': user.id,
            'first_name': user.first_name,
            'login': user.login,
            'roles': user.roles,
            'age_group': user.age_group,
        }