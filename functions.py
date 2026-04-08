from models import TypesOfTransport, db, car_carbon_per_km, plane_long_range_carbon_per_km

def addTransport(transportList):
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


def pointsCalculator(carbon_used, distance):
    carbon_used_per_km = carbon_used/distance
    standard_max_carbon = car_carbon_per_km
    if distance > 1500:
        standard_max_carbon = plane_long_range_carbon_per_km
    elif distance > 750:
        standard_max_carbon = (distance/750 - 1) * plane_long_range_carbon_per_km + (2 - distance/750) * car_carbon_per_km
    carbon_saved_per_km = standard_max_carbon - carbon_used_per_km
    carbon_saved = carbon_saved_per_km * distance
    points = int(7.5 * carbon_saved)
    return max(points, 0)


