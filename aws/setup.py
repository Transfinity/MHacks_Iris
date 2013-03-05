import boto
import os
import sys
import time
import ConfigParser

#
# Main
#
def main(argv):
    config = ConfigParser.RawConfigParser()
    config.read('aws.cfg')

    if prompt_user('Would you like to manage the s3 bucket?'):
        if not manage_s3(config):
            print 'Failed to set up the s3 bucket. Aborting.'
            return -1

    if prompt_user('Would you like to manage the sqs queue?'):
        if not manage_queue(config):
            print 'Failed to set up the sqs queue. Aborting.'
            return -1

    if prompt_user('Would you like to manage an ec2 instance?'):
        if not start_ec2(config):
            print 'Failed to start an ec2 instance. Aborting.'
            return -1


#
# Amazon S3 management functionality
#
def create_bucket(s3, name):
    #Keep looping until a bucket is successfully created
    bucket_created = False
    while not bucket_created:
        if name == None:
            print 'Please enter a new bucket name: ',
            name = sys.stdin.readline().strip().lower()

        #Try to create the bucket. If it fails, then prompt for a new bucket name
        try:
            s3.create_bucket(name)
            print 'Successfully created bucket \'' + name + '\''

            #Return the successfully created bucket name
            return name
        except boto.exception.S3CreateError:
            name = None

def manage_s3(config):
    section_name = 'Amazon S3'

    #Connect to Amazon S3
    s3 = boto.connect_s3()

    #Make sure the config file has a section for Amazon S3 configuration.
    if not config.has_section(section_name):
        config.add_section(section_name)

    #The currently-in-use bucket name
    cur_bucket_name = None

    #Manage the S3 bucket
    try:
        #Get the configuration's bucket name
        cfg_bucket_name = config.get(section_name, 'bucket_name')

        #If the bucket doesn't exist, ask the user if they want to create it.
        if None == s3.lookup(cfg_bucket_name):
            print 'The current configuration is set to use bucket \'' + cfg_bucket_name + '\', but it doesn\'t exist.'
            if prompt_user('Would you like to create \'' + cfg_bucket_name + '\'?'):
                cur_bucket_name = create_bucket(s3, cfg_bucket_name)
            elif prompt_user('Would you like to create a different bucket?'):
                cur_bucket_name = create_bucket(s3, None)
        #The bucket already exists. Ask the user if they want to use a different bucket
        else:
            print 'The currently active bucket is \'' + cfg_bucket_name + '\'.'
            if prompt_user('Would you like to use a different bucket?'):
                cur_bucket_name = create_bucket(s3, None)
            else:
                cur_bucket_name = cfg_bucket_name

        #Write the bucket name into the configuration file if it was changed.
        if cur_bucket_name != cfg_bucket_name:
            config.set(section_name, 'bucket_name', cur_bucket_name)
            with open('aws.cfg', 'wb') as cfgfile:
                config.write(cfgfile)

    #The bucket name wasn't present in the configuration file. Get the desired bucket name.
    except ConfigParser.NoOptionError:
        print 'The current configuration has no bucket name specified.'
        cur_bucket_name = create_bucket(s3, None)

        #Write the bucket name into the configuration file
        config.set(section_name, 'bucket_name', cur_bucket_name)
        with open('aws.cfg', 'wb') as cfgfile:
            config.write(cfgfile)

    print 'Using S3 Bucket \'' + cur_bucket_name + '\''
    return True

#
# Amazon SQS management functionality
#
def create_queue(sqs, name):
    #Keep looping until a bucket is successfully created
    queue_created = False
    while not queue_created:
        if name == None:
            print 'Please enter a new queue name: ',
            name = sys.stdin.readline().strip().lower()

        #Make sure there isn't a conflict with an existing queue. If there is then prompt for a new queue name.
        if None != sqs.lookup(name):
            print '\''+name+'\' already exists.'
            name = None
        else:
            sqs.create_queue(name)
            print 'Successfully created queue \'' + name + '\''

            #Return the successfully created bucket name
            return name

def manage_queue(config):
    section_name = 'Amazon SQS'

    #Connect to Amazon SQS
    sqs = boto.connect_sqs()

    #Make sure the config file has a section for Amazon SQS configuration.
    if not config.has_section(section_name):
        config.add_section(section_name)

    #The currently-in-use queue name
    cur_queue_name = None

    #Manage the SQS queue
    try:
        #Get the configuration's queue name
        cfg_queue_name = config.get(section_name, 'queue_name')

        #If the queue doesn't exist, ask the user if they want to create it.
        if None == sqs.lookup(cfg_queue_name):
            print 'The current configuration is set to use queue \'' + cfg_queue_name + '\', but it doesn\'t exist.'
            if prompt_user('Would you like to create \'' + cfg_queue_name + '\'?'):
                cur_queue_name = create_queue(sqs, cfg_queue_name)
            elif prompt_user('Would you like to create a different queue?'):
                cur_queue_name = create_queue(sqs, None)
        #The queue already exists. Ask the user if they want to use a different queue
        else:
            print 'The currently active queue is \'' + cfg_queue_name + '\'.'
            if prompt_user('Would you like to use a different queue?'):
                cur_queue_name = create_queue(sqs, None)
            else:
                cur_queue_name = cfg_queue_name

        #Write the bucket name into the configuration file if it was changed.
        if cur_queue_name != cfg_queue_name:
            config.set(section_name, 'queue_name', cur_queue_name)
            with open('aws.cfg', 'wb') as cfgfile:
                config.write(cfgfile)

    #The queue name wasn't present in the configuration file. Get the desired queue name.
    except ConfigParser.NoOptionError:
        print 'The current configuration has no queue name specified.'
        cur_queue_name = create_queue(sqs, None)

        #Write the queue name into the configuration file
        config.set(section_name, 'queue_name', cur_queue_name)
        with open('aws.cfg', 'wb') as cfgfile:
            config.write(cfgfile)

    print 'Using SQS Queue \'' + cur_queue_name + '\''
    return True

# 
# Amazon EC2 management functionality
#
def get_key_pair(ec2, name):
    save_dir = os.path.join(os.environ['HOME'], '.ssh/')
    key_pair = ec2.get_key_pair(name)

    #if the key-pair didn't exist. create it.
    while key_pair == None:
        print 'key-pair \''+name+'\' didn\'t exist. Attempting to create it...'
        key_pair = ec2.create_key_pair(name)
        #try to save the keypair
        try:
            key_pair.save(save_dir)
        except:
            full_name = os.path.join(save_dir, name + '.pem')
            print 'key-pair \'' + full_name + '\' already exists.'
            if prompt_user('Would you like to overwrite \'' + full_name + '\'?'):
                #Overwrite the file
                os.remove(full_name)
                key_pair.save(save_dir)
            else:
                if prompt_user('Would you like to enter a new filename?'):
                    #Read new filename
                    name = sys.stdin.readline().strip()
                else:
                    return None
    return name

def get_security_group(ec2, name):
    if name not in [sg.name for sg in ec2.get_all_security_groups()]:
        #Create the security group
        print 'Creating the security group \'' + name + '\'.'
        sg = ec2.create_security_group(name=name, description='mhacks_iris')
        sg.authorize(ip_protocol='tcp', from_port='22', to_port='22', cidr_ip='0.0.0.0/0')
    return name

def start_ec2_instance(ec2, ami, kp_name, sg_name, type):
    res = ec2.run_instances(image_id='ami-1405937d', key_name=kp_name, security_groups=[sg_name], instance_type='t1.micro')

    #Wait a bit for the instance to boot up
    print 'Waiting for the instance to start up...'
    while res.id not in [r.id for r in ec2.get_all_instances()]:
        time.sleep(1)
    dns = None
    while dns != None:
        for r in ec2.get_all_instances():
            if res.id == r.id:
                if r.instances[0].state == 'running':
                    dns = r.instances[0].public_dns_name
                    break;

def start_ec2():
    #Connect to ec2
    ec2 = boto.connect_ec2()

    #Get the key-pair
    key_pair_name = get_key_pair(ec2, 'mhacks_iris_key')
    if key_pair_name == None:
        print 'Could not establish the key-pair for the ec2 instance.'
        return False
    print 'Using key-pair \'' + key_pair_name + '\''

    #Load the security group
    security_group_name = get_security_group(ec2, 'mhacks_iris_security_group')

    #Start the ec2 instance
    start_ec2_instance(ec2, 'ami-1405937d', key_pair_name, [security_group_name], 't1.micro')

    #TODO: Allocate an elastic ip and associate it with the newly created instance
    #TODO: Set up dns to point to the elastic ip (maybe we don't need this?)

    #Start the server script on the new ec2 instance
    call('ssh -i ' + os.path.join(key_pair_save_dir, key_pair_name + '.pem') + ' ubuntu@' + dns + ' ./MHacks_Iris/aws/test_dequeue.py .')

    return True

#
# Assorted utility functionality
#
def prompt_user(prompt):
    while True:
        lne = raw_input(prompt + ' [Y/N]: ').lower()
        if lne == 'y' or lne == 'yes':
            return True
        elif lne == 'n' or lne == 'no':
            return False
        else:
            print 'please enter either [y]es or [n]o: ',

#
# Run main
#
if __name__ == '__main__':
    sys.exit(main(sys.argv))

