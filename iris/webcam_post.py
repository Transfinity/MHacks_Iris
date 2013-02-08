import cv
import sys
import time

cv.NamedWindow("w1", cv.CV_WINDOW_AUTOSIZE)
capture = cv.CaptureFromCAM(1)

def repeat():
    frame = cv.QueryFrame(capture)

    r_plane = cv.CreateImage(cv.GetSize(frame), 8, 1)
    g_plane = cv.CreateImage(cv.GetSize(frame), 8, 1)
    b_plane = cv.CreateImage(cv.GetSize(frame), 8, 1)

    cv.Split(frame, r_plane, g_plane, b_plane, None)

    frame = b_plane

    cv.ShowImage("w1", frame)
    c = cv.WaitKey(10)
    if chr(c & 0xff) == 'p' :
        cv.SaveImage('image.png', frame)
    elif c != -1 :
        sys.exit()

while True:
    repeat()
