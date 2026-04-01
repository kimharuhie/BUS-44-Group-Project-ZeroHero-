from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY']='zerohero'
db = SQLAlchemy(app)

transportList = [
        {'transport': 'Car (Petrol)', 'carbonUse': 0.17048},
        {'transport': 'Car (Electric)', 'carbonUse': 0.0684},
        {'transport': 'Motorbike', 'carbonUse': 0.11355},
        {'transport': 'Flight (Domestic)', 'carbonUse': 0.24587},
        {'transport': 'Flight (Travelling Within Europe)', 'carbonUse': 0.15353},
        {'transport': 'Flight (Travelling Outside of Europe)', 'carbonUse': 0.19309},
        {'transport': 'Ferry (Foot Passenger)', 'carbonUse': 0.01874},
        {'transport': 'Ferry (Car Passenger)', 'carbonUse': 0.12952},
        {'transport': 'Bus', 'carbonUse': 0.0965},
        {'transport': 'Coach', 'carbonUse': 0.02733},
        {'transport': 'Rail', 'carbonUse': 0.03549},
        {'transport': 'Light Rail/Tram/Tube', 'carbonUse': 0.02861},
        {'transport': 'Cycling', 'carbonUse': 0.00528},
        {'transport': 'Walking', 'carbonUse': 0.01212},
    ]
car_carbon_per_km = transportList[0]["carbonUse"]
plane_long_range_carbon_per_km = transportList[5]["carbonUse"]

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    points = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)

class TypesOfTransport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transport = db.Column(db.String(80), nullable=False)
    carbonUse = db.Column(db.Float(80), nullable=False)
