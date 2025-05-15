from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from set_env import set_environment_variables

set_environment_variables()
app = Flask(__name__)
app.config['SECRET_KEY'] = '80fb07cee98496de2e54fe8f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///classify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

from Classify import routes
from Classify.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))