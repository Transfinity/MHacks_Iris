import os
import boto
import simplejson
import twitter
import tesseract
import cv


class OCR_Queue:
    def __init__(self, s3_bucket_name = 'mhacks_iris', sqs_queue_name = 'mhacks_iris', s3_connection = None, sqs_connection = None, twitter_connection = None, word_dictionary = None):
        self.twit_conn = twitter_connection
        self.s3_conn = s3_connection
        self.sqs_conn = sqs_connection
        self.wordlist = word_dictionary

        if self.s3_conn == None:
            self.s3_conn = boto.connect_s3()
        if self.sqs_conn == None:
            self.sqs_conn = boto.connect_sqs()

        self.bucket = self.s3_conn.get_bucket(s3_bucket_name)
        self.queue = self.sqs_conn.get_queue(sqs_queue_name)

        self.quiet = False

    def enqueue_frame(self, filename):
        #Create the key name by stripping off the path
        key_fname = os.path.basename(filename)
        #Upload the file to s3
        key = self.bucket.new_key('raw/'+key_fname)
        key.set_contents_from_filename(filename)
        key.set_acl('public-read')

        #Add the file message to the SQS queue
        message = self.queue.new_message(body=simplejson.dumps({'key': key.name}))
        self.queue.write(message)

        print '  > enqueued frame ' + key.name


    def dequeue_frame(self, dest_dir):
        #Read a message from the queue
        m = self.queue.read()
        if m == None:
            return False

        #Decode the queue message
        #returns a dict {'bucket': name, 'key': key}
        m_data = simplejson.loads(m.get_body())

        try:
            key = self.bucket.get_key(m_data['key'])

            #Construct the filename 
            local_fname = os.path.join(dest_dir, os.path.basename(key.name))
            #Download the frame from S3
            key.get_contents_to_filename(local_fname)

            #Process the frame
            self.process_frame(local_fname, key)
        finally:
            #Remove it from the queue
            #If we crashed on it once, we will
            #surely do it again...
            self.queue.delete_message(m) 

        print '  > dequeued frame ' + '/' + key.name
        return True


    def process_frame(self, filename, key):
        #Open the file
        print '  > processing \'' + filename + '\''

        #Do OCR on the file
        text = self.do_ocr(filename)
        words = text.strip().split()

        #Strip out non-words
        text = ''
        has_four_word = False
        for w in words:
            w_strip = w.strip('.,?!\'\"').lower()
            try:
                if self.get_wordlist()[w_strip]:
                    text = text + ' ' + w
                    if len(w) > 3:
                        has_four_word = True
            except KeyError:
                cnt = 0
                for c in w:
                    if (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z'):
                        cnt += 1
                if cnt > 3:
                    text = text + ' ' + w
                else:
                    print ' ignoring non-word \''+w+'\'',
        print ''

        #Ignore the frame if no text found
        if len(text) == 0 or not has_four_word:
            print '  > frame contained no discernable text'
            return

        #Tweet the contents if possible
        #otherwise generate a html file and tweet that
        print '  > found text.'
        print '  > generating tweet.'
        url = 'https://s3.amazonaws.com/' + self.bucket.name + '/' + key.name
        text = text.strip() + ' ' + url
        if len(text) < 140:
            #tweet the line
            print '  > tweeting:'
            print '  > \'' + text + '\''
        else:
            print '  > tweet too large.'

            print '  > generating html file.'
            html = '<html><body>'
            html = html + '<p>' + text.strip(url) + '</p>'
            html = html + '<img src=\"'+url+'\" alt=\"capture\">'
            html = html + '</body></html>'

            print '  > uploading html to s3'
            html_key_uqname = os.path.basename(key.name).split('.')[0]
            html_key = self.bucket.new_key('html/'+html_key_uqname+'.html')
            html_key.set_contents_from_string(html)
            html_key.set_acl('public-read')
            
            print '  > generating new url'
            text = 'Look what I just saw at #mhacks https://s3.amazonaws.com/' + self.bucket.name + '/' + html_key.name
            print '  > ' + text

        #Send the tweet!
        print '  > tweeting...'
        try:
            status = self.connect_twitter().PostUpdates(text)
        except:
            print '  > failure :-('
            return
        print '  > success!'
        return

    def do_ocr(self, fname):
        api = tesseract.TessBaseAPI()
        api.Init(".", "eng", tesseract.OEM_DEFAULT)
        api.SetVariable("tessedit_char_whitelist", "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.?!")
        api.SetPageSegMode(tesseract.PSM_AUTO)

        fp = open(fname, 'rb')
        buf = fp.read()
        fp.close()

        return tesseract.ProcessPagesBuffer(buf, len(buf), api)

    def load_twitter_credentials(self, fname):
        print '  > loading twitter credentials'
        fp = open(fname, 'r')
        c_k = fp.readline().strip()
        c_s = fp.readline().strip()
        a_k = fp.readline().strip()
        a_s = fp.readline().strip()
        fp.close()
        return (c_k, c_s, a_k, a_s)

    def connect_twitter(self):
        if self.twit_conn == None:
            print '  > connecting to twitter'
            creds = self.load_twitter_credentials(os.environ['HOME']+'/.twit.cfg')

            self.twit_conn = twitter.Api(
                    consumer_key=creds[0],
                    consumer_secret=creds[1],
                    access_token_key=creds[2],
                    access_token_secret=creds[3])

        return self.twit_conn

    def get_wordlist(self):
        if self.wordlist == None:
            print '  > loading american-english dictionary'
            fp = open('/usr/share/dict/american-english', 'r')
            self.wordlist = {}
            for line in fp:
                self.wordlist[line.strip()] = True
            fp.close()

        return self.wordlist

