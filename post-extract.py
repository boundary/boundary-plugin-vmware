#!/usr/bin/env python
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
    return isPythonVersionSupported

if __name__ == "__main__":
  if (isPythonVesrsionSupported()):
    bootstrap = Bootstrap()
    bootstrap.setup()
  else:
      currentPythonVersion = sys.version_info
      util.sendEvent("Plugin vmware:", "Python version not supported: [" + str(currentPythonVersion[0]) + "." +str(currentPythonVersion[1]) +"."+str(currentPythonVersion[2])+"]", "error")
      sys.exit(-1)
