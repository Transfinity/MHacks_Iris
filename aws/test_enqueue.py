import sys
from ocr_queue import OCR_Queue

q = OCR_Queue()

while True:
    print 'Input filename:',
    line = sys.stdin.readline().strip()
    if line == 'quit':
        break

    print '  > adding ' + line + ' to s3'
    q.enqueue_frame(line)
    print '  > success!'

