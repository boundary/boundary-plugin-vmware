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
        self._lock = threading.Lock()

    def run(self):
        self.vmware = VMWare(self.vcenter)

        self.discovery_thread = threading.Thread(target=self._discovery)
        self.discovery_thread.daemon = True
        self.discovery_thread.setName(self.vcenter['host'] + "_" + "Discovery")
        self.discovery_thread.start()

        while True:
            try:
                self._lock.acquire()
                self.vmware.collect()
                self._lock.release()

                time.sleep(float(self.vcenter.get("pollInterval", 1000) / 1000))
            except StandardError as se:
                util.sendEvent("Plugin vmware: Unknown Error", "Unknown error occurred: [" + str(se) + "]", "critical")
                if self._lock.locked:
                    self._lock.release
                sys.exit(-1)

    def _discovery(self):
        #while True:
            try:
                #self._lock.acquire()
                #util.sendEvent("Plugin vmware: Discovery Cycle for " + self.vcenter['host'], "Running discovery cycle for " + self.vcenter['host'] + " started.", "info")
                self.vmware.discovery(self)
                #self._lock.release()
                #util.sendEvent("Plugin vmware: Discovery Cycle for " + self.vcenter['host'], "Running discovery cycle for " + self.vcenter['host'] + " completed.", "info")

                #time.sleep(self.vcenter.get("discoveryInterval", 10800000) / 1000)
            except StandardError as se:
                util.sendEvent("Unknown Error", "Unknown error occurred: [" + str(se) + "]", "error")
                if self._lock.locked:
                    self._lock.release
                sys.exit(-1)

if __name__ == "__main__":
    params = util.parse_params()
    util.sendEvent("Plugin started", "Started vmware plugin", "info")

    for vcenter in params['items']:
        thread = CollectionThread(vcenter)
        thread.daemon = True
        thread.setName(vcenter['host'])
        thread.start()

    while True:
        time.sleep(60)
