__author__ = 'goutham'

import socket
import time
import sys

from modules import util
from modules.vmware import VMWare

HOSTNAME = socket.gethostname()

if __name__ == "__main__":
    # now = datetime.datetime.now()
    # util.report_metric("name", "value", source=HOSTNAME, timestamp=now)
    sys.path.append('./.pip')

    vmware = VMWare()
    vmware.discovery()

    params = util.parse_params()

    util.sendEvent("Plugin started","Started vmware plugin","info")

    while(True):
        for vcenter in params['items']:
            vmware.collect(vcenter['host'])

        #util.sendEvent("Plugin sleeping","Sleeping..","info")
        util.sleep_interval()
        #util.sendEvent("Plugin wokeup","Wokeup..","info")
