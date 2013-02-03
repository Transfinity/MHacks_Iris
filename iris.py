#!/usr/bin/python
import cv
import math
import numpy as np
import threading
import time

from optparse import OptionParser

import aws.queue_ops as qo
from line_detector import Line_Detector

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

def send_to_aws (frame, currenttime) :
    # Send image to the aws server
    filename = '%0.2f.png' %currenttime
    cv.SaveImage(filename, frame)
    qo.enqueue_frame(filename)

    print 'Thread for image', filename, 'finished.'


class Iris :
    def __init__ (self, enable_aws, enable_draw, e_cam_id, f_cam_id) :
        self.enable_aws = enable_aws
        self.enable_draw = enable_draw

        self.frame_ct = 0
        self.screencapid = 0
        self.eyecam = cv.CaptureFromCAM(e_cam_id)
        self.forwardcam = cv.CaptureFromCAM(f_cam_id)
        self.font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 1, 1, 0, 1, 8)
        self.starttime = time.time()
        self.previoustime = 0

        if self.enable_draw :
            self.eyecam_post = 'Eyecam Robovision'
            cv.NamedWindow(self.eyecam_post, cv.CV_WINDOW_AUTOSIZE)
            self.eyecam_raw = 'Eyecam Raw'
            cv.NamedWindow(self.eyecam_raw, cv.CV_WINDOW_AUTOSIZE)
            self.forward_window = 'Forward Vision'
            cv.NamedWindow(self.forward_window, cv.CV_WINDOW_AUTOSIZE)

        # Build an inital bounding box for the eye
        sample_frame = cv.QueryFrame(self.eyecam)
        self.frame_size = cv.GetSize(sample_frame)
        self.build_default_bb()

        self.line_tracker = Line_Detector()

        self.last_frame_sent = None

        if self.enable_draw :
            cv.MoveWindow(self.eyecam_post, 0, 0)
            cv.MoveWindow(self.eyecam_raw, sample_frame.width + 32, 0)
            cv.MoveWindow(self.forward_window, sample_frame.width + 32, sample_frame.height + 32)


    def handle_keys (self) :
        c = cv.WaitKey(2)
        char = chr(c & 0xff)
        if char == 'p' or char == 'P' :
            cv.SaveImage('screencap%03d_pupil.png' %(self.screencapid), self.pupil_frame)
            cv.SaveImage('screencap%03d_white.png' %(self.screencapid), self.white_frame)
            self.screencapid += 1

        elif char == 'c' or char == 'C' :
            print 'Faking a line event'
            to_send = cv.QueryFrame(self.forwardcam)
            self.last_frame_sent = to_send
            if self.enable_aws :
                aws_thread = threading.Thread(target=send_to_aws,
                        args=(to_send, time.time() - self.start_time))
                aws_thread.daemon = True
                aws_thread.start()

        elif char == 's' or char == 'S' :
            print 'Switching camera feeds'
            self.line_tracker.reset_timer()
            temp = self.eyecam
            self.eyecam = self.forwardcam
            self.forwardcam = temp

        elif c != -1 :
            return False

        return True

    def build_default_bb(self) :
        upperleft = (self.frame_size[0]/4, self.frame_size[1]/4)
        lowerright = (3*self.frame_size[0]/4, 3*self.frame_size[1]/4)
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

        return trimmed_center


    def find_pupil (self, frame, currenttime) :
        # Preprocess : greyscale, smooth, equalize, threshold
        grey_frame = cv.CreateImage(cv.GetSize(frame), 8, 1)
        cv.CvtColor(frame, grey_frame, cv.CV_BGR2GRAY)

        cv.Smooth(grey_frame, grey_frame, cv.CV_MEDIAN)
        cv.EqualizeHist(grey_frame, grey_frame)

        threshold = 30
        color = 255
        cv.Threshold(grey_frame, grey_frame, threshold, color, cv.CV_THRESH_BINARY)

        # Dilate to remove eyebrows
        element_shape = cv.CV_SHAPE_RECT
        pos = 1
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
            event_detected = self.line_tracker.add_point(center)
            if event_detected :
                print 'Detected line event at %0.2f' %currenttime
                to_send = cv.QueryFrame(self.forwardcam)
                self.last_frame_sent = to_send
                if self.enable_aws :
                    aws_thread = threading.Thread(target=send_to_aws,
                            args=(to_send, currenttime))
                    aws_thread.daemon = True
                    aws_thread.start()

        if self.enable_draw :
            # Draw robovision elements

            # Mark the sequence of points that triggered the last line event
            for point in self.line_tracker.get_last_sequence() :
                cv.Circle(pupil_frame, point, 3, cv.CV_RGB(255, 0, 255))

            # Circle the center of the pupil
            cv.Circle(pupil_frame, center, 4, cv.CV_RGB(255, 0, 0), cv.CV_FILLED)

            # Give it a border
            cv.Rectangle(pupil_frame, self.bounding_box[0],
                    self.bounding_box[1], cv.CV_RGB(0,255,0))

            pupil_border = self.build_border(pupil_frame)
            cv.PutText(pupil_border,
                    'Frame %s - %0.2f seconds' %(self.frame_ct, currenttime),
                    (10, frame.height+50), self.font, 255)

            cv.ShowImage(self.eyecam_post, pupil_border)


    def repeat(self) :
        currenttime = time.time() - self.starttime
        frame = cv.QueryFrame(self.eyecam)      # frame is an iplimage
        self.frame_ct += 1

        # Find the pupil
        self.find_pupil(frame, currenttime)

        if self.enable_draw :
            cv.Rectangle(frame, self.bounding_box[0],
                    self.bounding_box[1], cv.CV_RGB(0,255,0))
            cv.ShowImage(self.eyecam_raw, frame)

            if self.line_tracker.recent_event() and self.last_frame_sent is not None :
                fw_image = cv.CloneImage(self.last_frame_sent)
                cv.Rectangle(fw_image, (0,0), (fw_image.width, fw_image.height),
                        cv.CV_RGB(255,0,255), 4)
                cv.ShowImage(self.forward_window, fw_image)
            else :
                cv.ShowImage(self.forward_window, cv.QueryFrame(self.forwardcam))

        self.previoustime = currenttime
        # Handle keyboard input
        return self.handle_keys()


    def run (self) :
        while self.repeat():
            pass


def main () :
    parser = OptionParser()
    parser.add_option('-a', '--aws',
            action='store_false', dest='enable_aws', default=True,
            help='disable pushing caputred images to aws')
    parser.add_option('-d', '--display',
            action='store_true', dest='enable_draw', default=False,
            help='enable graphical display')
    parser.add_option('-e', '--eye_cam',
            action='store', type='int', dest='e_cam_id', default=EYE_CAM_ID,
            help='specify forward camera id (ls /dev/vid*)')
    parser.add_option('-f', '--forward_cam',
            action='store', type='int', dest='f_cam_id', default=FORWARD_CAM_ID,
            help='specify forward camera id (ls /dev/vid*)')
    (options, arguments) = parser.parse_args()

    iris = Iris(options.enable_aws, options.enable_draw, options.e_cam_id, options.f_cam_id)
    iris.run()
    for thread in threading.enumerate() :
        if thread is not threading.currentThread() :
            thread.join()

if __name__ == '__main__' :
    main()
