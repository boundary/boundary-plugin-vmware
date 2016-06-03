#!/usr/bin/env python
# This script is called after the plugin files have been copied to the target host file system
from bootstrap import Bootstrap
from modules import util
import sys
def isPythonVesrsionSupported():
    currentPythonVersion = sys.version_info
    pluginSupportedPythonVersions = ['2.7.5','2.7.6','2.7.7','2.7.8','2.7.9','3.3.0','3.3.1','3.3.2','3.3.3','3.3.4','3.3.5','3.3.6','3.4.0','3.4.1','3.4.2']
    isPythonVersionSupported = False
    currentPythonVersions = str(currentPythonVersion[0]) + "." +str(currentPythonVersion[1]) +"."+str(currentPythonVersion[2])
    for version in pluginSupportedPythonVersions:
        if currentPythonVersions == version: 
            isPythonVersionSupported = True
            break
        else:
            isPythonVersionSupported = False
    return isPythonVersionSupported

if __name__ == "__main__":
  if (isPythonVesrsionSupported()):
    bootstrap = Bootstrap()
    bootstrap.setup()
  else:
      currentPythonVersion = sys.version_info
      util.sendEvent("Plugin vmware:", "Python version not supported: [" + str(currentPythonVersion[0]) + "." +str(currentPythonVersion[1]) +"."+str(currentPythonVersion[2])+"]", "error")
      sys.exit(-1)
