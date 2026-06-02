from py_compile import main
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
class customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mk= db.Column(db.Integer, nullable=False)
with app.app_context():
    db.create_all()
@app.route('/')
def index():
    customers = customer.query.all()
    return render_template('index.html', customers=customers)
