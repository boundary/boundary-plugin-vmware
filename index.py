__author__ = 'goutham'

import socket
import sys
import time
import threading
import ctypes
sys.path.append('./.pip')
from modules.vmware import VMWare
from modules import util


HOSTNAME = socket.gethostname()


class CollectionThread(threading.Thread):

    def __init__(self, vcenter):
        threading.Thread.__init__(self)
        self.vcenter = vcenter
        self._lock = threading.Lock()

    def run(self):
            self.start()
        
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
                pass 
                #sys.exit(-1)
    
    def terminate_thread(self,thread):
        """Terminates a python thread from another thread.

        :param thread: a threading.Thread instance
        """
        if not thread.isAlive():
            return

        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
        if res == 0:
            raise ValueError("nonexistent thread id")
        elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
        
    def start(self):
        self.vmware = VMWare(self.vcenter)
        self.discovery_thread = threading.Thread(target=self._discovery)
        self.discovery_thread.daemon = True
        self.discovery_thread.setName(self.vcenter['host'] + "_" + "Discovery")
        self.discovery_thread.start()

        while True:
            try:
                self._lock.acquire()
                retval = self.vmware.collect()
                self._lock.release()
                time.sleep(float(self.vcenter.get("pollInterval", 1000) / 1000))
                if retval == "error" :
                    break
            except StandardError as se:
                util.sendEvent("Plugin vmware: Unknown Error", "Unknown error occurred: [" + str(se) + "]", "critical")
                if self._lock.locked:
                    self._lock.release
                break
                #sys.exit(-1)
        while True:
            self.terminate_thread(self.discovery_thread) #Killing old discovery thread
            self.start()
        
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

