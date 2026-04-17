"""Import statements are here."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

"""app and database configuration."""
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY']='zerohero'
db = SQLAlchemy(app)

"""
Database of how much carbon in kg is used per km of travel.
The sources the statistics were taken from are listed below.
For walking/cycling:
https://www.globe.gov/explore-science/scientists-blog/archived-posts/sciblog/index.html_p=186.html
For all other modes of transport:
https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2022
"""
transport_list = [
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

class PointsHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now())
