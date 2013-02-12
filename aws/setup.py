import boto
import os
import sys
import time

def main(argv):
    #Connect to ec2
    ec2 = boto.connect_ec2()

    #Load the key-pair
    key_pair_name = 'mhacks_iris_key'
    key_pair_save_dir = os.path.join(os.environ['HOME'], '.ssh/')
    key_pair = ec2.get_key_pair(key_pair_name)

    #if the key-pair didn't exist. create it.
    while key_pair == None:
        print 'key-pair \''+key_pair_name+'\' didn\'t exist. Attempting to create it...'
        key_pair = ec2.create_key_pair(key_pair_name)
        #try to save the keypair
        try:
            key_pair.save(key_pair_save_dir)
        except:
            key_pair_full_name = os.path.join(key_pair_save_dir, key_pair_name + '.pem')
            print 'key-pair \'' + key_pair_full_name + '\' already exists.'
            if prompt_user('Would you like to overwrite \'' + key_pair_full_name + '\'?'):
                #Overwrite the file
                os.remove(key_pair_full_name)
                key_pair.save(key_pair_save_dir)
            else:
                if prompt_user('Would you like to enter a new filename?'):
                    #Read new filename
                    key_pair_name = sys.stdin.readline().strip()
                else:
                    print 'Could not establish the key-pair for the ec2 instance. Aborting.'
                    return

    print 'Using key-pair \'' + key_pair_name + '\''

    #Load the security group
    security_group_name = 'mhacks_iris_security_group'
    if security_group_name not in [sg.name for sg in ec2.get_all_security_groups()]:
        #Create the security group
        print 'Creating the security group.'
        sg = ec2.create_security_group(name=security_group_name, description='mhacks_iris')
        sg.authorize(ip_protocol='tcp', from_port='22', to_port='22', cidr_ip='0.0.0.0/0')

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

    #Print out the command to ssh into the machine.
    print 'ssh -i ' + os.path.join(key_pair_save_dir, key_pair_name + '.pem') + ' ubuntu@' + dns


    #TODO: Allocate an elastic ip and associate it with the newly created instance
    #TODO: Set up dns to point to the elastic ip
    #TODO: Set up the bucket
    #TODO: Set up the queue
    #TODO: Start the listener on the instance

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

