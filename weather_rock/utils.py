"Utility functions used witin the main program"

import sys


def exit_gracefully(signum, frame):
    "Exit the program gracefully"
    sys.exit(0)


def deg_to_compass(degrees):
    "Convert numerical degrees into compas direction"
    val = int((degrees/22.5)+.5)
    dirs = ["N", "NNE", "NE", "ENE",
            "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW",
            "W", "WNW", "NW", "NNW"]
    return dirs[(val % 16)]


def get_abbreviation(phrase):
    """
    Create an apbreviation from a phrase by taking the first letter of
    each word, lowercasing it, and returning it.
    For example, Pi Weather Rock would be converted to pwr.
    """
    abbreviation = ''.join(item[0].lower() for item in phrase.split())
    return abbreviation


def get_temperature_letter(unit):
    "Determine what letter to place after a temperature"
    return units_decoder(unit)['temperature'].split(' ')[-1][0].upper()


def get_windspeed_abbreviation(unit):
    "Determine what abreviation should go after the wind speed"
    return get_abbreviation(units_decoder(unit)['windSpeed'])


def icon_mapping(icon, size):
    """
    https://darksky.net/dev/docs has this to say about icons:
    icon optional
    A machine-readable text summary of this data point, suitable for selecting an
    icon for display. If defined, this property will have one of the following
    values: clear-day, clear-night, rain, snow, sleet, wind, fog, cloudy,
    partly-cloudy-day, or partly-cloudy-night. (Developers should ensure that a
    sensible default is defined, as additional values, such as hail, thunderstorm,
    or tornado, may be defined in the future.)

    Based on that, this method will map the Dark Sky icon name to the name of an
    icon in this project.
    """
    if icon == 'clear-day':
        icon_path = 'icons/{}/clear.png'.format(size)
    elif icon == 'clear-night':
        icon_path = 'icons/{}/nt_clear.png'.format(size)
    elif icon == 'rain':
        icon_path = 'icons/{}/rain.png'.format(size)
    elif icon == 'snow':
        icon_path = 'icons/{}/snow.png'.format(size)
    elif icon == 'sleet':
        icon_path = 'icons/{}/sleet.png'.format(size)
    elif icon == 'wind':
        icon_path = 'icons/alt_icons/{}/wind.png'.format(size)
    elif icon == 'fog':
        icon_path = 'icons/{}/fog.png'.format(size)
    elif icon == 'cloudy':
        icon_path = 'icons/{}/cloudy.png'.format(size)
    elif icon == 'partly-cloudy-day':
        icon_path = 'icons/{}/partlycloudy.png'.format(size)
    elif icon == 'partly-cloudy-night':
        icon_path = 'icons/{}/nt_partlycloudy.png'.format(size)
    else:
        icon_path = 'icons/{}/unknown.png'.format(size)

    # print(icon_path)
    return icon_path


def seconds_to_hm(sec):
    "Convert seconds to (hours, minutes)"
    mins = sec.seconds // 60
    hrs = mins // 60
    return (hrs, mins % 60)


def units_decoder(units):
    """
    https://darksky.net/dev/docs has lists out what each
    unit is. The method below is just a codified version
    of what is on that page.
    """
    si_dict = {
        'nearestStormDistance': 'Kilometers',
        'precipIntensity': 'Millimeters per hour',
        'precipIntensityMax': 'Millimeters per hour',
        'precipAccumulation': 'Centimeters',
        'temperature': 'Degrees Celsius',
        'temperatureMin': 'Degrees Celsius',
        'temperatureMax': 'Degrees Celsius',
        'apparentTemperature': 'Degrees Celsius',
        'dewPoint': 'Degrees Celsius',
        'windSpeed': 'Meters per second',
        'windGust': 'Meters per second',
        'pressure': 'Hectopascals',
        'visibility': 'Kilometers',
    }
    ca_dict = si_dict.copy()
    ca_dict['windSpeed'] = 'Kilometers per hour'
    ca_dict['windGust'] = 'Kilometers per hour'
    uk2_dict = si_dict.copy()
    uk2_dict['nearestStormDistance'] = 'Miles'
    uk2_dict['visibility'] = 'Miles'
    uk2_dict['windSpeed'] = 'Miles per hour'
    uk2_dict['windGust'] = 'Miles per hour'
    us_dict = {
        'nearestStormDistance': 'Miles',
        'precipIntensity': 'Inches per hour',
        'precipIntensityMax': 'Inches per hour',
        'precipAccumulation': 'Inches',
        'temperature': 'Degrees Fahrenheit',
        'temperatureMin': 'Degrees Fahrenheit',
        'temperatureMax': 'Degrees Fahrenheit',
        'apparentTemperature': 'Degrees Fahrenheit',
        'dewPoint': 'Degrees Fahrenheit',
        'windSpeed': 'Miles per hour',
        'windGust': 'Miles per hour',
        'pressure': 'Millibars',
        'visibility': 'Miles',
    }
    switcher = {
        'ca': ca_dict,
        'uk2': uk2_dict,
        'us': us_dict,
        'si': si_dict,
    }
    return switcher.get(units, "Invalid unit name")
