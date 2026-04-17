from datetime import datetime
from flask import request
from flask import url_for
from flask import render_template
from flask import redirect
from flask import session
from flask import flash
from sqlalchemy.testing.pickleable import User
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from models import User
from models import TypesOfTransport
from models import app
from models import db
from models import PointsHistory
from functions import add_transport
from functions import points_calculator
from functions import get_points_by_day

with app.app_context():
    db.create_all()
    if TypesOfTransport.query.count() == 0:
        print("No transport found")
        add_transport()
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
    else:
        tree = 'large'

    return render_template('homepage.html',user=user, tree=tree)

@app.route('/travel', methods=['GET', 'POST'])
def travel_logging():
    if 'userID' not in session:
        flash('Please sign in to log your journey', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['userID'])

    total_carbon_usage = None
    transport_name = None
    distance_km = None
    transport_types = TypesOfTransport.query.all()

    if len(transport_types) == 0:
        add_transport()
        transport_types = TypesOfTransport.query.all()

    if request.method == 'POST':
        journey_action = request.form.get('journeyAction')
        print(journey_action)

        if journey_action == 'Add':
            try:
                transport_type = request.form.get('transportType')
                distance_str = request.form.get('distance')
                miles_or_km = request.form.get('milesKM')

                if not transport_type or not distance_str:
                    flash('Fields cannot be left empty.', 'error')

                else:
                    distance = float(distance_str)

                    if miles_or_km == 'miles':
                        distance_km = distance * 1.609344
                    else:
                        distance_km = distance

                    transport = TypesOfTransport.query.get(transport_type)
                    if transport:
                        total_carbon_usage = distance_km * transport.carbonUse
                        transport_name = transport.transport

                        if 'currentJourney' not in session:
                            session['currentJourney'] = []

                        total_carbon_usage_rounded = f"{total_carbon_usage:.3f}"

                        session['currentJourney'].append({
                            'transport': transport_name,
                            'distance': distance_km,
                            'carbonUse': total_carbon_usage,
                            "carbonUseRounded": total_carbon_usage_rounded,
                            'date':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        session.modified = True
                        flash(f"Travel segment added: {transport_name} for {distance_km} km.")
            except Exception as e:
                flash(f'Error logging journey {str(e)}', 'error')

        elif journey_action == 'Submit Journey':
            full_journey = session.pop('currentJourney', [])
            if not full_journey:
                flash('No travel added!', 'error')
            else:
                total_carbon_usage = sum(seg['carbonUse']for seg in full_journey)
                total_distance = sum(seg['distance']for seg in full_journey)
                points = points_calculator(total_carbon_usage, total_distance)

                if 'journeys' not in session:
                    session['journeys'] = []

                session['journeys'].append({
                    'transport': transport_name,
                    'distance': distance_km,
                    'carbonUse': total_carbon_usage,
                    'points': points,
                    'date':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                session.modified = True
                flash(f"You earned {points} points!")
                user.points += points
                new_history = PointsHistory(user_id=user.id, points=points)
                db.session.add(new_history)
                db.session.commit()
                flash(f"Journey logged successfully! You used {total_carbon_usage:.3f} kg of C02", 'success')

        elif journey_action == "Return Home":
            return redirect(url_for('homepage'))

    return render_template('travelLogging.html', user=user, transportTypes=transport_types, totalCarbonUsage=total_carbon_usage, transportName=transport_name, distance=distance_km, currentJourney=session.get('currentJourney', []))

@app.route('/track_progress', methods=['GET', 'POST'])
def progress_track():
    if 'userID' not in session:
        flash('Please sign in to track your progress', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['userID'])

    days = int(request.form.get('days', 7))

    labels, values = get_points_by_day(days, PointsHistory, user)
    print("DAYS:", days)
    print("LABELS:", labels)
    print("VALUES:", values)

    return render_template('progress.html', user=user, labels=labels, values=values, days=days)

@app.route('/leaderboard', methods=['GET', 'POST'])
def leaderboard():
    if 'userID' not in session:
        flash('Please sign in to see your ranking ', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['userID'])
    all_users = User.query.order_by(User.points.desc()).all()

    user_rank = None
    for i, u in enumerate(all_users):
        if u.id == user.id:
            user_rank = i + 1
            break

    return render_template('leaderboard.html', user=user, all_users=all_users, user_rank=user_rank)

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
        
        hashed_password = generate_password_hash(password)

        existing_user = User.query.filter((User.username == username)|(User.email == email)).first()
        if existing_user:
            flash("Username/email already exists.", 'error')
            return render_template('register.html')
        new_user = User(username = username, email = email, password = hashed_password)
        try:
            db.session.add(new_user)
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
        username_email = request.form['usernameEmail']
        password = request.form['password']

        user = User.query.filter((User.username == username_email)|(User.email == username_email)).first()
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
