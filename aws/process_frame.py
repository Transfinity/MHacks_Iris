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

def process_frame(filename, bucket, key):
    #Open the file
    print '  > processing \'' + filename + '\''
    fp = open(filename, "r")

    #Do OCR on the file
    lines = fp.readlines()
    text = ''
    for l in lines:
        text = text + l
    text = text.strip()

    #Ignore the frame if no text found
    if len(text) == 0:
        print '  > frame contained no discernable text'
        return

    #Tweet the contents if possible
    #otherwise generate a html file and tweet that
    print '  > found text.'
    print '  > generating tweet.'
    url = key.generate_url(600)
    text = text.strip() + ' ' + url
    if len(text) < 140:
        #tweet the line
        print '  > tweeting:'
        print '  > \'' + text + '\''
    else:
        print '  > tweet too large.'

        print '  > generating html file.'
        html = '<html><p>' + text.strip(url) + '</p>'
        html = html + '<a href=\"'+url+'\"></html>'

        print '  > uploading html to s3'
        key = bucket.new_key('html/'+filename)
        key.set_contents_from_string(html)
        
        print '  > generating new url'
        text = key.generate_url(600)
        print '  > ' + text

    #Send the tweet!
    print '  > tweeting...'
    acn = connect_twitter()
    try:
        status=acn.PostUpdates(text)
    except:
        print '  > failure :-('
        return
    print '  > success!'
    return

def connect_twitter():
    acn = twitter.Api(
            consumer_key=c_k,
            consumer_secret=c_s,
            access_token_key=a_k,
            access_token_secret=a_s)
    
    return acn
