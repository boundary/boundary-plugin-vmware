__author__ = 'goutham'

import socket
import sys
import time
import threading

sys.path.append('./.pip')

from modules import util
from modules.vmware import VMWare

HOSTNAME = socket.gethostname()

class CollectionThread:

    def __init__(self, params):
        self.params = params
        self.vmware = VMWare(params)

    def run(self):
        self.vmware.discovery()
        while True:
            try:
                self.vmware.collect()
                time.sleep(float(self.params.get("pollInterval", 1000) / 1000))
            except StandardError as se:
                util.sendEvent("Unknown Error", "Unknown error occurred: [" +str(se) + "]", "critical")
                sys.exit(-1)

if __name__ == "__main__":
    params = util.parse_params()
    util.sendEvent("Plugin started","Started vmware plugin","info")

    for vcenter in params['items']:
        collector = CollectionThread(vcenter)
        t = threading.Thread(target=collector.run(), args=())
        t.setName(vcenter['host'])
        t.start()