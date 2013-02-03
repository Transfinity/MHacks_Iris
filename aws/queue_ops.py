import boto
import simplejson
from process_frame import *

bucket_name = 'mhacks_iris'
queue_name = 'frame_queue'

def enqueue_frame(filename):
    #Connect to s3 and add the file
    s3 = boto.connect_s3()
    bucket = s3.get_bucket(bucket_name)
    #create the key name by stripping off the path
    key_fname = filename.split('/')
    key_fname = key_fname[len(key_fname)-1]
    #upload the file to s3
    key = bucket.new_key('raw/'+key_fname)
    key.set_contents_from_filename(filename)
    key.set_acl('public-read')

    #Connect to sqs and add the file message
    sqs = boto.connect_sqs()
    q = sqs.get_queue(queue_name)
    message = q.new_message(body=simplejson.dumps({'bucket': bucket.name, 'key': key.name}))
    q.write(message)

#return dict {'bucket': name, 'key': key}
def dequeue_frame(dest_dir):
    #Connect to sqs
    sqs = boto.connect_sqs()
    q = sqs.get_queue(queue_name)
    m = q.read()
    if m == None:
        return False
    m_data = simplejson.loads(m.get_body())

    try:
        #Connect to s3
        s3 = boto.connect_s3()

        #Decode the queue message
        bucket = s3.get_bucket(m_data['bucket'])
        key = bucket.get_key(m_data['key'])

        #Construct the filename and download the frame from s3
        key_uqname = key.name.split('/')[1]
        local_fname = dest_dir.strip('/') + '/' + key_uqname
        key.get_contents_to_filename(local_fname)

        #Process the frame
        process_frame(local_fname, bucket, key)
    finally:
        #Remove it from the queue
        #If we crashed on it once, we will
        #surely do it again...
        q.delete_message(m) 

    return True

