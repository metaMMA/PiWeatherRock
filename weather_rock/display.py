"Displays the GUI"


def conditions_line(self, label, cond, is_temp, multiplier=None):
    y_start_position = 0.17
    line_spacing_gap = 0.065
    conditions_text_height = 0.05
    degree_symbol_height = 0.03
    degree_symbol_y_offset = 0.001
    x_start_position = 0.52
    second_column_x_start_position = 0.69
    text_color = (255, 255, 255)
    font_name = "freesans"

    if multiplier is None:
        y_start = y_start_position
    else:
        y_start = (y_start_position + line_spacing_gap * multiplier)

    conditions_font = pygame.font.SysFont(
        font_name, int(self.ymax * conditions_text_height), bold=1)

    txt = conditions_font.render(str(label), True, text_color)

    self.screen.blit(
        txt, (self.xmax * x_start_position, self.ymax * y_start))

    txt = conditions_font.render(str(cond), True, text_color)
    self.screen.blit(txt, (self.xmax * second_column_x_start_position,
                           self.ymax * y_start))

    if is_temp:
        txt_x = txt.get_size()[0]
        degree_font = pygame.font.SysFont(
            font_name, int(self.ymax * degree_symbol_height), bold=1)
        degree_txt = degree_font.render(UNICODE_DEGREE, True, text_color)
        self.screen.blit(degree_txt, (
            self.xmax * second_column_x_start_position + txt_x * 1.01,
            self.ymax * (y_start + degree_symbol_y_offset)))
        degree_letter = conditions_font.render(utils.get_temperature_letter(config.UNITS),
                                               True, text_color)
        degree_letter_x = degree_letter.get_size()[0]
        self.screen.blit(degree_letter, (
            self.xmax * second_column_x_start_position +
            txt_x + degree_letter_x * 1.01,
            self.ymax * (y_start + degree_symbol_y_offset)))


def subwindow(self, data, day, c_times):
    subwindow_centers = 0.125
    subwindows_y_start_position = 0.530
    line_spacing_gap = 0.065
    rain_percent_line_offset = 5.95
    rain_present_text_height = 0.060
    text_color = (255, 255, 255)
    font_name = "freesans"

    forecast_font = pygame.font.SysFont(
        font_name, int(self.ymax * self.subwindow_text_height), bold=1)
    rpfont = pygame.font.SysFont(
        font_name, int(self.ymax * rain_present_text_height), bold=1)

    txt = forecast_font.render(day, True, text_color)
    (txt_x, txt_y) = txt.get_size()
    self.screen.blit(txt, (self.xmax *
                           (subwindow_centers * c_times) - txt_x / 2,
                           self.ymax * (subwindows_y_start_position +
                                        line_spacing_gap * 0)))
    if hasattr(data, 'temperatureLow'):
        txt = forecast_font.render(
            str(int(round(data.temperatureLow))) +
            UNICODE_DEGREE +
            ' / ' +
            str(int(round(data.temperatureHigh))) +
            UNICODE_DEGREE + utils.get_temperature_letter(config.UNITS),
            True, text_color)
    else:
        txt = forecast_font.render(
            str(int(round(data.temperature))) +
            UNICODE_DEGREE + utils.get_temperature_letter(config.UNITS),
            True, text_color)
    (txt_x, txt_y) = txt.get_size()
    self.screen.blit(txt, (self.xmax *
                           (subwindow_centers * c_times) - txt_x / 2,
                           self.ymax * (subwindows_y_start_position +
                                        line_spacing_gap * 5)))
    # rtxt = forecast_font.render('Rain:', True, lc)
    # self.screen.blit(rtxt, (ro,self.ymax*(wy+gp*5)))
    rptxt = rpfont.render(
        str(int(round(data.precipProbability * 100))) + '%',
        True, text_color)
    (txt_x, txt_y) = rptxt.get_size()
    self.screen.blit(rptxt, (self.xmax *
                             (subwindow_centers * c_times) - txt_x / 2,
                             self.ymax * (subwindows_y_start_position +
                                          line_spacing_gap *
                                          rain_percent_line_offset)))
    icon = pygame.image.load(
        utils.icon_mapping(data.icon, self.icon_size)).convert_alpha()
    (icon_size_x, icon_size_y) = icon.get_size()
    if icon_size_y < 90:
        icon_y_offset = (90 - icon_size_y) / 2
    else:
        icon_y_offset = config.LARGE_ICON_OFFSET

    self.screen.blit(icon, (self.xmax *
                            (subwindow_centers * c_times) -
                            icon_size_x / 2,
                            self.ymax *
                            (subwindows_y_start_position +
                                line_spacing_gap
                                * 1.2) + icon_y_offset))


def summary(self):
    y_start_position = 0.444
    conditions_text_height = 0.04
    text_color = (255, 255, 255)
    font_name = "freesans"

    conditions_font = pygame.font.SysFont(
        font_name, int(self.ymax * conditions_text_height), bold=1)
    txt = conditions_font.render(self.weather.summary, True, text_color)
    txt_x = txt.get_size()[0]
    x = self.xmax * 0.27 - (txt_x * 1.02) / 2
    self.screen.blit(txt, (x, self.ymax * y_start_position))


def umbrella_info(self, umbrella_txt):
    x_start_position = 0.52
    y_start_position = 0.444
    conditions_text_height = 0.04
    text_color = (255, 255, 255)
    font_name = "freesans"

    conditions_font = pygame.font.SysFont(
        font_name, int(self.ymax * conditions_text_height), bold=1)
    txt = conditions_font.render(umbrella_txt, True, text_color)
    self.screen.blit(txt, (
        self.xmax * x_start_position,
        self.ymax * y_start_position))