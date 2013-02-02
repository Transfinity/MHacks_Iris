import boto

s3 = boto.connect_s3()
bucket = s3.create_bucket('mhacks_iris')
if bucket == None:
    print 'Error creating bucket'

#sqs = boto.connect_sqs()
#q = sqs.create_queue('frame_queue')
#if q == None:
#    print 'Error creating queue'

