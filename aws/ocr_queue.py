import os
import boto
import simplejson
import twitter
import tesseract
import cv
import ConfigParser

class OCR_Queue:
    def __init__(self, s3_connection = None, sqs_connection = None, twitter_connection = None, word_dictionary = None):
        self.twit_conn = twitter_connection
        self.s3_conn = s3_connection
        self.sqs_conn = sqs_connection
        self.wordlist = word_dictionary

        #Lazily-instantiate the mysql connection so that the helmet
        #doesn't need to open a mysql connection.
        #Only the reader of the queue needs the mysql functionality.
        self.mysql = None

        #Pre-emptively connect to Amazon S3 and SQS.
        #The reader and writer both need them to operate.
        if self.s3_conn == None:
            self.s3_conn = boto.connect_s3()
        if self.sqs_conn == None:
            self.sqs_conn = boto.connect_sqs()

        #Read the AWS configuration file
        config = ConfigParser.RawConfigParser()
        config.read('aws/aws.cfg')

        #Try to connect to the AWS resources
        try:
            self.bucket = self.s3_conn.get_bucket(config.get('Amazon S3', 'bucket_name'))
            self.queue = self.sqs_conn.get_queue(config.get('Amazon SQS', 'queue_name'))

        #Handle errors
            if self.queue == None:
                raise RuntimeError('SQS Queue not found. Did you run setup.py first?')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            raise RuntimeError('Could not load the AWS configuration. Did you run setup.py first?')
        except (boto.exception.S3ResponseError, boto.exception.SQSError), err:
            raise RuntimeError(str(err) + '\nAWS resources not found. Did you run setup.py first?')

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

        self.log_to_console('  > enqueued frame ' + key.name)


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

        self.log_to_console('  > dequeued frame ' + '/' + key.name)
        return True


    def process_frame(self, filename, key):
        #Open the file
        self.log_to_console('  > processing \'' + filename + '\'')

        #Do OCR on the file
        text = self.do_ocr(filename)
        words = text.strip().split()

        #Strip out non-words
        text = ''
        has_four_word = False
        ignored_words = []
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
                    ignored_words.append(w)
        self.log_to_console(' ignored non-words: ' + ignored_words)

        #Ignore the frame if no text found
        if len(text) == 0 or not has_four_word:
            self.log_to_console('  > frame contained no discernable text')
            return

        #tweet(text)
        mysql_insert(filename, text)

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
        self.log_to_console('  > loading twitter credentials')
        fp = open(fname, 'r')
        c_k = fp.readline().strip()
        c_s = fp.readline().strip()
        a_k = fp.readline().strip()
        a_s = fp.readline().strip()
        fp.close()
        return (c_k, c_s, a_k, a_s)

    #Allow lazy-instantiation of the twitter connection
    def connect_twitter(self):
        if self.twit_conn == None:
            self.log_to_console('  > connecting to twitter')
            creds = self.load_twitter_credentials(os.environ['HOME']+'/.twit.cfg')

            self.twit_conn = twitter.Api(
                    consumer_key=creds[0],
                    consumer_secret=creds[1],
                    access_token_key=creds[2],
                    access_token_secret=creds[3])

        return self.twit_conn

    def tweet (self, text) :
        #Tweet the contents if possible
        #otherwise generate a html file and tweet that
        self.log_to_console('  > found text.')
        self.log_to_console('  > generating tweet.')
        url = 'https://s3.amazonaws.com/' + self.bucket.name + '/' + key.name
        text = text.strip() + ' ' + url
        if len(text) < 140:
            #tweet the line
            self.log_to_console('  > tweeting:')
            self.log_to_console('  > \'' + text + '\'')
        else:
            self.log_to_console('  > tweet too large.')

            self.log_to_console('  > generating html file.')
            html = '<html><body>'
            html = html + '<p>' + text.strip(url) + '</p>'
            html = html + '<img src=\"'+url+'\" alt=\"capture\">'
            html = html + '</body></html>'

            self.log_to_console('  > uploading html to s3')
            html_key_uqname = os.path.basename(key.name).split('.')[0]
            html_key = self.bucket.new_key('html/'+html_key_uqname+'.html')
            html_key.set_contents_from_string(html)
            html_key.set_acl('public-read')

            self.log_to_console('  > generating new url')
            text = 'Look what I just saw at #mhacks https://s3.amazonaws.com/' + self.bucket.name + '/' + html_key.name
            self.log_to_console('  > ' + text)

        #Send the tweet!
        self.log_to_console('  > tweeting...')
        try:
            status = self.connect_twitter().PostUpdates(text)
        except:
            self.log_to_console('  > failure :-(')
            return
        self.log_to_console('  > success!')

        return

    def get_wordlist(self):
        if self.wordlist == None:
            self.log_to_console('  > loading american-english dictionary')
            fp = open('/usr/share/dict/american-english', 'r')
            self.wordlist = {}
            for line in fp:
                self.wordlist[line.strip()] = True
            fp.close()

        return self.wordlist

    #Allow lazy-instantiation of the mysql connection
    def get_mysql_conn(self):
        if self.mysql == None:
            from mysql.mysql_mgr import MySQL_Mgr
            self.mysql = MySQL_Mgr()
        return self.mysql

    def mysql_insert (self, filename, text) :
        #Get the mysql connection
        mysql = get_mysql_conn()
        # TODO: Get date/time associated with the image, rather than right now
        now = time.localtime()
        date = "%04d:%02d:%02d" %(now.tm_year, now.tm_mon, now.tm_mday)
        tod  = "%02d:%02d:%02d" %(now.tm_hour, now.tm_min, now.tm_sec)
        mysql.add_image(filename, text, date, tod)
        mysql.commit()

    def log_to_console(self, msg):
        if not self.quiet:
            print msg

