import sys
from queue_ops import *

while True:
    print 'Input filename:',
    line = sys.stdin.readline().strip()
    if line == 'quit':
        break

    print '  > adding ' + line + ' to s3'
    enqueue_frame(line)
    print '  > success!'

