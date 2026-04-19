"""
models.py contains all the major classes in the project, as well as the transport_type dictionary.
Classes exported:
    User() for all the users,
    TypesOfTransport() for all the types of transport and their carbon emissions,
    PointsHistory for the points history of users.
Lists exported:
    transport_list for all the transports and their carbon usage per km.
"""


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


"""
User class for users.
id: Unique identifier.
username: Public display of user.
email: Email attached to user.
password: Secure phrase a user need to log in.
points: The number of points a user has accumulated in total.
streak: The number of consecutive days a user has logged in for.
"""

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    points = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)


"""
Class for all types of transport and their carbon usage.
id: Unique identifier.
transport: The name of the type of transport (e.g. Car (Petrol)).
carbon_use: The amount of carbon used per km of that type of transport.
"""

class TypesOfTransport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transport = db.Column(db.String(80), nullable=False)
    carbonUse = db.Column(db.Float(80), nullable=False)


"""
Class for displaying what points the user earned and when.
id: Unique identifier.
user_id: Foreign key from User(), the unique identifier of the user.
points: The number of points earned on a particular date.
carbon: The carbon usage (in kg) for the specified date.
date: The date the points were added.
"""

class PointsHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    carbon = db.Column(db.Float, nullable = False, default = 0)
    date = db.Column(db.DateTime, default=lambda: datetime.now())

