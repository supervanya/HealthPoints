import os
from flask import Flask, session
from flask_script import Manager, Shell

# Configure base directory of app
basedir = os.path.abspath(os.path.dirname(__file__))


# App setup code
app = Flask(__name__)
app.debug = True

# All app.config values
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'hardtoguessstringfromsi364'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/midterm_playground" 
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True







# Setting up the VIEWS (forms and templates)
from view import *

# Setting up the CONTROLLER







# Set up Flask debug stuff
manager = Manager(app)

# Manager setup
def make_shell_context():
	return dict(app=app, db=db, User=User, Food = Food)
manager.add_command("shell", Shell(make_context=make_shell_context))







if __name__ == '__main__':
    db.create_all()
    manager.run() # NEW: run with this: python main_app.py runserver
    # Also provides more tools for debugging