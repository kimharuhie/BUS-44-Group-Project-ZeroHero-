#Note 0: This code is only for calculating carbon costs, needs a link from main home page
#Note 4: Users should be able to store "favourite" journeys (e.g. home -> work) for quick usage
#Note 5: Should be able to recommend transport options given factors such as total distance, public transport availability, etc

#Dictonary containing information about how much carbon transport costs (per kilometre)
#Note 1: statistics taken from:
#(for walking/cycling) https://www.globe.gov/explore-science/scientists-blog/archived-posts/sciblog/index.html_p=186.html
#(for all other modes of transport) https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2022
#(could update with more reliable if wanted but that's very low priority I reckon)
#Note 2: could include more/less travel options e.g. diesel cars (include if wanted)
carbon_database = {
    "Car (Petrol)": 0.17048,
    "Car (Electric)":   0.0684,
    "Motorbike":   0.11355,
    "Flight (Domestic)": 0.24587,
    "Flight (Within Europe)": 0.15353,
    "Flight (Outside of Europe)": 0.19309,
    "Ferry (Foot passenger)": 0.01874,
    "Ferry (Car passenger)": 0.12952,
    "Bus": 0.0965,
    "Coach": 0.02733,
    "Rail": 0.03549,
    "Light rail/Tram/Tube": 0.02861,
    "Cycling": 0.00528,
    "Walking": 0.01212
}

#Calculates the amount of carbon saved, given transport modes
def carbon_calculator(journey):
    total_carbon = 0.0
    for i in journey.keys():
        total_carbon += journey[i] * carbon_database[i]
    return round(total_carbon, 3)

#Code to let the user set up a journey (called twice, once each for old and new journeys)
#Note 3: code can be rewritten once this journey setup is a dropdown menu (e.g. checking if journey mode is valid can be removed)
def journey_setup(unit_type):
    journey = {
    "Car (Petrol)": 0.0,
    "Car (Electric)":   0.0,
    "Motorbike":   0.0,
    "Flight (Domestic)": 0.0,
    "Flight (Within Europe)": 0.0,
    "Flight (Outside of Europe)": 0.0,
    "Ferry (Foot passenger)": 0.00,
    "Ferry (Car passenger)": 0.0,
    "Bus": 0.0,
    "Coach": 0.0,
    "Rail": 0.0,
    "Light rail/Tram/Tube": 0.0,
    "Cycling": 0.0,
    "Walking": 0.0
}
    while True:
        mode = input("Add a mode of transport:\n")
        if not mode in journey.keys():
            print("Error- not a recognised mode of transport.")
            continue
        while True:
            try:
                distance_by_mode = float(input("How far did you travel by this mode?\n"))
                if distance_by_mode < 0:
                    print("Error- please enter a positive number.")
                    continue
                else:
                    break
            except ValueError:
                print("Error- please enter a number.")
                continue
        if unit_type == "mi":
            distance_by_mode *= 1.609344
        journey[mode] += distance_by_mode
        while True:
            stop_adding_transport = input("Add another transport? Y/N\n")
            if stop_adding_transport == "y" or stop_adding_transport == "Y":
                break
            elif stop_adding_transport == "n" or stop_adding_transport == "N":
                return journey
            else:
                print("Error- please enter Y or N.")

#Main function and prints carbon saving results
def main():
    print("You will need to set up how you currently complete your current journey.")
    while True:
        unit_type = input("Input desired unit (mi or km):\n")
        if not (unit_type == "mi" or unit_type == "km"):
            print("Error- select a unit type.")
        else:
            break
    old_journey = journey_setup(unit_type)
    old_journey_carbon = carbon_calculator(old_journey)
    print(f"Your journey currently has a carbon cost of:\n{old_journey_carbon}kg of CO2.")
    print("Now set up how you would like to complete your new journey.")
    new_journey = journey_setup(unit_type)
    new_journey_carbon = carbon_calculator(new_journey)
    print(f"Your new journey would have a carbon cost of:\n{new_journey_carbon}kg of CO2.")
    print(f"You would save:\n{round(old_journey_carbon-new_journey_carbon, 3)}kg of CO2.")

if __name__ == "__main__":
    main()
