#!/usr/bin/python
import math
import numpy as np
import scipy.stats as stats
import time

class Line_Detector :
    def __init__ (self) :
        self.pearson_threshold = 0.9
        self.min_xy_ratio = 3
        self.min_line_width = 25
        self.x_points = np.zeros(20)
        self.y_points = np.zeros(20)
        self.pp_index = 0
        self.pp_max = 20
        self.full = False
        self.last_line_time = 0
        self.min_line_time = 5
        self.last_sequence = []

    def add_point (self, point) :
        if self.full == False :
            self.x_points[self.pp_index] = point[0]
            self.y_points[self.pp_index] = point[1]
            self.pp_index += 1

            if self.pp_index == self.pp_max :
                self.full = True
                self.pp_index = 0

            return False

        else :
            self.x_points[self.pp_index] = point[0]
            self.y_points[self.pp_index] = point[1]
            self.pp_index += 1
            self.pp_index %= self.pp_max

            # We want more horizontal movement than vertical
            delta_x = abs(self.x_points.max() - self.x_points.min())
            delta_y = abs(self.y_points.max() - self.y_points.min())
            if delta_y > delta_x * self.min_xy_ratio and delta_x > self.min_line_width :
                return False

            # Make sure that the points fall in a line
            corrcoef, p_val = stats.pearsonr(self.x_points, self.y_points)
            if abs(corrcoef) > self.pearson_threshold :
                currenttime = time.time()
                if currenttime - self.last_line_time > self.min_line_time :
                    print 'Firing line read event!'
                    self.last_line_time = currenttime
                    self.last_sequence = []
                    for index in range(0, len(self.x_points)) :
                        point = (int(self.x_points[index]),
                                int(self.y_points[index]))
                        self.last_sequence.append(point)
                    return True

        return False

    def get_last_sequence (self) :
        if self.recent_event() :
            return self.last_sequence
        else :
            return []

    def recent_event (self) :
        if self.full == False :
            return False

        currenttime = time.time()
        if currenttime - self.last_line_time < 1.5 :
            return True
        else :
            return False

    def reset_timer (self) :
        self.last_line_time = time.time()

