#
# Copyright 2016 BMC Software, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 

__author__ = 'goutham'

import socket
import sys
import time
import threading
import ctypes

sys.path.append('./.pip')
from modules.vmware import VMWare
from modules import util
import traceback

HOSTNAME = socket.gethostname()


class CollectionThread(threading.Thread):
    def __init__(self, vcenter):
        threading.Thread.__init__(self)
        self.vcenter = vcenter
        self._lock = threading.Lock()

    def run(self):
        self.start()

    def _discovery(self):
        # while True:
        try:
            # self._lock.acquire()
            # util.sendEvent("Plugin vmware: Discovery Cycle for " + self.vcenter['host'], "Running discovery cycle for " + self.vcenter['host'] + " started.", "info")
            self.vmware.discovery(self)
            # self._lock.release()
            # util.sendEvent("Plugin vmware: Discovery Cycle for " + self.vcenter['host'], "Running discovery cycle for " + self.vcenter['host'] + " completed.", "info")

            # time.sleep(self.vcenter.get("discoveryInterval", 10800000) / 1000)
        except Exception as se:
            util.sendEvent("Plugin vmware: Discovery error", "Unknown error occurred: [" + str(se) + "]", "error")
            if self._lock.locked:
                self._lock.release
                # sys.exit(-1)

    def terminate_thread(self, thread):
        """Terminates a python thread from another thread.

        :param thread: a threading.Thread instance
        """
        if not thread.isAlive():
            return

        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(thread.ident), exc)
        if res == 0:
            # raise ValueError("nonexistent thread id")
            print("Non existent thread id")
        elif res > 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
            # raise SystemError("PyThreadState_SetAsyncExc failed")
            print("PyThreadState_SetAsyncExc failed")

    def start(self):
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
            except Exception as se:
                self._lock.release()
                util.sendEvent("Plugin vmware: Unknown Error", "Unknown error occurred: [" + str(se) + "]", "critical")
                time.sleep(float(self.vcenter.get("pollInterval", 1000) / 1000))
                self.terminate_thread(self.discovery_thread)  # Killing old discovery thread
                util.sendEvent("Plugin vmware", "Trying to re-connect to vCenter: [" + self.vcenter['host'] + "]",
                               "info")
                self.vmware = VMWare(self.vcenter)
                self.discovery_thread = threading.Thread(target=self._discovery)
                self.discovery_thread.daemon = True
                self.discovery_thread.setName(self.vcenter['host'] + "_" + "Discovery")
                self.discovery_thread.start()


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
