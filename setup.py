from setuptools import setup,find_packages
import os.path
import os

# try to  read the version file
versionFilePath = 'version.txt'
if os.path.exists(versionFilePath):
  try:
    f = open(versionFilePath, 'r')
    versionNumber = f.read()
    f.close()
    # is it really string ?
    versionNumber = str(versionNumber)
    versionNumber = versionNumber[1:]
  except Exception, e:
    print("loading version info failed")
    print(e)
else:
  print("version file not found, using default")
  versionNumber = "0.1"

# generate data files tree
data_files = []
for pathTuple in os.walk('.'):
  data_files.append( ('', pathTuple[0]) )
  
setup (
  name = 'modRana',
  version = versionNumber,

  # just package everything in this folder
  data_files = data_files,

  # list the main modRana script
  scripts = ['modrana'],

  author = 'Martin Kolman',
  author_email = 'modrana@gmail.com',

  description = 'A flexible GPS navigation system for mobile Linux devices.',
  url = 'http://www.modrana.org',
  license = 'GNU GPLv3',
  long_description= 'Modrana is a flexible GPS navigation system for mobile Linux devices.',

  # could also include long_description, download_url, classifiers, etc.
)