from datetime import datetime, timedelta, timezone
from flask import Flask, request, url_for, render_template, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.testing.pickleable import User
from werkzeug.security import generate_password_hash, check_password_hash
from models import transportList, User, TypesOfTransport, app, db, car_carbon_per_km, plane_long_range_carbon_per_km, PointsHistory
from functions import addTransport, pointsCalculator

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

    if user is None:
        return render_template('homepage.html', user=None, tree='large')
    
    points = user.points
    if points <= 500:
        tree = 'seed'
    elif 500 < points <= 1000:
        tree = 'sapling'
    elif 1000 < points <= 2500:
        tree = 'small'
    elif 2500 < points <= 5000:
        tree = 'medium'
    elif 5000 < points:
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
                points = pointsCalculator(totalCarbonUsage, totalDistance)

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
                new_history = PointsHistory(user_id=user.id, points=points)
                db.session.add(new_history)
                db.session.commit()
                flash(f"Journey logged successfully! You used {totalCarbonUsage:.3f} kg of C02", 'success')

        elif journeyAction == "Return Home":
            return redirect(url_for('homepage'))

    return render_template('travelLogging.html', user=user, transportTypes=transportTypes, totalCarbonUsage=totalCarbonUsage, transportName=transportName, distance=distanceKM, currentJourney=session.get('currentJourney', []))

@app.route('/track_progress', methods=['GET', 'POST'])
def progressTrack():
    if 'userID' not in session:
        flash('Please sign in to track your progress', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['userID'])
    now = datetime.now()

    days = int(request.form.get('days', 7))

    def getPointsByDay(days):
        start_day = now - timedelta(days=days)
        history = PointsHistory.query.filter(
            PointsHistory.user_id == user.id,
            PointsHistory.date >= start_day
        ).all()

        points_by_day = {}
        for entry in history:
            day = entry.date.strftime('%Y-%m-%d')
            points_by_day[day] =  points_by_day.get(day, 0) + entry.points

        labels = []
        values = []
        for i in range(days):
            day = (start_day + timedelta(days=i+1)).strftime('%Y-%m-%d')
            labels.append(day)
            values.append(points_by_day.get(day, 0))

        return labels, values

    labels, values = getPointsByDay(days)
    print("DAYS:", days)
    print("LABELS:", labels)
    print("VALUES:", values)

    return render_template('progress.html', user=user, labels=labels, values=values, days=days)

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
        confirm_password = request.form['confirm']
        if len(password) < 8:
            flash('Passwords must be at least 8 characters long.','error')
            return render_template('register.html')
        if password != confirm_password:
            flash("Passwords are not identical. Please try registering again.", "error")
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
            flash(f"Error creating user: {str(e)}", "error")
    return render_template("register.html")


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
