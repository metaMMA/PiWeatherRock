#!/usr/bin/env python
# -*- coding: utf-8 -*-
# BEGIN LICENSE
# Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>
# Copyright (c) 2017 Gene Liverman <gene@technicalissues.us>

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# END LICENSE

""" Fetches weather reports from Dark Sky for displaying on a screen. """

__version__ = "0.0.12"

###############################################################################
#   Raspberry Pi Weather Display
#   Original By: Jim Kemp          10/25/2014
#   Modified By: Gene Liverman    12/30/2017 & multiple times since
###############################################################################
# standard imports
import datetime
import os
import platform
import signal
import sys
import syslog
import time

# third party imports
from darksky import forecast
import pygame
# from pygame.locals import *
import requests

# local imports
import config
import weather_rock.display as display
import weather_rock.draw as draw
import weather_rock.utils as utils

# globals
MODE = 'd'  # Default to weather mode.
MOUSE_X, MOUSE_Y = 0, 0
UNICODE_DEGREE = u'\xb0'


signal.signal(signal.SIGTERM, utils.exit_gracefully)


###############################################################################
class MyDisplay:
    screen = None

    ####################################################################
    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        if platform.system() == 'Darwin':
            pygame.display.init()
            driver = pygame.display.get_driver()
            print('Using the {0} driver.'.format(driver))
        else:
            # Based on "Python GUI in Linux frame buffer"
            # http://www.karoltomala.com/blog/?p=679
            disp_no = os.getenv("DISPLAY")
            if disp_no:
                print("X Display = {0}".format(disp_no))
                syslog.syslog("X Display = {0}".format(disp_no))

            # Check which frame buffer drivers are available
            # Start with fbcon since directfb hangs with composite output
            drivers = ['x11', 'fbcon', 'directfb', 'svgalib']
            found = False
            for driver in drivers:
                # Make sure that SDL_VIDEODRIVER is set
                if not os.getenv('SDL_VIDEODRIVER'):
                    os.putenv('SDL_VIDEODRIVER', driver)
                try:
                    pygame.display.init()
                except pygame.error:
                    print('Driver: {0} failed.'.format(driver))
                    syslog.syslog('Driver: {0} failed.'.format(driver))
                    continue
                found = True
                break

            if not found:
                raise Exception('No suitable video driver found!')

        size = (pygame.display.Info().current_w,
                pygame.display.Info().current_h)
        print("Framebuffer Size: %d x %d" % (size[0], size[1]))
        syslog.syslog("Framebuffer Size: %d x %d" % (size[0], size[1]))
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.mouse.set_visible(0)
        pygame.display.update()
        # Print out all available fonts
        # for fontname in pygame.font.get_fonts():
        #        print(fontname)

        if config.FULLSCREEN:
            self.xmax = pygame.display.Info().current_w - 35
            self.ymax = pygame.display.Info().current_h - 5
            if self.xmax <= 1024:
                self.icon_size = '64'
            else:
                self.icon_size = '256'
        else:
            self.xmax = 480 - 35
            self.ymax = 320 - 5
            self.icon_size = '64'
        self.subwindow_text_height = 0.055
        self.time_date_text_height = 0.115
        self.time_date_small_text_height = 0.075
        self.time_date_y_position = 8
        self.time_date_small_y_position = 18

        self.last_update_check = 0

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def get_forecast(self):
        if (time.time() - self.last_update_check) > config.DS_CHECK_INTERVAL:
            self.last_update_check = time.time()
            try:
                self.weather = forecast(config.DS_API_KEY,
                                        config.LAT,
                                        config.LON,
                                        exclude='minutely',
                                        units=config.UNITS,
                                        lang=config.LANG)

                sunset_today = datetime.datetime.fromtimestamp(
                    self.weather.daily[0].sunsetTime)
                if datetime.datetime.now() < sunset_today:
                    index = 0
                    sr_suffix = 'today'
                    ss_suffix = 'tonight'
                else:
                    index = 1
                    sr_suffix = 'tomorrow'
                    ss_suffix = 'tomorrow'

                self.sunrise = self.weather.daily[index].sunriseTime
                self.sunrise_string = datetime.datetime.fromtimestamp(
                    self.sunrise).strftime("%I:%M %p {}").format(sr_suffix)
                self.sunset = self.weather.daily[index].sunsetTime
                self.sunset_string = datetime.datetime.fromtimestamp(
                    self.sunset).strftime("%I:%M %p {}").format(ss_suffix)

                # start with saying we don't need an umbrella
                self.take_umbrella = False
                icon_now = self.weather.icon
                icon_today = self.weather.daily[0].icon
                if icon_now == 'rain' or icon_today == 'rain':
                    self.take_umbrella = True
                else:
                    # determine if an umbrella is needed during daylight hours
                    curr_date = datetime.datetime.today().date()
                    for hour in self.weather.hourly:
                        hr = datetime.datetime.fromtimestamp(hour.time)
                        sr = datetime.datetime.fromtimestamp(
                            self.weather.daily[0].sunriseTime)
                        ss = datetime.datetime.fromtimestamp(
                            self.weather.daily[0].sunsetTime)
                        rain_chance = hour.precipProbability
                        is_today = hr.date() == curr_date
                        is_daylight_hr = hr >= sr and hr <= ss
                        if is_today and is_daylight_hr and rain_chance >= .25:
                            self.take_umbrella = True
                            break

            except requests.exceptions.RequestException as e:
                print('Request exception: ' + str(e))
                return False
            except AttributeError as e:
                print('Attribute error: ' + str(e))
                return False
        return True

    def disp_weather(self):
        # Fill the screen with black
        self.screen.fill((0, 0, 0))
        xmin = 10
        lines = 5
        line_color = (255, 255, 255)
        text_color = (255, 255, 255)
        font_name = "freesans"

        draw.lines(self, line_color, xmin, lines)
        self.disp_time_date(font_name, text_color)
        self.disp_current_temp(font_name, text_color)
        display.summary(self)
        display.conditions_line(self,
                                'Feels Like:', int(
                                    round(self.weather.apparentTemperature)),
                                True)

        try:
            wind_bearing = self.weather.windBearing
            wind_direction = utils.deg_to_compass(wind_bearing) + ' @ '
        except AttributeError:
            wind_direction = ''
        wind_txt = wind_direction + str(
            int(round(self.weather.windSpeed))) + \
            ' ' + utils.get_windspeed_abbreviation(config.UNITS)
        display.conditions_line(self,
                                'Wind:', wind_txt, False, 1)

        display.conditions_line(self,
                                'Humidity:', str(
                                    int(round((self.weather.humidity * 100)))) + '%',
                                False, 2)

        # Skipping multiplier 3 (line 4)

        if self.take_umbrella:
            umbrella_txt = 'Grab your umbrella!'
        else:
            umbrella_txt = 'No umbrella needed today.'
        display.umbrella_info(self, umbrella_txt)

        # Today
        today = self.weather.daily[0]
        today_string = "Today"
        multiplier = 1
        display.subwindow(self, today, today_string, multiplier)

        # counts from 0 to 2
        for future_day in range(3):
            this_day = self.weather.daily[future_day + 1]
            this_day_no = datetime.datetime.fromtimestamp(this_day.time)
            this_day_string = this_day_no.strftime("%A")
            multiplier += 2
            display.subwindow(self, this_day, this_day_string, multiplier)

        # Update the display
        pygame.display.update()

    def disp_hourly(self):
        # Fill the screen with black
        self.screen.fill((0, 0, 0))
        xmin = 10
        lines = 5
        line_color = (255, 255, 255)
        text_color = (255, 255, 255)
        font_name = "freesans"

        draw.lines(self, line_color, xmin, lines)
        self.disp_time_date(font_name, text_color)
        self.disp_current_temp(font_name, text_color)
        display.summary(self)
        display.conditions_line(self,
                                'Feels Like:', int(
                                    round(self.weather.apparentTemperature)),
                                True)

        try:
            wind_bearing = self.weather.windBearing
            wind_direction = utils.deg_to_compass(wind_bearing) + ' @ '
        except AttributeError:
            wind_direction = ''
        wind_txt = wind_direction + str(
            int(round(self.weather.windSpeed))) + \
            ' ' + utils.get_windspeed_abbreviation(config.UNITS)
        self.display_conditions_line(
            'Wind:', wind_txt, False, 1)

        self.display_conditions_line(
            'Humidity:', str(int(round((self.weather.humidity * 100)))) + '%',
            False, 2)

        # Skipping multiplier 3 (line 4)

        if self.take_umbrella:
            umbrella_txt = 'Grab your umbrella!'
        else:
            umbrella_txt = 'No umbrella needed today.'
        display.umbrella_info(self, umbrella_txt)

        # Current hour
        this_hour = self.weather.hourly[0]
        this_hour_24_int = int(datetime.datetime.fromtimestamp(
            this_hour.time).strftime("%H"))
        if this_hour_24_int <= 11:
            ampm = 'a.m.'
        else:
            ampm = 'p.m.'
        this_hour_12_int = int(datetime.datetime.fromtimestamp(
            this_hour.time).strftime("%I"))
        this_hour_string = "{} {}".format(str(this_hour_12_int), ampm)
        multiplier = 1
        display.subwindow(self, this_hour, this_hour_string, multiplier)

        # counts from 0 to 2
        for future_hour in range(3):
            this_hour = self.weather.hourly[future_hour + 1]
            this_hour_24_int = int(datetime.datetime.fromtimestamp(
                this_hour.time).strftime("%H"))
            if this_hour_24_int <= 11:
                ampm = 'a.m.'
            else:
                ampm = 'p.m.'
            this_hour_12_int = int(datetime.datetime.fromtimestamp(
                this_hour.time).strftime("%I"))
            this_hour_string = "{} {}".format(str(this_hour_12_int), ampm)
            multiplier += 2
            display.subwindow(self, this_hour, this_hour_string, multiplier)

        # Update the display
        pygame.display.update()

    def disp_current_temp(self, font_name, text_color):
        # Outside Temp
        outside_temp_font = pygame.font.SysFont(
            font_name, int(self.ymax * (0.5 - 0.15) * 0.6), bold=1)
        txt = outside_temp_font.render(
            str(int(round(self.weather.temperature))), True, text_color)
        (txt_x, txt_y) = txt.get_size()
        degree_font = pygame.font.SysFont(
            font_name, int(self.ymax * (0.5 - 0.15) * 0.3), bold=1)
        degree_txt = degree_font.render(UNICODE_DEGREE, True, text_color)
        (rendered_am_pm_x, rendered_am_pm_y) = degree_txt.get_size()
        degree_letter = outside_temp_font.render(utils.get_temperature_letter(config.UNITS),
                                                 True, text_color)
        (degree_letter_x, degree_letter_y) = degree_letter.get_size()
        # Position text
        x = self.xmax * 0.27 - (txt_x * 1.02 + rendered_am_pm_x +
                                degree_letter_x) / 2
        self.screen.blit(txt, (x, self.ymax * 0.20))
        x = x + (txt_x * 1.02)
        self.screen.blit(degree_txt, (x, self.ymax * 0.2))
        x = x + (rendered_am_pm_x * 1.02)
        self.screen.blit(degree_letter, (x, self.ymax * 0.2))

    def disp_time_date(self, font_name, text_color):
        # Time & Date
        time_date_font = pygame.font.SysFont(
            font_name, int(self.ymax * self.time_date_text_height), bold=1)
        # Small Font for Seconds
        small_font = pygame.font.SysFont(
            font_name,
            int(self.ymax * self.time_date_small_text_height), bold=1)

        time_string = time.strftime("%a, %b %d   %I:%M", time.localtime())
        am_pm_string = time.strftime(" %p", time.localtime())

        rendered_time_string = time_date_font.render(time_string, True,
                                                     text_color)
        (rendered_time_x, rendered_time_y) = rendered_time_string.get_size()
        rendered_am_pm_string = small_font.render(am_pm_string, True,
                                                  text_color)
        (rendered_am_pm_x, rendered_am_pm_y) = rendered_am_pm_string.get_size()

        full_time_string_x_position = self.xmax / 2 - (rendered_time_x +
                                                       rendered_am_pm_x) / 2
        self.screen.blit(rendered_time_string, (full_time_string_x_position,
                                                self.time_date_y_position))
        self.screen.blit(rendered_am_pm_string,
                         (full_time_string_x_position + rendered_time_x + 3,
                          self.time_date_small_y_position))

    ####################################################################
    def sPrint(self, text, font, x, line_number, text_color):
        rendered_font = font.render(text, True, text_color)
        self.screen.blit(rendered_font, (x, self.ymax * 0.075 * line_number))

    ####################################################################
    def disp_info(self, in_daylight, day_hrs, day_mins, seconds_til_daylight,
                  delta_seconds_til_dark):
        # Fill the screen with black
        self.screen.fill((0, 0, 0))
        xmin = 10
        lines = 5
        line_color = (0, 0, 0)
        text_color = (255, 255, 255)
        font_name = "freesans"

        # Draw Screen Border
        pygame.draw.line(self.screen, line_color,
                         (xmin, 0), (self.xmax, 0), lines)
        pygame.draw.line(self.screen, line_color,
                         (xmin, 0), (xmin, self.ymax), lines)
        pygame.draw.line(self.screen, line_color,
                         (xmin, self.ymax), (self.xmax, self.ymax), lines)
        pygame.draw.line(self.screen, line_color,
                         (self.xmax, 0), (self.xmax, self.ymax), lines)
        pygame.draw.line(self.screen, line_color,
                         (xmin, self.ymax * 0.15),
                         (self.xmax, self.ymax * 0.15), lines)

        time_height_large = self.time_date_text_height
        time_height_small = self.time_date_small_text_height

        # Time & Date
        regular_font = pygame.font.SysFont(
            font_name, int(self.ymax * time_height_large), bold=1)
        small_font = pygame.font.SysFont(
            font_name, int(self.ymax * time_height_small), bold=1)

        hours_and_minites = time.strftime("%I:%M", time.localtime())
        am_pm = time.strftime(" %p", time.localtime())

        rendered_hours_and_minutes = regular_font.render(
            hours_and_minites, True, text_color)
        (tx1, ty1) = rendered_hours_and_minutes.get_size()
        rendered_am_pm = small_font.render(am_pm, True, text_color)
        (tx2, ty2) = rendered_am_pm.get_size()

        tp = self.xmax / 2 - (tx1 + tx2) / 2
        self.screen.blit(rendered_hours_and_minutes,
                         (tp, self.time_date_y_position))
        self.screen.blit(rendered_am_pm,
                         (tp + tx1 + 3, self.time_date_small_y_position))

        self.sPrint("A weather rock powered by Dark Sky", small_font,
                    self.xmax * 0.05, 3, text_color)

        self.sPrint("Sunrise: %s" % self.sunrise_string,
                    small_font, self.xmax * 0.05, 4, text_color)

        self.sPrint("Sunset:  %s" % self.sunset_string,
                    small_font, self.xmax * 0.05, 5, text_color)

        text = "Daylight: %d hrs %02d min" % (day_hrs, day_mins)
        self.sPrint(text, small_font, self.xmax * 0.05, 6, text_color)

        # leaving row 7 blank

        if in_daylight:
            text = "Sunset in %d hrs %02d min" % utils.seconds_to_hm(
                delta_seconds_til_dark)
        else:
            text = "Sunrise in %d hrs %02d min" % utils.seconds_to_hm(
                seconds_til_daylight)
        self.sPrint(text, small_font, self.xmax * 0.05, 8, text_color)

        # leaving row 9 blank

        text = "Weather checked at"
        self.sPrint(text, small_font, self.xmax * 0.05, 10, text_color)

        text = "    %s" % time.strftime(
            "%I:%M:%S %p %Z on %a. %d %b %Y ",
            time.localtime(self.last_update_check))
        self.sPrint(text, small_font, self.xmax * 0.05, 11, text_color)

        # Update the display
        pygame.display.update()

    # Save a jpg image of the screen.
    ####################################################################
    def screen_cap(self):
        pygame.image.save(self.screen, "screenshot.jpeg")
        print("Screen capture complete.")


# Given a sunrise and sunset unix timestamp,
# return true if current local time is between sunrise and sunset. In other
# words, return true if it's daytime and the sun is up. Also, return the
# number of hours:minutes of daylight in this day. Lastly, return the number
# of seconds until daybreak and sunset. If it's dark, daybreak is set to the
# number of seconds until sunrise. If it daytime, sunset is set to the number
# of seconds until the sun sets.
#
# So, five things are returned as:
#  (InDaylight, Hours, Minutes, secToSun, secToDark).
############################################################################
def daylight(weather):
    inDaylight = False    # Default return code.

    # Get current datetime with tz's local day and time.
    tNow = datetime.datetime.now()

    # Build a datetime variable from a unix timestamp for today's sunrise.
    tSunrise = datetime.datetime.fromtimestamp(weather.daily[0].sunriseTime)
    tSunset = datetime.datetime.fromtimestamp(weather.daily[0].sunsetTime)

    # Test if current time is between sunrise and sunset.
    if (tNow > tSunrise) and (tNow < tSunset):
        inDaylight = True        # We're in Daytime
        delta_seconds_til_dark = tSunset - tNow
        seconds_til_daylight = 0
    else:
        inDaylight = False        # We're in Nighttime
        delta_seconds_til_dark = 0            # Seconds until dark.
        # Delta seconds until daybreak.
        if tNow > tSunset:
            # Must be evening - compute sunrise as time left today
            # plus time from midnight tomorrow.
            sunrise_tomorrow = datetime.datetime.fromtimestamp(
                weather.daily[1].sunriseTime)
            seconds_til_daylight = sunrise_tomorrow - tNow
        else:
            # Else, must be early morning hours. Time to sunrise is
            # just the delta between sunrise and now.
            seconds_til_daylight = tSunrise - tNow

    # Compute the delta time (in seconds) between sunrise and set.
    dDaySec = tSunset - tSunrise        # timedelta in seconds
    # split into hours and minutes.
    (dayHrs, dayMin) = utils.seconds_to_hm(dDaySec)

    return (inDaylight, dayHrs, dayMin, seconds_til_daylight,
            delta_seconds_til_dark)


# Create an instance of the lcd display class.
MY_DISP = MyDisplay()

RUNNING = True             # Stay running while True
SECONDS = 0                # Seconds Placeholder to pace display.
# Display timeout to automatically switch back to weather dispaly.
NON_WEATHER_TIMEOUT = 0
# Switch to info periodically to prevent screen burn
PERIODIC_INFO_ACTIVATION = 0

# Loads data from darksky.net into class variables.
if MY_DISP.get_forecast() is False:
    print('Error: no data from darksky.net.')
    RUNNING = False


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
while RUNNING:
    # Look for and process keyboard events to change modes.
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            # On 'q' or keypad enter key, quit the program.
            if ((event.key == pygame.K_KP_ENTER) or (event.key == pygame.K_q)):
                RUNNING = False

            # On 'd' key, set mode to 'weather'.
            elif event.key == pygame.K_d:
                MODE = 'd'
                NON_WEATHER_TIMEOUT = 0
                PERIODIC_INFO_ACTIVATION = 0

            # On 's' key, save a screen shot.
            elif event.key == pygame.K_s:
                MY_DISP.screen_cap()

            # On 'i' key, set mode to 'info'.
            elif event.key == pygame.K_i:
                MODE = 'i'
                NON_WEATHER_TIMEOUT = 0
                PERIODIC_INFO_ACTIVATION = 0

            # on 'h' key, set mode to 'hourly'
            elif event.key == pygame.K_h:
                MODE = 'h'
                NON_WEATHER_TIMEOUT = 0
                PERIODIC_INFO_ACTIVATION = 0

    # Automatically switch back to weather display after a couple minutes.
    if MODE not in ('d', 'h'):
        PERIODIC_INFO_ACTIVATION = 0
        NON_WEATHER_TIMEOUT += 1
        # Five minute timeout at 100ms loop rate.
        if NON_WEATHER_TIMEOUT > 3000:
            MODE = 'd'
            syslog.syslog("Switched to weather mode")
    else:
        NON_WEATHER_TIMEOUT = 0
        PERIODIC_INFO_ACTIVATION += 1
        CURR_MIN_INT = int(datetime.datetime.now().strftime("%M"))
        # 15 minute timeout at 100ms loop rate
        if PERIODIC_INFO_ACTIVATION > 9000:
            MODE = 'i'
            syslog.syslog("Switched to info mode")
        elif PERIODIC_INFO_ACTIVATION > 600 and CURR_MIN_INT % 2 == 0:
            MODE = 'h'
        elif PERIODIC_INFO_ACTIVATION > 600:
            MODE = 'd'

    # Daily Weather Display Mode
    if MODE == 'd':
        # Update / Refresh the display after each second.
        if SECONDS != time.localtime().tm_sec:
            SECONDS = time.localtime().tm_sec
            MY_DISP.disp_weather()
            # ser.write("Weather\r\n")
        # Once the screen is updated, we have a full second to get the weather.
        # Once per minute, update the weather from the net.
        if SECONDS == 0:
            try:
                MY_DISP.get_forecast()
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                print("Decoding JSON has failed", sys.exc_info()[0])
            except BaseException:
                print("Unexpected error:", sys.exc_info()[0])
    # Hourly Weather Display Mode
    elif MODE == 'h':
        # Update / Refresh the display after each second.
        if SECONDS != time.localtime().tm_sec:
            SECONDS = time.localtime().tm_sec
            MY_DISP.disp_hourly()
        # Once the screen is updated, we have a full second to get the weather.
        # Once per minute, update the weather from the net.
        if SECONDS == 0:
            try:
                MY_DISP.get_forecast()
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                print("Decoding JSON has failed", sys.exc_info()[0])
            except BaseException:
                print("Unexpected error:", sys.exc_info()[0])
    # Info Screen Display Mode
    elif MODE == 'i':
        # Pace the screen updates to once per second.
        if SECONDS != time.localtime().tm_sec:
            SECONDS = time.localtime().tm_sec

            (inDaylight, dayHrs, dayMins, seconds_til_daylight,
             delta_seconds_til_dark) = daylight(MY_DISP.weather)

            # Extra info display.
            MY_DISP.disp_info(inDaylight, dayHrs, dayMins,
                              seconds_til_daylight,
                              delta_seconds_til_dark)
        # Refresh the weather data once per minute.
        if int(SECONDS) == 0:
            try:
                MY_DISP.get_forecast()
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                print("Decoding JSON has failed", sys.exc_info()[0])
            except BaseException:
                print("Unexpected error:", sys.exc_info()[0])

    (inDaylight, dayHrs, dayMins, seconds_til_daylight,
     delta_seconds_til_dark) = daylight(MY_DISP.weather)

    # Loop timer.
    pygame.time.wait(100)


pygame.quit()
