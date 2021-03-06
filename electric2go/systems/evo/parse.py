# coding=utf-8


def get_cars(system_data_dict):
    return system_data_dict.get('data', [])


def get_car_basics(car):
    return car['Id'], car['Lat'], car['Lon']


def get_car(car):
    result = {}

    vin, lat, lng = get_car_basics(car)

    result['vin'] = vin
    result['license_plate'] = car['Name']

    result['model'] = 'Toyota Prius C'

    result['lat'] = lat
    result['lng'] = lng

    result['address'] = car['Address']

    result['fuel'] = car['Fuel']

    return result
