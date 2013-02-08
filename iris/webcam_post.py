import cv
import sys
import time

cv.NamedWindow("w1", cv.CV_WINDOW_AUTOSIZE)
capture = cv.CaptureFromCAM(-1)

def repeat():
    frame = cv.QueryFrame(capture)
    cv.ShowImage("w1", frame)
    c = cv.WaitKey(10)
    if chr(c & 0xff) == 'p' :
        cv.SaveImage('image.png', frame)
    elif c != -1 :
        sys.exit()

while True:
    repeat()
