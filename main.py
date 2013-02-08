#!/usr/bin/python
from iris.iris import Iris
from optparse import OptionParser
import threading

EYE_CAM_ID = 1
FORWARD_CAM_ID = 2

def main () :
    parser = OptionParser()
    parser.add_option('-a', '--aws',
            action='store_false', dest='enable_aws', default=True,
            help='disable pushing caputred images to aws')
    parser.add_option('-d', '--display',
            action='store_true', dest='enable_draw', default=False,
            help='enable graphical display')
    parser.add_option('-e', '--eye_cam',
            action='store', type='int', dest='e_cam_id', default=EYE_CAM_ID,
            help='specify forward camera id (ls /dev/vid*)')
    parser.add_option('-f', '--forward_cam',
            action='store', type='int', dest='f_cam_id', default=FORWARD_CAM_ID,
            help='specify forward camera id (ls /dev/vid*)')
    (options, arguments) = parser.parse_args()

    iris = Iris(options.enable_aws, options.enable_draw, options.e_cam_id, options.f_cam_id)
    iris.run()
    for thread in threading.enumerate() :
        if thread is not threading.currentThread() :
            thread.join()

if __name__ == '__main__' :
    main()
