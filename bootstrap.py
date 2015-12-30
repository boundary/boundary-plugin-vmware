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
               version="12.0.4",
               base='http://pypi.python.org/packages/source/v/virtualenv',
               python="python",
               env="pyenv",
               requirements="requirements.txt"):
    self.version = version
    self.base = base
    self.python = python
    self.env = env
    self.dirname = 'virtualenv-' + self.version
    self.tgz_file = self.dirname + '.tar.gz'
    self.venv_url = self.base + '/' + self.tgz_file
    self.requirements=requirements

  def shellcmd(self,cmd,echo=False):
    """ Run 'cmd' in the shell and return its standard out.
    """
    if not echo: print('[cmd] {0}'.format(cmd))
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    out = p.communicate()[0]
    if not echo: print(out)
    return out

  def download(self):
    """ Fetch virtualenv from PyPI
    """
    if sys.version_info >= (3, 0, 0):
        urllib.request.urlretrieve(self.venv_url,self.tgz_file)
    else:
        urllib.urlretrieve(self.venv_url,self.tgz_file)

  def extract(self):
    """ Untar
    """
    tar = tarfile.open(self.tgz_file,"r:gz")
    tar.extractall()

  def create(self):
    """ Create the initial env
    """
    self.shellcmd('{0} {1}/virtualenv.py {2}'.format(self.python,self.dirname,self.env))

  def install(self):
    """Install the virtualenv package itself into the initial env
    """
    self.shellcmd('{0}/bin/pip install {1}'.format(self.env,self.tgz_file))

  def install_libs(self):
    """Install the virtualenv package itself into the initial env
    """
    self.shellcmd('{0}/bin/pip install -r {1}'.format(self.env,self.requirements))

  def cleanup(self):
    """ Cleanup
    """
    os.remove(self.tgz_file)
    shutil.rmtree(self.dirname)

  def setup(self):
    """Bootraps a python environment
    """
    self.download()
    self.extract()
    self.create()
    self.install()
    self.cleanup()
    if os.path.isfile(self.requirements):
      self.install_libs()

if __name__ == "__main__":
  bootstrap = Bootstrap()
  bootstrap.setup()
