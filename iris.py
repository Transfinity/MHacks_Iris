#!/usr/bin/python
import cv
import numpy as np
import time

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

class Watcher :
    def __init__ (self) :
        self.frame_ct = 0
        self.screencapid = 0
        self.eyecam = cv.CaptureFromCAM(0)
        self.font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 1, 1, 0, 1, 8)
        self.starttime = time.time()

        self.pupil_window = 'Pupil Tracking'
        cv.NamedWindow(self.pupil_window, cv.CV_WINDOW_AUTOSIZE)
        self.white_window = 'White Tracking'
        cv.NamedWindow(self.white_window, cv.CV_WINDOW_AUTOSIZE)

        self.click = (-1,-1)
        cv.SetMouseCallback(self.pupil_window, mouse_handler, self)
        cv.SetMouseCallback(self.white_window, mouse_handler, self)

    def handle_keys (self) :
        c = cv.WaitKey(30)
        char = chr(c & 0xff)
        if char == 'p' or char == 'P' :
            cv.SaveImage('screencap%03d_pupil.png' %(self.screencapid), self.pupil_frame)
            cv.SaveImage('screencap%03d_white.png' %(self.screencapid), self.white_frame)
            self.screencapid += 1
            return True

        if c != -1 :
            return False
        else :
            return True

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

        # Give it a border
        pupil_frame = cv.CreateImage((frame.width, frame.height), 8, 3)
        cv.CvtColor(grey_frame, pupil_frame, cv.CV_GRAY2BGR)
        pupil_border = self.build_border(pupil_frame)
        cv.PutText(pupil_border,
                'Frame %s - %0.2f seconds - last click (%s, %s)'    \
                        %(self.frame_ct, currenttime, self.click[0], self.click[1]),
                (10, frame.height+50), self.font, 255)

        cv.ShowImage(self.pupil_window, pupil_border)
        self.pupil_frame = pupil_frame

        return


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
        cv.ShowImage(self.white_window, white_border)
        self.white_frame = white_frame

        return



    def repeat(self) :
        currenttime = time.time() - self.starttime
        frame = cv.QueryFrame(self.eyecam)      # frame is an iplimage
        self.frame_ct += 1

        # Find the pupil
        self.find_pupil(frame, currenttime)

        self.find_white(frame, currenttime)

        # Handle keyboard input
        return self.handle_keys()


    def run (self) :
        while self.repeat():
            pass



eyeon = Watcher()
eyeon.run()
