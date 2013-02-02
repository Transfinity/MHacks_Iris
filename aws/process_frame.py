import os
import boto
import simplejson
import twitter

cfg_fname = os.environ['HOME']+'/.twit.cfg'
fp = open(cfg_fname, 'r')
c_k = fp.readline().strip()
c_s = fp.readline().strip()
a_k = fp.readline().strip()
a_s = fp.readline().strip()
fp.close()

def process_frame(filename):
    print '  > processing \'' + filename + '\''
    fp = open(filename, "r")
    lines = fp.readlines()
    if len(lines) == 1:
        if len(lines[0]) < 140:
            #tweet the line
            print '  > tweeting contents:'
            print '  > \'' + lines[0] + '\''
            acn = connect_twitter()
            status=acn.PostUpdates(lines[0].strip())
            print status
            if status != None:
                print '  > success!'
                print status
            else:
                print '  > failure :-('
    return

def connect_twitter():
    acn = twitter.Api(
            consumer_key=c_k,
            consumer_secret=c_s,
            access_token_key=a_k,
            access_token_secret=a_s)
    
    return acn
