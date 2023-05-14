import pytest_asyncio
import pytest

from app import app
from database.db import db
from database.models import User, UserHistory

from testdata.create_users import load_test_data
from utils.helpers import DbHelper
from settings import test_settings

@pytest_asyncio.fixture(scope='session')
async def db_client():

    def _truncate_tables(models):
        for model in models:
            db.session.query(model).delete()
        db.session.commit()

    models = [UserHistory, User]

    with app.app_context():
        _truncate_tables(models)

    load_test_data()    

    yield db

    with app.app_context():
        db.session.remove()

@pytest.fixture
def db_helper(db_client):
    return DbHelper(db_client, User, app, test_settings)