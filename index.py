__author__ = 'goutham'

import socket
import sys
import time
import threading

sys.path.append('./.pip')

from modules import util
from modules.vmware import VMWare

HOSTNAME = socket.gethostname()


class CollectionThread(threading.Thread):

    def __init__(self, vcenter):
        threading.Thread.__init__(self)
        self.vcenter = vcenter

    def run(self):
        vmware = VMWare(self.vcenter)
        vmware.discovery()
        while True:
            try:
                vmware.collect()
                time.sleep(float(self.vcenter.get("pollInterval", 1000) / 1000))
            except StandardError as se:
                util.sendEvent("Unknown Error", "Unknown error occurred: [" +str(se) + "]", "critical")
                sys.exit(-1)

if __name__ == "__main__":
    params = util.parse_params()
    util.sendEvent("Plugin started", "Started vmware plugin", "info")

    for vcenter in params['items']:
        thread = CollectionThread(vcenter)
        thread.setName(vcenter['host'])
        thread.start()

    while(True):
        pass
