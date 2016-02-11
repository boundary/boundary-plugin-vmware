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
               isPipFound="succeeded",
               install="installPIP",
               osType="Windows",
               pipCheckCmd='python -c "import pip" 2>&- && echo "succeeded" || echo "failed"',
               isPipExistsInUserLocalDir = "/usr/lib/boundary/.local/bin/pip",
               isPipFoundInUserLocalDir = "userLocalDir"):
      
    self.python = python
    self.requirements = requirements
    self.pipGetUrl = pipGetUrl
    self.pipFileName = pipFileName
    self.pythonPath = pythonPath
    self.isPipFound = isPipFound
    self.install = install
    self.osType = osType
    self.pipCheckCmd = pipCheckCmd
    self.isPipFound = isPipFound
    self.isPipExistsInUserLocalDir = isPipExistsInUserLocalDir

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
  

  def getPythonVersion(self):
    """Get python version
    """
    pythonVersionAarray = sys.version.split(' ')[0].split(".")
    return (pythonVersionAarray[0] + pythonVersionAarray [1])

  def isFound(self):
    """ checking is pip is installed or not
    """
    isFound = self.shellcmd(self.pipCheckCmd)
    isPipExeFileFound = self.isPipExistsInUserLocal()
       if(isPipExeFileFound == True):
        return self.isPipFoundInUserLocalDir
    elif isFound.strip() == 'succeeded':
        return self.isPipFound
    else:
        return self.install
           
  
  def isPipExistsInUserLocal(self):
    """ checking  is Pip Exists In User Local
    """
    retVale = os.path.exists(self.isPipExistsInUserLocalDir)
    return retVale

  def installLibs(self):
    """ Install dependencies 
    """
    retVal = self.isFound()
    platformName = platform.platform(aliased=True)
    if platformName.find(self.osType) != -1:
                if retVal == self.install:
                    self.download()
                    self.shellcmd(self.python + " " + self.pipFileName)
                    self.shellcmd('pip install -r {0} -t ./.pip'.format(self.requirements))
                    self.deleteFile()
    else :
        if retVal == self.isPipExistsInUserLocalDir:
            version = self.getPythonVersion()
            pythonPath = self.pythonPath.replace("DYNAMICVERSION", version)
            self.shellcmd(pythonPath + ' install -r {0} -t ./.pip'.format(self.requirements))
            return
        if retVal == self.isPipFound:
           self.shellcmd('pip install -r {0} -t ./.pip'.format(self.requirements))
           return 
        else :         
                self.download()
                self.shellcmd(self.python + " " + self.pipFileName + " --user")
                version = self.getPythonVersion()
                pythonPath = self.pythonPath.replace("DYNAMICVERSION", version)
                self.shellcmd(pythonPath + ' install -r {0} -t ./.pip'.format(self.requirements))
                self.deleteFile()
                return 
  
    
if __name__ == "__main__":
  bootstrap = Bootstrap()
  bootstrap.setup()

