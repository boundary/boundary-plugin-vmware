__author__ = 'goutham'

import socket
import sys

sys.path.append('./.pip')

from modules import util
from modules.vmware import VMWare

HOSTNAME = socket.gethostname()

if __name__ == "__main__":

    params = util.parse_params()

    util.sendEvent("Plugin started","Started vmware plugin","info")

    #while(True):
    for vcenter in params['items']:
        vmware = VMWare(vcenter)
        vmware.discovery()
        vmware.collect()

        #util.sendEvent("Plugin sleeping","Sleeping..","info")
        #util.sleep_interval()
        #util.sendEvent("Plugin wokeup","Wokeup..","info")
