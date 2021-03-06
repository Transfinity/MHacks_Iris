import sys
import time
from ocr_queue import OCR_Queue

def main(argv):
    if len(argv) != 2:
        print 'Input child dir for tmp files (must already exist): '
        dest_dir = sys.stdin.readline().strip()

    dest_dir = argv[1]

    q = OCR_Queue()

    #Have a linear backoff but exponential turn-on
    #for queue handling
    e_delay = 0.1

    while True:
        #print '  > waiting to process a frame'
        succ = q.dequeue_frame(dest_dir)
        if succ:
            print '  > success!'
            if e_delay > 0.001:
                e_delay = e_delay / 2.0
        else:
            #print '  > queue empty! backing off for ',
            print str(e_delay) + ' seconds'
            time.sleep(e_delay)
            if e_delay < 60.0:
                e_delay = e_delay + 0.1

if __name__ == '__main__':
    sys.exit(main(sys.argv))

