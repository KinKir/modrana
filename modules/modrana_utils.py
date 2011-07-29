# modRana - shared utility classes and methods
from __future__ import with_statement # for python 2.5
import threading
import os
try:
  import magic
  magicAvailable = True
except ImportError:
  magicAvailable = False
  print("WARNING : libmagic is not installed : WARNING")
  print("this means that batch-downloaded tiles will not be checked,")
  print("to remove HTML error pages from real tiles")
  print("-> this can result in tiles not showing up after batch-download")
  print("WARNING : : WARNING")
from cStringIO import StringIO
#import time

class Empty(Exception):
    "Exception raised by the Synchronized circular stack"
    pass

class SynchronizedCircularStack:
  """
  this should be a synchronized circular stact implementation
  * LIFO
  * once the size limit is reached, items re discarded,
    starting by the oldest ones
  * thread safe using a mutex
  maxItems sets the maximum number of items, 0=infinite size


  """
  def __init__(self,maxItems=0):
    self.list = []
    self.listLock = threading.Lock()
    self.maxItems = maxItems

  def push(self, item):
    """add a new item to the stack, make sure the size stays in bounds"""
    with self.listLock:
      self.list.append(item)
      # check list size
      if self.maxItems:
          # discard olderst items to get back to the limit
          while len(self.list) > self.maxItems:
            del self.list[0]

  def batchPush(self, itemList):
    """batch push items in a smart way"""
    with self.listLock:
      """
      reverse the imput list to simulate stack pushes
      then combine the old list and the new one
      and finally slice it to fit to the size limit
      """
      itemList.reverse()
      self.list.extend(itemList)
      self.list = self.list[-self.maxItems:]

  def pop(self):
    """
    NOTE: when the queue is empty, the Empty exception is raised
    """
    with self.listLock:
      if len(self.list) == 0:
        raise Empty
      else:
        return self.list.pop()

  def popValid(self):
    """
    if the stack is not empty and the item is valid, return
    (popped_item, True)
    if the stack is empty and no items are available, return
    (None, True)

    this basically enables easy consuming
    th queue without having to handle the
    Empty exception
    """
    with self.listLock:
      if len(self.list) == 0:
        return (None,False)
      else:
        return (self.list.pop(),True)

  def isIn(self, item):
    """item existence testing"""
    with self.listLock:
      return item in self.list

#  def isInNonSync(self, item):
#    """nonsynchronized version of item existence testing"""
#    return item in self.list

def isTheStringAnImage(s):
  """test if the string contains an image
  by reading its magic number"""
#  start = time.clock()
  if magicAvailable:
    # create a file like object
    f = StringIO(s)
    mime = str(magic.from_buffer(f.read(1024), mime=True))
    f.close() # clenup
    # get ists mime
    mimeSplit = mime.split('/')
    mime1 = mimeSplit[0]
    # check if its an image

  #  print("mime checked in %1.2f ms" % (1000 * (time.clock() - start)))
    if mime1 == 'image':
      return True
    else:
      return False
  else:
    # mime checking not available
    # lets hope it really is a tile
    return True

def createFolderPath(newPath):
  """
  Creat a path for a directory and all needed parent forlders
  -> parent directoryies will be created
  -> if directory already exists, then do nothing
  -> if there is another filsystem object (like a file) with the same name, raise an exception
  """
  if not newPath:
    print("cannot create folder, wrong path: ", newPath)
    return False
  if os.path.isdir(newPath):
    return True
  elif os.path.isfile(newPath):
    print("cannot create directory, file already exists: '%s'" % newPath)
    return False
  else:
    print("creating path: %s" % newPath)
    head, tail = os.path.split(newPath)
    if head and not os.path.isdir(head):
        createFolderPath(head) # NOTE: recursion
    if tail:
        os.mkdir(newPath)
    return True

# from:
# http://www.5dollarwhitebox.org/drupal/node/84
def bytes2PrettyUnitString(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fTB' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fGB' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fMB' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fKB' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size