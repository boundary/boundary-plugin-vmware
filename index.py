__author__ = 'goutham'

import socket

from modules import util
from modules.vmware import VMWare

HOSTNAME = socket.gethostname()

if __name__ == "__main__":
    # now = datetime.datetime.now()
    # util.report_metric("name", "value", source=HOSTNAME, timestamp=now)

    vmware = VMWare()
    vmware.discovery()

    params = util.parse_params()

    while(True):
        for vcenter in params:
            vmware.collect(vcenter['host'])

        util.sleep_interval()