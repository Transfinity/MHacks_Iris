import boto
import os
import sys
import time

def main(argv):
    if prompt_user('Would you like to set up the s3 bucket?'):
        if not create_bucket():
            print 'Failed to set up the s3 bucket. Aborting.'
            return -1

    if prompt_user('Would you like to set up the sqs queue?'):
        if not create_queue():
            print 'Failed to set up the sqs queue. Aborting.'
            return -1

    if prompt_user('Would you like to set up an ec2 instance?'):
        if not start_ec2():
            print 'Failed to start an ec2 instance. Aborting.'
            return -1


def create_bucket():
    s3 = boto.connect_s3()

    bucket_name = 'mhacks_iris'
    b = s3.lookup(bucket_name)
    if b == None:
        s3.create_bucket(bucket_name)

    return True

def create_queue():
    sqs = boto.connect_sqs()

    queue_name = 'mhacks_iris'
    q = sqs.get_queue(queue_name)
    if q == None:
        sqs.create_queue(queue_name)

    return True

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
    if security_group_name not in [sg.name for sg in ec2.get_all_security_groups()]:
        #Create the security group
        print 'Creating the security group \'' + name + '\'.'
        sg = ec2.create_security_group(name=security_group_name, description='mhacks_iris')
        sg.authorize(ip_protocol='tcp', from_port='22', to_port='22', cidr_ip='0.0.0.0/0')
    return name

def start_ec2_instance(ec2, ami, kp_name, sg_name, type):
    res = ec2.run_instances(image_id='ami-1405937d', key_name=key_pair_name, security_groups=[security_group_name], instance_type='t1.micro')

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

def prompt_user(prompt):
    while True:
        print prompt + ' [Y/N]'
        lne = sys.stdin.readline().strip().lower()
        if lne == 'y' or lne == 'yes':
            return True
        elif lne == 'n' or lne == 'no':
            return False
        else:
            print 'please enter either [y]es or [n]o'

if __name__ == '__main__':
    sys.exit(main(sys.argv))

