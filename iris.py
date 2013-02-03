#!/usr/bin/python
import cv
import math
import numpy as np
import scipy.stats as stats
import time

import queue_ops

EYE_CAM_ID = 1
FORWARD_CAM_ID = 2

# Takes array, array, (y,x)
def blit(dest, src, loc) :
    h_max = src.height + loc[0]
    w_max = src.width + loc[1]
    if h_max > dest.shape[0] or w_max > dest.shape[1] :
        print >> sys.stderr, 'Blit destination dimmensions not big enough!'
        print >> sys.stderr, 'Needed at least (%s, %s), found (%s, %s) (y, x)' \
                %(h_max, w_max, dest.shape[0], dest.shape[1])
        return
    dest[loc[0]:h_max, loc[1]:w_max] = src
    return

def mouse_handler (event, x, y, flags, eyeon) :
    if event == cv.CV_EVENT_LBUTTONDOWN :
        eyeon.click = (y,x)

def traverse(seq):
    while seq:
        print list(seq)
        traverse(seq.v_next()) # Recurse on children
        seq = seq.h_next() # Next sibling

class Line_Detector :
    def __init__ () :
        self.x_points = np.zeros(20)
        self.y_points = np.zeros(20)
        self.pp_index = 0
        self.pp_max = 20
        self.full = False
        self.last_line_time = 0
        self.min_line_time = 5

    def add_point (self, point) :
        if self.full == False :
            self.x_points[self.pp_index] = point[0]
            self.y_points[self.pp_index] = point[1]
            self.pp_index += 1

            if self.pp_index = self.pp_max :
                self.full = True
                self.pp_index = 0

            return None

        else :
            self.x_points[self.pp_index] = point[0]
            self.y_points[self.pp_index] = point[1]
            self.pp_index += 1
            self.pp_index %= self.pp_max

            correlation = stats.pearsonr(x_points, y_points)
            print 'Correlation for last second:', correlation
            if abs(correlation) > .8 :
                print 'Line read event detected!'
                currenttime = time.time()
                if currenttime - self.last_line_time > self.min_line_time :
                    print 'Firing line read event!'
                    return x_points, y_points

        return None



class Watcher :
    def __init__ (self) :
        self.frame_ct = 0
        self.screencapid = 0
        self.eyecam = cv.CaptureFromCAM(EYE_CAM_ID)
        self.forwardcam = cv.CaptureFromCAM(FORWARD_CAM_ID)
        self.font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 1, 1, 0, 1, 8)
        self.starttime = time.time()
        self.previoustime = 0

        self.pupil_window = 'Pupil Tracking'
        cv.NamedWindow(self.pupil_window, cv.CV_WINDOW_AUTOSIZE)
        self.white_window = 'White Tracking'
        cv.NamedWindow(self.white_window, cv.CV_WINDOW_AUTOSIZE)

        self.click = (-1,-1)
        cv.SetMouseCallback(self.pupil_window, mouse_handler, self)
        cv.SetMouseCallback(self.white_window, mouse_handler, self)

        # Build an inital bounding box for the eye
        sample_frame = cv.QueryFrame(self.eyecam)
        self.frame_size = cv.GetSize(sample_frame)
        upperleft = (self.frame_size[0]/4, self.frame_size[1]/4)
        lowerright = (3*self.frame_size[0]/4, 3*self.frame_size[1]/4)
        self.bounding_box = (upperleft, lowerright)
        print 'Bounding box from', upperleft, 'to', lowerright
        self.prev_bound_size = self.frame_size[0]/4
        self.center_bound_box = True

        self.line_tracker = Line_Detector()

        cv.MoveWindow(self.pupil_window, 0, 0)
        cv.MoveWindow(self.white_window, sample_frame.width + 32, 0)


    def handle_keys (self) :
        c = cv.WaitKey(2)
        char = chr(c & 0xff)
        if char == 'p' or char == 'P' :
            cv.SaveImage('screencap%03d_pupil.png' %(self.screencapid), self.pupil_frame)
            cv.SaveImage('screencap%03d_white.png' %(self.screencapid), self.white_frame)
            self.screencapid += 1

        elif char == 'c' or char == 'C' :
            print 'Toggling bound box'
            self.center_bound_box = not self.center_bound_box

        elif c != -1 :
            return False

        return True

    def build_default_bb(self) :
        upperleft = (self.frame_size[0]/4, self.frame_size[1]/4)
        lowerright = (3*self.frame_size[0]/4, 3*self.frame_size[1]/4)
        self.bounding_box = (upperleft, lowerright)

    def build_bounding_box(self, center, growth) :
        if self.center_bound_box :
            return self.build_default_bb()

        # Bounds on how big/small the box can get
        min_bb_size = 20
        max_bb_size = self.frame_size[0]/3

        if growth > 0 :
            bb_size = self.prev_bound_size * 1.05
        elif growth < 0 :
            bb_size = self.prev_bound_size * .95
        else :
            bb_size = self.prev_bound_size

        bb_size = max(min_bb_size, bb_size)
        bb_size = min(max_bb_size, bb_size)
        x = int(max(center[0] - bb_size, 0))
        y = int(max(center[1] - bb_size, 0))
        upperleft = (x, y)

        x = int(min(center[0] + bb_size, self.frame_size[0]))
        y = int(min(center[1] + bb_size, self.frame_size[1]))
        lowerright = (x, y)

        self.bounding_box = (upperleft, lowerright)


    # pip is the picture in picture, the thing around which we're building a border
    def build_border (self, pip) :
        top_border = 0
        left_border = 0
        right_border = 0
        bottom_border = 64

        border_size = (pip.height + top_border + bottom_border,
                pip.width + left_border + right_border, 3)
        border = np.zeros(border_size, np.uint8)    # Outer is a numpy array

        pip_loc = (top_border, left_border)
        blit(border, cv.GetMat(pip), pip_loc)

        return cv.fromarray(border)

    def handle_dark_pixels (self, grey_frame) :
        # TODO: optimize?
        # Track black pixels within the bounding box, and compute the average
        dark_pix = []
        avg_x = 0.0
        avg_y = 0.0
        for y in range(self.bounding_box[0][1], self.bounding_box[1][1]) :
            for x in range(self.bounding_box[0][0], self.bounding_box[1][0]) :
                if grey_frame[y, x] < 100 :
                    dark_pix.append((x, y))
                    avg_x += x
                    avg_y += y

        if len(dark_pix) == 0 :
            return (42, 42)

        avg_x = int(avg_x / len(dark_pix))
        avg_y = int(avg_y / len(dark_pix))
        center = (avg_x, avg_y)

        distances = []
        dist_pix = []
        for pix in dark_pix :
            dist = math.sqrt((center[0] - pix[0]) ** 2 + (center[1] - center[1]) ** 2)
            distances.append(dist)
            dist_pix.append((dist, pix))

        distances = np.array(distances)

        dist_std = np.std(distances)
        dist_avg = np.mean(distances)

        trimmed_pix = []
        avg_x = 0.0
        avg_y = 0.0
        for pix in dist_pix :
            if pix[0] < dist_avg + 1 * dist_std :
                trimmed_pix.append(pix[1])
                avg_x += pix[1][0]
                avg_y += pix[1][1]
        if len(trimmed_pix) == 0 :
            return (42, 42)
        avg_x = int(avg_x / len(trimmed_pix))
        avg_y = int(avg_y / len(trimmed_pix))
        trimmed_center = (avg_x, avg_y)

        # We want to stabilize at around 93%
        trim_ratio = 1.0 * len(trimmed_pix) / len(dark_pix)
        print 'Trim ratio:', trim_ratio
        if trim_ratio > .90 :
            bb_growth = 1
        elif trim_ratio < .80 :
            bb_growth = -1
        else :
            bb_growth = 0

        self.build_bounding_box(trimmed_center, bb_growth)

        return trimmed_center




    def find_pupil (self, frame, currenttime) :
        # Preprocess : greyscale, smooth, equalize, threshold
        grey_frame = cv.CreateImage(cv.GetSize(frame), 8, 1)
        cv.CvtColor(frame, grey_frame, cv.CV_BGR2GRAY)

        cv.Smooth(grey_frame, grey_frame, cv.CV_MEDIAN)
        cv.EqualizeHist(grey_frame, grey_frame)

        threshold = 20
        color = 255
        cv.Threshold(grey_frame, grey_frame, threshold, color, cv.CV_THRESH_BINARY)

        # Dilate to remove eyebrows
        element_shape = cv.CV_SHAPE_RECT
        pos=1
        element = cv.CreateStructuringElementEx(pos*2+1, pos*2+1, pos, pos, element_shape)
        cv.Dilate(grey_frame, grey_frame,element, 2)
        cv.Smooth(grey_frame, grey_frame, cv.CV_MEDIAN)

        # Track black pixels within the bounding box, and compute the average
        center = self.handle_dark_pixels(grey_frame)

        # Go to color
        pupil_frame = cv.CreateImage((frame.width, frame.height), 8, 3)
        cv.CvtColor(grey_frame, pupil_frame, cv.CV_GRAY2BGR)

        # See if we've found a line-event
        if currenttime - self.previoustime > .05 :
            result = self.line_tracker.add_point(pupil_center)
            if result is not None :
                x_points = result[0]
                y_points = result[1]
                for index in range(0, len(x_points)) :
                    point = (x_points[index], y_points[index])
                    cv.Circle(pupil_frame, point, 2, cv.CV_RGB(255, 0, 0))

                # Send image to the aws server
                filename = '%0.2f.png' %currenttime
                cv.SaveImage(filename, cv.QuerryFrame(self.forwardcam))
                queue_ops.enqueue_frame(filename)

        # Give it a border
        cv.Circle(pupil_frame, center, 4, cv.CV_RGB(255, 0, 0), cv.CV_FILLED)
        cv.Rectangle(pupil_frame, self.bounding_box[0],
                self.bounding_box[1], cv.CV_RGB(0,255,0))

        pupil_border = self.build_border(pupil_frame)
        cv.PutText(pupil_border,
                'Frame %s - %0.2f seconds - last click (%s, %s)'    \
                        %(self.frame_ct, currenttime, self.click[0], self.click[1]),
                (10, frame.height+50), self.font, 255)

        cv.ShowImage(self.pupil_window, pupil_border)
        self.pupil_frame = pupil_frame

        return center


    def find_white (self, frame, currenttime) :
        #Create images to hold filtered images
        hsv=cv.CreateImage(cv.GetSize(frame), 8, 3)
        s_plane=cv.CreateImage(cv.GetSize(frame), 8, 1) # s for saturation
        #Transform image to HSV colour space.
        cv.CvtColor(frame, hsv, cv.CV_RGB2HSV)
        cv.Split(hsv, None, s_plane, None, None)
        cv.Smooth(s_plane, s_plane, cv.CV_MEDIAN)

        # find pixels w/in a bounding box of the old center
        # threshold
        element_shape = cv.CV_SHAPE_RECT
        pos=1
        element = cv.CreateStructuringElementEx(pos*2+1, pos*2+1, pos, pos, element_shape)
        cv.Erode(s_plane, s_plane,element, 2)
        cv.Smooth(s_plane, s_plane, cv.CV_MEDIAN)


        # Do border stuff
        white_frame = cv.CreateImage((frame.width, frame.height), 8, 3)
        cv.CvtColor(s_plane, white_frame, cv.CV_GRAY2BGR)
        white_border = self.build_border(white_frame)
        cv.PutText(white_border,
                'Frame %s - %0.2f seconds - last click (%s, %s)'    \
                        %(self.frame_ct, currenttime, self.click[0], self.click[1]),
                (10, frame.height+50), self.font, 255)


        # Push to screen
        #cv.ShowImage(self.white_window, white_border)
        self.white_frame = white_frame

        return


    def repeat(self) :
        currenttime = time.time() - self.starttime
        frame = cv.QueryFrame(self.eyecam)      # frame is an iplimage
        self.frame_ct += 1

        # Find the pupil
        pupil_center = self.find_pupil(frame, currenttime)

        #self.find_white(frame, currenttime)
        cv.ShowImage(self.white_window, frame)

        self.previoustime = currenttime
        # Handle keyboard input
        return self.handle_keys()


    def run (self) :
        while self.repeat():
            pass



eyeon = Watcher()
eyeon.run()
