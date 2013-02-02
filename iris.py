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

        self.window_name = 'Iris'
        cv.NamedWindow(self.window_name, cv.CV_WINDOW_AUTOSIZE)

        self.click = (-1,-1)
        cv.SetMouseCallback(self.window_name, mouse_handler, self)

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


    def repeat(self) :
        frame = cv.QueryFrame(self.eyecam)      # frame is an iplimage
        self.frame_ct += 1

        # Find the pupil

        # Preprocess : greyscale, smooth, equalize, threshold
        grey_frame = cv.CreateImage((frame.width, frame.height), 8, 1)
        cv.CvtColor(frame, grey_frame, cv.CV_BGR2GRAY)

        cv.Smooth(grey_frame, grey_frame, cv.CV_MEDIAN)
        cv.EqualizeHist(grey_frame, grey_frame)

        threshold = 20
        color = 255
        cv.Threshold(grey_frame, grey_frame, threshold, color, cv.CV_THRESH_BINARY)

        #Create images to hold filtered images
        hsv=cv.CreateImage(cv.GetSize(frame), 8, 3)
        s_plane=cv.CreateImage(cv.GetSize(frame), 8, 1)
        #Transform image to HSV colour space.
        cv.CvtColor(frame, hsv, cv.CV_RGB2HSV)
        cv.Split(hsv, None, s_plane, None, None)
        cv.Smooth(s_plane, s_plane, cv.CV_MEDIAN)
        """ Doesn't seem able to pick out important bits
        threshold = 50
        color = 255
        cv.Threshold(s_plane, s_plane, threshold, color, cv.CV_THRESH_BINARY)
        """
        cv.ShowImage("s_plane", s_plane)

        final_frame = cv.CreateImage((frame.width, frame.height), 8, 3)
        cv.CvtColor(grey_frame, final_frame, cv.CV_GRAY2BGR)

        # find pixels w/in a bounding box of the old center
        # threshold


        # Do border stuff
        border = self.build_border(final_frame)
        currenttime = time.time() - self.starttime
        cv.PutText(border,
                'Frame %s - %0.2f seconds - last click (%s, %s)'    \
                        %(self.frame_ct, currenttime, self.click[0], self.click[1]),
                (10, frame.height+50), self.font, 255)

        #cv.ShowImage(self.window_name, border)
        c = cv.WaitKey(30)
        char = chr(c & 0xff)
        if char == 'p' or char == 'P' :
            cv.SaveImage('screencap%03d.png' %(self.screencapid), s_plane)
            self.screencapid += 1

        return c

    def run (self) :
        while True:
            c = self.repeat()
            if c == -1 :
                continue

            # Grab the char value of c
            c = chr(c & 0xff)
            if c == 'p' or c == 'P' or c == 'w' :
                continue
            elif c != -1 :
                print 'got code', c
                break



eyeon = Watcher()
eyeon.run()
