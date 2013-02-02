import boto
import simplejson

def process_frame(filename):
    print '  > processing \'' + filename + '\''
    fp = open(filename, "r")
    lines = fp.readlines()
    if len(lines) == 1:
        if len(lines[0]) < 140:
            #tweet the line
            print '  > tweeting contents:'
            print '  > \'' + lines[0] + '\''
    return
