from datetime import datetime

from flask import Flask, request, url_for, render_template, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.testing.pickleable import User
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY']='zerohero'
db = SQLAlchemy(app)

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

def addTransport():
    transportList = [
        {'transport':'Car (Petrol)', 'carbonUse': 0.17048},
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
    addedCount = 0
    for i in transportList:
        exists = TypesOfTransport.query.filter_by(transport=i['transport']).first()
        if not exists:
            newTransport = TypesOfTransport(transport=i['transport'], carbonUse=i['carbonUse'])
            db.session.add(newTransport)
            addedCount+=1
            print("Adding transport")
    db.session.commit()
    print("Added transport")
    return addedCount

with app.app_context():
    db.create_all()
    if TypesOfTransport.query.count() == 0:
        print("no transport found")
        addTransport()
        print(TypesOfTransport.query.count())


@app.route('/')
def homepage():
    if 'userID' in session:
        user = User.query.get(session['userID'])
    else:
        user = None
    return render_template('homepage.html',user=user)

@app.route('/travel', methods=['GET', 'POST'])
def travelLogging():
    if 'userID' not in session:
        flash('Please sign in to log your journey', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['userID'])

    totalCarbonUsage = None
    transportName = None
    distanceKM = None
    transportTypes = TypesOfTransport.query.all()

    if len(transportTypes) == 0:
        addTransport()
        transportTypes = TypesOfTransport.query.all()

    if request.method == 'POST':
        journeyAction = request.form.get('journeyAction')
        print(journeyAction)

        if journeyAction == 'Add':
            try:
                transportType = request.form.get('transportType')
                distance_str = request.form.get('distance')
                milesKM = request.form.get('milesKM')

                if not transportType or not distance_str:
                    flash('Fields cannot be left empty.', 'error')

                else:
                    distance = float(distance_str)

                    if milesKM == 'miles':
                        distanceKM = distance * 1.609344
                    else:
                        distanceKM = distance

                    transport = TypesOfTransport.query.get(transportType)

                    if transport:
                        totalCarbonUsage = distanceKM * transport.carbonUse
                        transportName = transport.transport

                        if 'currentJourney' not in session:
                            session['currentJourney'] = []

                        totalCarbonUsageRounded = f"{totalCarbonUsage:.3f}"

                        session['currentJourney'].append({
                            'transport': transportName,
                            'distance': distanceKM,
                            'carbonUse': totalCarbonUsage,
                            "carbonUseRounded": totalCarbonUsageRounded,
                            'date':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        session.modified = True
                        flash(f"Travel segment added: {transportName} for {distanceKM} km.")
            except Exception as e:
                flash(f'Error logging journey {str(e)}', 'error')

        elif journeyAction == 'Submit Journey':
            fullJourney = session.pop('currentJourney', [])
            if not fullJourney:
                flash('No travel added!', 'error')
            else:
                totalCarbonUsage = sum(seg['carbonUse']for seg in fullJourney)
                if 'journeys' not in session:
                    session['journeys'] = []

                session['journeys'].append({
                    'transport': transportName,
                    'distance': distanceKM,
                    'carbonUse': totalCarbonUsage,
                    'date':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                session.modified = True
                flash(f"Journey logged successfully! You used {totalCarbonUsage:.3f} kg of C02", 'success')

        elif journeyAction == "Return Home":
            return render_template('homepage.html')

    return render_template('travelLogging.html', user=user, transportTypes=transportTypes, totalCarbonUsage=totalCarbonUsage, transportName=transportName, distance=distanceKM, currentJourney=session.get('currentJourney', []))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if len(password) != 8:
            flash('Passwords must be 8 characters long.','error')
            return render_template('register.html')
        
        hashedPassword = generate_password_hash(password)

        existingUser = User.query.filter((User.username == username)|(User.email == email)).first()
        if existingUser:
            flash("Username/email already exists.", 'error')
            return render_template('register.html')
        newUser = User(username = username, email = email, password = hashedPassword)
        try:
            db.session.add(newUser)
            db.session.commit()
            flash(f'Welcome {username}. You have been successfully registered! Please login to start using ZeroHero.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'attempts' not in session:
        session['attempts'] = 0
    if request.method == 'POST':
        usernameEmail = request.form['usernameEmail']
        password = request.form['password']

        user = User.query.filter((User.username == usernameEmail)|(User.email == usernameEmail)).first()
        if session['attempts']>=5:
            flash("Too many failed attempts!",'error')
        if user and check_password_hash(user.password, password):
            session['userID'] = user.id
            session['attempts'] = 0
            return redirect(url_for('homepage'))
        else:
            session['attempts'] += 1
            flash(f"Incorrect username or password, you have {5-session['attempts']} attempts remaining.",'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('userID', None)
    session.pop('attempts', None)
    flash("You have been logged out. See you soon!")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, port=5555)
