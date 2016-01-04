#!/usr/bin/env python
import os
import shutil
import sys
import subprocess
import tarfile
if sys.version_info >= (3, 0, 0):
    import urllib.request
else:
    import urllib

class Bootstrap:

  def __init__(self,
               python="python",
               requirements="requirements.txt"):
    self.python = python
    self.requirements=requirements

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
      self.install_libs()

if __name__ == "__main__":
  bootstrap = Bootstrap()
  bootstrap.setup()
