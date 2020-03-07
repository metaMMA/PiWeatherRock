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
import syslog
import json
import time
import os
import glob
import math
import re

# third-part imports
import feedparser
import pygame

# local imports
import plugin_configs.rss_config as rss_config


class Rss():
    def get_rss(self, last_update_time):
        initial = False
        if last_update_time == 0:
            initial = True
            # Make sure the rss directory exists.
            os.makedirs(
                os.path.join("/home/pi/PiWeatherRock/", "rss"), exist_ok=True)

        if ((time.time() - last_update_time) > rss_config.UPDATE_FREQ):
            slot_count = rss_config.COLUMNS * rss_config.ROWS
            feed_list = rss_config.FEED_LIST
            feed_dict = {}
            try:
                for feed in feed_list:
                    feed_dict[feed] = feedparser.parse(feed)
            except:  # Find Exception
                syslog.syslog('Error accessing feed.')
                if initial:
                    return 0
                else:
                    return (round(time.time()) + 300)
            item_dict = {}
            for x in range(slot_count):
                item_dict[x] = {}

            available_items = 0
            for feed in feed_list:
                available_items += len(feed_dict[feed]['entries'])
            if available_items < slot_count:
                slot_count = available_items
            added_items = 0
            loop = -1
            while True:
                loop +=1
                for feed in feed_list:
                    try:
                        item_dict[added_items] = feed_dict[feed]['entries'][loop]['title']
                    except IndexError:
                        continue
                    added_items += 1
                    if added_items >= slot_count:
                        break
                if added_items >= slot_count:
                    break
            with open(f"/home/pi/PiWeatherRock/rss/{round(time.time())}.json", 'w') as f:
                json.dump(item_dict, f)
            return round(time.time())

        # Remove old RSS info
        rss_dir = '/home/pi/PiWeatherRock/rss/'
        file_list = glob.glob(rss_dir + "*.json")
        file_list.sort(key=os.path.getctime)
        keep = file_list[-3:]  # always keep 3 most recent files
        for fname in os.listdir(rss_dir):
            full_path = os.path.join(rss_dir, fname)
            if full_path not in keep and os.path.exists(full_path):
                os.remove(full_path)
        return last_update_time

    def disp_rss(self, last_update_time):
        # Fill the screen with black
        self.screen.fill((0, 0, 0))

        # Get stored RSS info
        list_of_files = glob.glob(
            '/home/pi/PiWeatherRock/rss/*.json')
        list_of_files.sort(key=os.path.getctime)
        if (os.stat(list_of_files[-1:][0]).st_size > 0):
            with open(list_of_files[-1:][0], 'rb') as f:
                info = json.load(f)
        else:
            with open(list_of_files[-2:][0], 'rb') as f:
                info = json.load(f)
        # Determine header type
        if not rss_config.NO_HEADER:
            if rss_config.HEADER_TYPE == 'custom':
                header = rss_config.CUSTOM_HEADER
            else:
                header = 'time-date'
        else:
            header = False

        # Draw borders and header
        font_name = "freesans"
        line_color = (255, 255, 255)
        text_color = (255, 255, 255)
        xmin = 10
        lines = 5
        if header:
            col_height = 0.75
            col_start = 0.2
            self.disp_header('freesans', (255, 255, 255), header) # change def name and tweak to accept 'time-date', other string or FALSE
            # Bottom of top box
            pygame.draw.line(self.screen, line_color, (xmin, self.ymax * 0.15),
                            (self.xmax, self.ymax * 0.15), lines)
        else:
            col_height = 0.9
            col_start = 0.05
        # Top
        pygame.draw.line(self.screen, line_color, (xmin, 0), (self.xmax, 0),
                         lines)
        # Left
        pygame.draw.line(self.screen, line_color, (xmin, 0),
                         (xmin, self.ymax), lines)
        # Bottom
        pygame.draw.line(self.screen, line_color, (xmin, self.ymax),
                         (self.xmax, self.ymax), lines)
        # Right
        pygame.draw.line(self.screen, line_color, (self.xmax, 0),
                         (self.xmax, self.ymax + 2), lines)
        slot_height = (col_height / rss_config.ROWS)
        font = pygame.font.SysFont(font_name, int(slot_height * 0.9 * self.ymax), bold=1)

        item_rendered = 0
        slot_width = 0.9 / rss_config.COLUMNS

        filled_count = 0
        filled = {}
        for col in range(rss_config.COLUMNS):
            filled[col] = {}
            for row in range(rss_config.ROWS):
                filled[col][row] = 0
        col = 0
        row = 0

        while True:#col < rss_config.COLUMNS:
#            syslog.syslog('ROW: %s, COL: %s' % (row, col))
            #while row < rss_config.ROWS:
            item_title = u'\u2022' + info[str(filled_count)]
            rendered_text = font.render(item_title, True, text_color)
            (text_x, text_y) = rendered_text.get_size()
            new_title2 = False
            if text_x > self.xmax * slot_width:
                char_space = text_x / len(item_title)
                char_limit = math.floor((self.xmax * slot_width) / char_space)
                if rss_config.WRAP_TEXT:
                    it = re.finditer(r"(?<![A-Za-z])'(?![A-Za-z])|[\"\- ]", item_title[:char_limit])
                    break_points = [m.start(0) for m in it]
                    new_title = item_title[:break_points[-1]]
                    new_title2 = item_title[break_points[-1]:]
                    if len(new_title2) > (char_limit - 2):
                        new_title2 = "  " + new_title2[:char_limit - 5] + "..."
                    else: new_title2 = "  " + new_title2[:char_limit]
                else:
                    new_title = item_title[:char_limit - 3] + "..."
                    new_title2 = False
                rendered_text = font.render(new_title, True, text_color)
            self.screen.blit(rendered_text, (int(self.xmax * (0.05 + col * slot_width)), int(self.ymax * (col_start + row * slot_height))))
            row += 1
            filled_count += 1
            if new_title2:
                rendered_text = font.render(new_title2, True, text_color)
                self.screen.blit(rendered_text, (int(self.xmax * (0.05 + col * slot_width)), int(self.ymax * (col_start + row * slot_height))))
                row += 1
                filled_count += 1
            if row >= rss_config.ROWS:
                row = 0
                col += 1
            if col == rss_config.COLUMNS:
                break

        pygame.display.update()
