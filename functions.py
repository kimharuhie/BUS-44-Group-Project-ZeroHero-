from models import TypesOfTransport
from models import db
from models import transport_list
from datetime import datetime
from datetime import timedelta

def extract_car_and_plane_data():
    car_carbon_per_km = None
    plane_long_range_carbon_per_km = None
    for i in range(len(transport_list)):
        if transport_list[i]['transport'] == 'Car (Petrol)':
            car_carbon_per_km = transport_list[i]['carbonUse']
            break
    if not car_carbon_per_km:
        raise Exception('"Car (Petrol)" was not found in "transportList".')
    for i in range(len(transport_list)):
        if transport_list[i]['transport'] == 'Flight (Travelling Outside of Europe)':
            plane_long_range_carbon_per_km = transport_list[i]['carbonUse']
            break
    if not plane_long_range_carbon_per_km:
        raise Exception('"Flight (Travelling Outside of Europe)" was not found in the dictionary.')
    return car_carbon_per_km, plane_long_range_carbon_per_km


def add_transport():
    added_count = 0
    for i in transport_list:
        exists = TypesOfTransport.query.filter_by(transport=i['transport']).first()
        if not exists:
            new_transport = TypesOfTransport(transport=i['transport'], carbonUse=i['carbonUse'])
            db.session.add(new_transport)
            added_count+=1
            print("Adding transport")
    db.session.commit()
    print("Added transport")
    return added_count


def points_calculator(carbon_used, distance):
    carbon_used_per_km = carbon_used/distance
    car_plane_data = extract_car_and_plane_data()
    car_carbon_per_km = car_plane_data[0]
    plane_long_range_carbon_per_km = car_plane_data[1]
    standard_max_carbon = car_carbon_per_km
    if distance > 1500:
        standard_max_carbon = plane_long_range_carbon_per_km
    elif distance > 750:
        standard_max_carbon = (distance/750 - 1) * plane_long_range_carbon_per_km + (2 - distance/750) * car_carbon_per_km
    carbon_saved_per_km = standard_max_carbon - carbon_used_per_km
    carbon_saved = carbon_saved_per_km * distance
    points = int(7.5 * carbon_saved)
    return max(points, 0)


def get_points_by_day(days, points_history, user):
    now = datetime.now()
    start_day = now - timedelta(days=days)
    history = points_history.query.filter(
        points_history.user_id == user.id,
        points_history.date >= start_day
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
