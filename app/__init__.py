from flask import Flask, render_template, url_for, request, redirect, Response, abort, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_mail import Mail, Message
import os
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rota.db'
app.secret_key = 'super secret keylol'
app.debug=True
db = SQLAlchemy(app)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'yourmail@email.com',#os.environ["MAIL_USERNAME"],
    "MAIL_PASSWORD":'mailpass'#os.environ["MAIL_PASSWORD"]
}
app.config.update(mail_settings)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
from app import views