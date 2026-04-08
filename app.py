from datetime import datetime
from flask import Flask, request, url_for, render_template, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.testing.pickleable import User
from werkzeug.security import generate_password_hash, check_password_hash
from models import transportList, User, TypesOfTransport, app, db, car_carbon_per_km, plane_long_range_carbon_per_km
from functions import addTransport, points_calculator

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

    points = user.points
    if points <= 50:
        tree = 'seed'
    elif 50 < points <= 100:
        tree = 'sapling'
    elif 100 < points <= 200:
        tree = 'small'
    elif 200 < points <= 300:
        tree = 'medium'
    elif 300 < points:
        tree = 'large'
    else:
        tree = 'large'

    return render_template('homepage.html',user=user, tree=tree)

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
                totalDistance = sum(seg['distance']for seg in fullJourney)
                points = points_calculator(totalCarbonUsage, totalDistance)

                if 'journeys' not in session:
                    session['journeys'] = []

                session['journeys'].append({
                    'transport': transportName,
                    'distance': distanceKM,
                    'carbonUse': totalCarbonUsage,
                    'points': points,
                    'date':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                session.modified = True
                flash(f"You earned {points} points!")
                user.points += points
                print(user.points)
                db.session.commit()
                flash(f"Journey logged successfully! You used {totalCarbonUsage:.3f} kg of C02", 'success')

        elif journeyAction == "Return Home":
            return redirect(url_for('homepage'))

    return render_template('travelLogging.html', user=user, transportTypes=transportTypes, totalCarbonUsage=totalCarbonUsage, transportName=transportName, distance=distanceKM, currentJourney=session.get('currentJourney', []))

@app.route('/habit_tracking', methods=['GET', 'POST'])
def habit_tracking():
    return "\"Habit tracking\" has not yet been implemented."

@app.route('/groups_and_leaderboards', methods=['GET', 'POST'])
def groups_and_leaderboards():
    return "\"Groups and leaderboards\" has not yet been implemented."

@app.route("/information", methods=["GET", "POST"])
def information():
    return "\"Information\" has not yet been implemented."

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
