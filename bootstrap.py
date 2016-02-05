#!/usr/bin/env python
import os
import sys
import subprocess
import platform
if sys.version_info >= (3, 0, 0):
    import urllib.request
else:
    import urllib

class Bootstrap:

  def __init__(self,
               python="python",
               requirements="requirements.txt",
               pipGetUrl="https://bootstrap.pypa.io/get-pip.py",
               sudoCommand="sudo",
               supportedOS="Windows,centos,Ubuntu,redhat",
               pipFileName="get-pip.py"):
    self.python = python
    self.requirements=requirements
    self.pipGetUrl = pipGetUrl
    self.sudoCommand = sudoCommand
    self.supportedOS = supportedOS
    self.pipFileName = pipFileName

  def shellcmd(self,cmd,echo=False):
    """ Run 'cmd' in the shell and return its standard out.
    """
    if not echo: print('[cmd] {0}'.format(cmd))
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    out = p.communicate()[0]
    if not echo: print(out)
    return out

  def install_libs(self):
    """Install the dependencies into the virtual env
    """
    self.shellcmd('pip install -r {0} -t ./.pip'.format(self.requirements))

  def setup(self):
    """Bootraps a python environment
    """
    if os.path.isfile(self.requirements):
      self.installPIP()
      self.install_libs()
      
  def installPIP(self):
    """Install the pip dependencies into the virtual env
    """
    platformName = platform.platform(aliased=True)
    supportedOsArrayList = []
    supportedOsArrayList = self.supportedOS.split(",")
    for supportedOS in supportedOsArrayList:
        if platformName.find(supportedOS) != -1:
            if supportedOS == 'Windows':
                self.download()
                self.shellcmd(self.python + " " + self.pipFileName)
                self.deleteFile()
                break
            else:
 		 
                 self.download()
		 self.shellcmd(self.python +  "  " + self.pipFileName + " --user")
                 self.shellcmd("export PATH=$PATH:~/.local/bin")
                 ##self.deleteFile()
                 break
            
                
             
            
    
  def download(self):
    """download pip file
    """
    urllib.urlretrieve (self.pipGetUrl,  self.pipFileName)

  def deleteFile(self):
    """Delete downloaded pip file
    """
    os.remove(self.pipFileName)
    
  
    
if __name__ == "__main__":
  bootstrap = Bootstrap()
  bootstrap.setup()

