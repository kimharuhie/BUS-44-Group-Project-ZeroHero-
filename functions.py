"""
functions.py contains all the significant, non-route functions of the project.
Functions exported:
    extract_car_and_plane_data(), for finding the specific values of
        car and plane carbon per km,
    add_transport(), to add transport types to the database,
    points_calculator(carbon_used, distance), to generate a score for journeys,
    get_points_by_day(days, points_history, user), for retrieving user point history.
"""


"""Import statements are here"""
from models import TypesOfTransport
from models import db
from models import transport_list
from datetime import datetime
from datetime import timedelta

"""
Function to extract carbon usage of a petrol car and a long haul flight.
Inputs: None, but requires transport_list from models to function.
Outputs: car_carbon_per_km (the amount of carbon a petrol car uses per km),
         plane_long_range_carbon_per_km (the amount of carbon a long haul flight uses per km).
Exceptions: If cannot find 'Car (Petrol)' in transport_list,
            if cannot find 'Flight (Travelling Outside of Europe)' in transport_list.
"""

def extract_car_and_plane_data() -> (float, float):
    car_carbon_per_km = None
    # Scan the whole list, and set car_carbon_per_km if 'Car (Petrol)' is found.
    for i in range(len(transport_list)):
        if transport_list[i]['transport'] == 'Car (Petrol)':
            car_carbon_per_km = transport_list[i]['carbonUse']
            break
    # If car_carbon_per_km is still undefined, raise error.
    if not car_carbon_per_km:
        raise Exception('"Car (Petrol)" was not found in "transport_list".')
    # The exact same code as above, but for planes instead of cars.
    plane_long_range_carbon_per_km = None
    for i in range(len(transport_list)):
        if transport_list[i]['transport'] == 'Flight (Travelling Outside of Europe)':
            plane_long_range_carbon_per_km = transport_list[i]['carbonUse']
            break
    if not plane_long_range_carbon_per_km:
        raise Exception('"Flight (Travelling Outside of Europe)" was not found in the dictionary.')
    return car_carbon_per_km, plane_long_range_carbon_per_km


"""
Function to add transport types to the database.
Inputs: None, but requires transport_list from models to function.
Outputs: added_count (number of transport types added).
Exceptions: None.
"""

def add_transport() -> int:
    added_count = 0
    # For each transport type, check if already in the database, and add it if not.
    for i in transport_list:
        exists = TypesOfTransport.query.filter_by(transport=i['transport']).first()
        if not exists:
            new_transport = TypesOfTransport(transport=i['transport'], carbonUse=i['carbonUse'])
            db.session.add(new_transport)
            added_count+=1
            print('Adding transport')
    db.session.commit()
    print('Added transport')
    return added_count


"""
Function to turn the carbon savings into points.
Inputs: carbon_used (the total amount of carbon outputted on a journey),
        distance (the total distance of a journey).
Outputs: points (the "score" a user earns for a journey (minimum 0)).
Exceptions: None.
"""

def points_calculator(carbon_used: float, distance: float) -> int:
    carbon_used_per_km = carbon_used/distance
    # Call extract_car_and_plane_data for car and plane carbon per km.
    car_plane_data = extract_car_and_plane_data()
    car_carbon_per_km = car_plane_data[0]
    plane_long_range_carbon_per_km = car_plane_data[1]
    # By default, use car_carbon_per_km as a baseline.
    standard_max_carbon = car_carbon_per_km
    # For long journeys, use plane_long_range_carbon_per_km as a baseline.
    if distance > 1500:
        standard_max_carbon = plane_long_range_carbon_per_km
    # For medium length journeys, use a middle ground between cars and planes.
    # This ensures the overall function is continuous with respect to distance.
    elif distance > 750:
        standard_max_carbon = ((distance/750 - 1) * plane_long_range_carbon_per_km
                              + (2 - distance/750) * car_carbon_per_km)
    # Carbon used is compared to the baseline, multiplied by distance, and scaled.
    carbon_saved_per_km = standard_max_carbon - carbon_used_per_km
    carbon_saved = carbon_saved_per_km * distance
    points = int(7.5 * carbon_saved)
    return max(points, 0)


"""
Function to retrieve point scoring history from the database.
Inputs: days (the number of days the user is viewing),
        points_history (the points scored on particular days),
        user (the user viewing their own information).
Outputs: labels (the days, on the x-axis),
         values (the points, on the y-axis).
Exceptions: None.
"""

def get_points_by_day(days: int, points_history, user) -> (list, list):
    # Generate history for each day in the viewing range.
    now = datetime.now()
    start_day = now - timedelta(days=days)
    history = points_history.query.filter(
        points_history.user_id == user.id,
        points_history.date >= start_day
    ).all()

    points_by_day = {}
    for entry in history:
        # Convert day into more readable format.
        day = entry.date.strftime('%Y-%m-%d')
        # Fetch points for each day in viewing range.
        points_by_day[day] =  points_by_day.get(day, 0) + entry.points

    # Create the lists of points that the progress graph will show.
    labels = []
    values = []
    for i in range(days):
        day = (start_day + timedelta(days=i+1)).strftime('%Y-%m-%d')
        labels.append(day)
        values.append(points_by_day.get(day, 0))

    return labels, values

