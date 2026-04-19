"""
app.py contains the bulk of the actual running code of the project.
app.py does not export any classes or functions to other modules.
"""


"""Imports go here."""
from datetime import datetime
from datetime import timedelta
from datetime import date
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
from models import transport_list
from models import TypesOfTransport
from models import app
from models import db
from models import PointsHistory
from functions import add_transport
from functions import points_calculator
from functions import get_points_by_day

"""Section of code to create the database."""
with app.app_context():
    db.create_all()
    if TypesOfTransport.query.count() == 0:
        print('No transport found')
        add_transport(transport_list)
        print(TypesOfTransport.query.count())


"""
Function for displaying the homepage.
Inputs: None.
Outputs: homepage.html (the homepage).
Exceptions: None.
"""

@app.route('/')
def homepage():
    # homepage() does NOT require a login to display (but any links from homepage will).
    # Check if user is logged in.
    if 'userID' in session:
        user = User.query.get(session['userID'])
    else:
        user = None

    # Default if user is not logged in.
    if user is None:
        return render_template('homepage.html', user=None, tree='large')

    # Decide which tree to use based on user points.
    points = user.points
    if points <= 50:
        tree = 'seed'
    elif 50 < points <= 100:
        tree = 'sapling'
    elif 100 < points <= 250:
        tree = 'small'
    elif 250 < points <= 500:
        tree = 'medium'
    else:
        tree = 'large'

    return render_template('homepage.html',user=user, tree=tree)


"""
Function to display and accept journey information.
Inputs: None.
Outputs: None explicit, but can append journeys to the database.
Exceptions: If user is not logged in,
            if user leaves transport or distance empty,
            if journey segment or total distance exceeds 150,000 km,
            if user submits journey without adding any segments,
            if user clicks "Return Home".
"""

@app.route('/travel', methods=['GET', 'POST'])
def travel_logging():
    # Check if user is logged in.
    if 'userID' not in session:
        flash('Please sign in to log your journey', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['userID'])

    # Gets today's and yesterday's date, as well as the minimum and maximum times, for carbon usage comparisons.
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    yesterday_start = datetime.combine(yesterday, datetime.min.time())
    yesterday_end = datetime.combine(yesterday, datetime.max.time())   

    total_carbon_usage = None
    transport_name = None
    distance_km = None
    transport_types = TypesOfTransport.query.all()

    # Calling add_transport if transport_types is empty.
    if len(transport_types) == 0:
        add_transport()
        transport_types = TypesOfTransport.query.all()

    if request.method == 'POST':
        # Determine user action.
        journey_action = request.form.get('journeyAction')
        print(journey_action)

        # If the user has attempted to add a segment to their journey.
        if journey_action == 'Add':
            # Try/except block for catching any errors.
            try:
                transport_type = request.form.get('transportType')
                distance_str = request.form.get('distance')
                miles_or_km = request.form.get('milesKM')

                # If user leaves a box empty, flash an error.
                if not transport_type or not distance_str:
                    flash('Fields cannot be left empty.', 'error')

                else:
                    distance = float(distance_str)

                    # Convert between miles and km, if the user input miles.
                    if miles_or_km == 'miles':
                        distance_km = distance * 1.609344
                    else:
                        distance_km = distance

                    # Puts an upper limit on distance in km to prevent any potential overflow errors.
                    if distance_km > 150000:
                        flash('Journey distance is too long.', 'error')

                    transport = TypesOfTransport.query.get(transport_type)

                    if transport:
                        total_carbon_usage = distance_km * transport.carbonUse
                        transport_name = transport.transport

                        if 'currentJourney' not in session:
                            session['currentJourney'] = []

                        # Rounding carbon usage to display to the user.
                        total_carbon_usage_rounded = f'{total_carbon_usage:.3f}'

                        # Append segment to current journey being created.
                        session['currentJourney'].append({
                            'transport': transport_name,
                            'distance': distance_km,
                            'carbonUse': total_carbon_usage,
                            "carbonUseRounded": total_carbon_usage_rounded,
                            'date':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        session.modified = True
                        flash(f'Travel segment added: {transport_name} for {distance_km} km.')
            except Exception as e:
                flash(f'Error logging journey {str(e)}', 'error')

        elif journey_action == 'Submit Journey':
            # Pop full_journey from session (so that a new one can be created).
            full_journey = session.pop('currentJourney', [])
            # Check full_journey is not empty.
            if not full_journey:
                flash('No travel added!', 'error')
            else:
                # Add carbon and distance of segments, and calculate total points.
                total_carbon_usage = sum(seg['carbonUse']for seg in full_journey)
                total_distance = sum(seg['distance']for seg in full_journey)
                points = points_calculator(total_carbon_usage, total_distance)

                # Puts an upper limit on distance in km to prevent any potential overflow errors.
                if total_distance > 150000:
                    flash('Total journey distance is too long.', 'error')
                else:
                    if 'journeys' not in session:
                        session['journeys'] = []

                    # Add journey to database and congratulate user.
                    session['journeys'].append({
                        'transport': transport_name,
                        'distance': distance_km,
                        'carbonUse': total_carbon_usage,
                        'points': points,
                        'date':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    session.modified = True
                    flash(f'You earned {points} points!')
                    user.points += points
                    new_history = PointsHistory(user_id=user.id, points=points)
                    db.session.add(new_history)
                    db.session.commit()
                    flash(f'Journey logged successfully! You used {
                    total_carbon_usage:.3f}kg of C02', 'success')

                    # Queries the PointsHistory db for today's and yesterday's carbon usage (within set limits)
                    today_journeys = PointsHistory.query.filter(
                        PointsHistory.user_id == user.id,
                        PointsHistory.date >= today_start,
                        PointsHistory.date <= today_end
                    ).all()
                    today_carbon = sum(j.carbon for j in today_journeys)

                    yesterday_journeys = PointsHistory.query.filter(
                        PointsHistory.user_id == user.id,
                        PointsHistory.date >= yesterday_start,
                        PointsHistory.date <= yesterday_end
                    ).all()
                    yesterday_carbon = sum(j.carbon for j in yesterday_journeys)

                    # If there is an entry for carbon usage yesterday, today's usage gets compared.
                    if yesterday_journeys:
                        if today_carbon < yesterday_carbon:
                            flash (f'You used {yesterday_carbon - today_carbon}kg less carbon than yesterday. Well Done!', 'success')
                        elif today_carbon > yesterday_carbon:
                            flash (f'You used {today_carbon - yesterday_carbon}kg more carbon than yesterday.', 'success')
                        else:
                            flash('You used the same amount of carbon as yesterday.')

    return render_template(
        'travelLogging.html',
        user=user,
        transportTypes=transport_types,
        totalCarbonUsage=total_carbon_usage,
        transportName=transport_name,
        distance=distance_km,
        currentJourney=session.get('currentJourney', [])
    )


"""
Function to display user point histories over the last few days.
Inputs: None.
Outputs: None explicit, but can display points earned over the last few days.
Exceptions: If user is not logged in,
            if user clicks "Return Home".
"""

@app.route('/track_progress', methods=['GET', 'POST'])
def progress_track():
    # Check if user is logged in.
    if 'userID' not in session:
        flash('Please sign in to track your progress', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['userID'])
    # Default range of days is 7 (but options for 15 and 30 exist).
    days = int(request.form.get('days', 7))
    # Call get_points_by_day to obtain how many points were scored on each day.
    labels, values = get_points_by_day(days, PointsHistory, user)
    # Print bar chart of points over last few days.
    return render_template(
        'progress.html',
        user=user,
        labels=labels,
        values=values,
        days=days
    )


"""
Function for displaying global leaderboards.
Input: None.
Output: None explicit, but can display global leaderboards.
Exceptions: If user is not logged in,
            if user clicks "Return Home".
"""

@app.route('/leaderboard', methods=['GET', 'POST'])
def leaderboard():
    # Check that user is logged in.
    if 'userID' not in session:
        flash('Please sign in to see your ranking ', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['userID'])
    all_users = User.query.order_by(User.points.desc()).all()
    # Obtain ranking of all users by points.
    user_rank = None
    for i, u in enumerate(all_users):
        if u.id == user.id:
            user_rank = i + 1
            break
    # Display leaderboards; top 10 if user is in top 10, and
    # top 3 and the 3 above and below the user if not.
    return render_template(
        'leaderboard.html',
        user=user,
        all_users=all_users,
        user_rank=user_rank)


"""
Function to display information page.
"""
@app.route("/information", methods=["GET", "POST"])
def information():
    if 'userID' not in session:
        flash('Please sign in to see your ranking ', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['userID'])

    return render_template('information.html', user=user)


"""
Function to allow a new user to register.
Inputs: None.
Outputs: None explicit, but allows a new user account to be created.
Exceptions: If password is < 8 characters,
            if password and confirm_password do not match,
            if user account already exists.
"""

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve data.
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm']
        # Check password is at least 8 characters.
        if len(password) < 8:
            flash('Passwords must be at least 8 characters long.','error')
            return render_template('register.html')
        # Check passwords match.
        if password != confirm_password:
            flash('Passwords are not identical. Please try registering again.', "error")
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        # Check user does not already exist.
        existing_user = User.query.filter((User.username == username)|(User.email == email)).first()
        if existing_user:
            flash('Username/email already exists.', 'error')
            return render_template('register.html')
        new_user = User(username=username, email=email, password=hashed_password)
        # Add user to user database and redirect to login page.
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(f'Welcome {username}. You have been successfully registered! Please login to start using ZeroHero.'
                 , 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    return render_template('register.html')


"""
Function to allow user to login.
Inputs: None.
Outputs: homepage.
Exceptions: If user fails 5 attempts.
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Reset failed attempts to 0.
    if 'attempts' not in session:
        session['attempts'] = 0
    if request.method == 'POST':
        # Fetch inputted data.
        username_email = request.form['usernameEmail']
        password = request.form['password']

        user = User.query.filter(
            (User.username == username_email)
            |(User.email == username_email)
        ).first()
        # Raise error if too many attempts.
        if session['attempts']>=5:
            flash('Too many failed attempts!','error')
        # Check username and password match.
        if user and check_password_hash(user.password, password):
            session['userID'] = user.id
            session['attempts'] = 0
            return redirect(url_for('homepage'))
        else:
            session['attempts'] += 1
            flash(f'Incorrect username or password, you have {5-session['attempts']} attempts remaining.',
                  'error')
    return render_template('login.html')


"""
Function to allow a user to logout.
Inputs: None
Outputs: None, but allows a user to logout.
Exceptions: None.
"""

@app.route('/logout')
def logout():
    # Pop user from session.
    session.pop('userID', None)
    session.pop('attempts', None)
    flash('You have been logged out. See you soon!')
    return redirect(url_for('login'))

"""Test code to run in debug mode."""
if __name__ == '__main__':
    app.run(debug=True, port=5555)
