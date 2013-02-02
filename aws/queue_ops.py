import boto
import simplejson
from process_image import *

bucket_name = 'mhacks_iris.chris-cole.net'
queue_name = 'frame_queue'

def enqueue_frame(filename):
    #Connect to s3 and add the file
    s3 = boto.connect_s3()
    bucket = s3.get_bucket(bucket_name)
    key = bucket.new_key('raw/'+filename)
    key.set_contents_from_filename(filename)
    key.set_acl('public-read')

    #Connect to sqs and add the file message
    sqs = boto.connect_sqs()
    q = sqs.get_queue(queue_name)
    message = q.new_message(body=simplejson.dumps({'bucket': bucket.name, 'key': key.name}))
    q.write(message)

#return dict {'bucket': name, 'key': key}
def dequeue_frame():
    #Connect to sqs
    sqs = boto.connect_sqs()
    q = sqs.get_queue(queue_name)
    m = q.read()
    if m == None:
        return
    m_data = simplejson.loads(m.get_body())

    #Connect to s3
    s3 = boto.connect_s3()
    bucket = s3.get_bucket(m_data['bucket'])
    key = bucket.get_key(m_data['key'])
    filename = m_data['key'].split('/')[1]
    key.get_contents_to_filename(filename)

    #Process the image
    process_frame(filename)

    #Remove it from the queue
    q.delete_message(m) 


