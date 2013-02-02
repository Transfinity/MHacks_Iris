import sys
from queue_ops import *

while True:
    print '  > waiting to process a frame'
    dequeue_frame()
    print '  > success!'
