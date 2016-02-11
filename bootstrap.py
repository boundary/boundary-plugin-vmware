#!/usr/bin/env python
import os
import sys
import subprocess
import platform
from subprocess import PIPE, Popen
if sys.version_info >= (3, 0, 0):
    import urllib.request
else:
    import urllib

class Bootstrap:

  def __init__(self,
               python="python",
               requirements="requirements.txt",
               pipGetUrl="https://bootstrap.pypa.io/get-pip.py",
               pythonPath="PYTHONPATH=/usr/lib/boundary/.local/lib/pythonDYNAMICVERSION/site-packages/ /usr/lib/boundary/.local/bin/pip ",
               pipFileName="get-pip.py",
               pipCheckcommand_1="pip --version",
               pipCheckcommand_2="PYTHONPATH=/usr/lib/boundary/.local/lib/pythonDYNAMICVERSION/site-packages/ /usr/lib/boundary/.local/bin/pip --version",
               pipFoundInGlobal="common",
               pipFoundInboundary="boundary",
               install="installPIP",
               osType="Windows",
               pipNotFoundVal="No such file or directory,is currently not installed"):
    self.python = python
    self.requirements = requirements
    self.pipGetUrl = pipGetUrl
    self.pipFileName = pipFileName
    self.pythonPath = pythonPath
    self.pipCheckcommand_1 = pipCheckcommand_1
    self.pipCheckcommand_2 = pipCheckcommand_2
    self.pipNotFoundVal = pipNotFoundVal
    self.isPipFoundORNot = " "
    self.pipFoundInGlobal = pipFoundInGlobal
    self.pipFoundInboundary = pipFoundInboundary
    self.install = install
    self.osType = osType
    

  def shellcmd(self, cmd, echo=False):
    """ Run 'cmd' in the shell and return its standard out.
    """
    if not echo: print('[cmd] {0}'.format(cmd))
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.communicate()[0]
    if not echo: print(out)
    return out

  def install_libs(self):
    """Install the dependencies into the virtual env
    """
    self.installLibs()

  def setup(self):
    """Bootraps a python environment
    """
    if os.path.isfile(self.requirements):
      # self.installPIP()
      self.install_libs()
      
    
  def download(self):
    """download pip file
    """
    urllib.urlretrieve (self.pipGetUrl, self.pipFileName)

  def deleteFile(self):
    """Delete downloaded pip file
    """
    os.remove(self.pipFileName)
  
  def checkPIPIsInstalledOrNot(self, command):
    version = self.getPythonVersion()
    command = command.replace("DYNAMICVERSIN",version)
    process = Popen(
        args=command,
        stdout=PIPE,
        shell=True
    )
    return process.communicate()[0]

  def getPythonVersion(self):
    """Get python version
    """
    pythonVersionAarray = sys.version.split(' ')[0].split(".")
    return (pythonVersionAarray[0] + pythonVersionAarray [1])

  def isFound(self, retCommandValues):
    """ checking retCommandValues contains 
    """
    pipNotFoundArray = self.pipNotFoundVal.split(",")
    isFound = True
    for pipNotFound in pipNotFoundArray:        
        if pipNotFound in retCommandValues:
            isFound =  False
            break
            return
    else:
            isFound =  True
           
    
    
    
  def checkPipIsInstalled(self):
    """ checking pip is installed or not 
    """
    retCommandValues = self.checkPIPIsInstalledOrNot(self.pipCheckcommand_1)
    if retCommandValues is not None:
        isFound = self.isFound(retCommandValues)
        
        if isFound == True:
            self.isPipFoundORNot = self.pipFoundInGlobal
            return 
        else:
            retCommandValues = self.checkPIPIsInstalledOrNot(self.pipCheckcommand_2) 
            isFound = self.isFound(retCommandValues)
            if isFound == True:
                self.isPipFoundORNot = self.pipFoundInboundary
                return
            else:
                self.isPipFoundORNot = self.install
            return
    
  
  def installLibs(self):
    """ Install dependencies 
    """
    self.checkPipIsInstalled()
    platformName = platform.platform(aliased=True)
    if platformName.find(self.osType) != -1:
                if self.isPipFoundORNot == self.install:
                    self.download()
                    self.shellcmd(self.python + " " + self.pipFileName)
                    self.shellcmd('pip install -r {0} -t ./.pip'.format(self.requirements))
                    self.deleteFile()
    else :
        
        if self.isPipFoundORNot == self.pipFoundInGlobal:
           self.shellcmd('pip install -r {0} -t ./.pip'.format(self.requirements))
           return 
           
        if self.isPipFoundORNot == self.pipFoundInboundary:
            version = self.getPythonVersion()
            pythonPath = self.pythonPath.replace("DYNAMICVERSION", version)
            self.shellcmd( pythonPath + ' install -r {0} -t ./.pip'.format(self.requirements))
            return 
           
        if self.isPipFoundORNot == self.install:
                self.download()
                self.shellcmd(self.python + " " + self.pipFileName + " --user")
                version = self.getPythonVersion()
                pythonPath = self.pythonPath.replace("DYNAMICVERSION", version)
                self.shellcmd(pythonPath  + ' install -r {0} -t ./.pip'.format(self.requirements))
                self.deleteFile()
                return 
  
    
if __name__ == "__main__":
  bootstrap = Bootstrap()
  bootstrap.setup()

