import os.path
#!/usr/bin/python
#----------------------------------------------------------------------------
# Sample of a Rana module.
#----------------------------------------------------------------------------
# Copyright 2007, Oliver White
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------
#from dbus.service import Object
from base_module import ranaModule
from upoints import gpx
import geo
import os
import glob
import cPickle
#import marshal
from time import clock
from time import gmtime, strftime
#from time import clock

def getModule(m,d):
  return(loadTracklogs(m,d))

class loadTracklogs(ranaModule):
  """A sample pyroute module"""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.tracklogs = {} # dictionary of all loaded tracklogs, path is the key
    #self.set('tracklogs', self.tracklogs) # now we make the list easily acessible to other modules
    self.cachePath = 'cache/tracklogs/tracklog_cache.txt'
    self.cache = {}
    self.tracklogFolder = 'tracklogs/'
    self.tracklogList = []
    self.tracklogPathList = []
    self.categoryList = []


  def firstTime(self):
    folder = self.get('tracklogFolder', 'tracklogs/')

    if folder != None:
      
      # make sure there is a slash on the end
      # TODO: check if this is too platform specific
      if folder[-1] == '/':
        self.tracklogFolder = folder
      else:
        self.tracklogFolder = (folder+'/')
    else:
      self.tracklogFolder = 'tracklogs/'

#    self.load()

  def handleMessage(self, message, type, args):
    if message == 'loadActive':
      # load the active tracklog
      path = self.get('activeTracklogPath', None)
      if path != None and self.tracklogList:
        print "loading tracklog: %s" % path

        # Zeroeth, is the tracklog already loaded ?
        if path not in self.tracklogs.keys():
          # First, is the cache loaded ?
          if self.cache == {}:
            self.loadCache()
          else:
            print "not loading cache (already loaded)"
          # Second, try to load the tracklog (if its not loaded)

          try:
            self.loadTracklog(path)
            print "tracklog successfully loaded"
          except:
            print "loading tracklog failed: %s" % path

          # Third, assure consistency of the cache
          print "assuring cache consistency"
          self.save()
          self.cleanCache()
          print "cache consistency assured"


  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

  def loadCache(self):
    # unpickle the cache from file
    print "loading cache"
    start = clock()
    try:
      f = open(self.cachePath, 'r')
      self.cache = cPickle.load(f)
    except:
      print "loadTracklogs: loading cache from file failed"
      self.cache = {}
    print "Loading cache took %1.2f ms" % (1000 * (clock() - start))

  def cleanCache(self):
    """remove files that are not present from the cache"""
    paths = self.tracklogPathList
    garbage = filter(lambda x: x not in paths, self.cache)


    for g in garbage:
      del self.cache[g]

  def deleteTrackFromCache(self, file):
    # self explanatory
    if file in self.cache:
      del self.cache[file]

  def getActiveTracklog(self):
    path = self.getActiveTracklogPath()
    # is the tracklog loaded ?
    if path not in self.tracklogs.keys():
      self.loadTracklog(path)
      self.save()
    # was the tracklog loaded successfully ?
    if path not in self.tracklogs.keys():
      return None
    else:
      return self.tracklogs[path]

  def getTracklogForPath(self, path):
    # return a tracklog coresponding to the path specified
    if path in self.tracklogs.keys():
      return self.tracklogs[path]
    else:
      # try to load the track
      track = self.loadTracklog(path)
      if track: # return the loaded track
        return track
      else: # something went wrong, return None
        return None

  def getTracklogList(self):
    if self.tracklogList:
      return self.tracklogList
    else:
      self.listAvailableTracklogs()
      return self.tracklogList

  def getTracklogPathList(self):
    if self.tracklogPathList:
      return self.tracklogPathList
    else:
      self.listAvailableTracklogs()
      return self.tracklogPathList

  def getLoadedTracklogPathList(self):
      """return a list of loaded tracklog paths"""
      return self.tracklogs.keys()


  def getIndexForPath(self,path):
    """get index for the tracklog with corresponding path
       from the main tracklog lists"""
       
    return self.tracklogPathList.index(path)


  def getActiveTracklogPath(self):
    path = self.get('activeTracklogPath', None)
    return path



  def listAvailableTracklogs(self):
    print "** making a list of available tracklogs"

    tf = self.tracklogFolder
    # does the tracklog folder exist ?
    if not os.path.exists(tf):
      return # no tracklog folder, nothing to list
    # get the available directories,
    # each directory represents a category
    currentFolders = os.listdir(tf)
    # leave just nonhidden folders
    currentFolders = filter(lambda x: os.path.isdir(tf+x) and x[0]!='.', currentFolders)
    # add files from all available folders
    availableFiles = []
    pathList = []
    for folder in currentFolders:
      #TODO: suport other tracklogs
      folderFiles = glob.glob(tf+folder+'/*.gpx')
      folderFiles.extend(glob.glob(tf+folder+'/*.GPX'))
      # remove possible folders
      folderFiles = filter(lambda x: os.path.isfile(x), folderFiles)
      for file in folderFiles:
        path = file
        filename = os.path.split(file)[1]
        lastModifiedEpochSecs = os.path.getmtime(path)
        lastModified = strftime("%d.%m.%Y %H:%M:%S",gmtime(lastModifiedEpochSecs))
        size = self.convertBytes(os.path.getsize(path))
        extension = os.path.splitext(path)[1]
        cat = folder
        item={'path':path,
              'filename': filename,
              'lastModified':lastModified,
              'size':size,
              'type':extension[1:],
              'cat':cat
               }
        availableFiles.append(item)
      pathList.extend(folderFiles)

    self.categoryList = currentFolders

    print "*  using this tracklog folder:"
    print self.tracklogFolder
    print "*  does it exist ?"
    print os.path.exists(self.tracklogFolder)
    print "*  there are %d tracklogs available" % len(availableFiles)
    self.tracklogPathList = pathList
    self.tracklogList = availableFiles

  def getCatList(self):
    # return the list of available categories
    if not self.categoryList:
      self.listAvailableTracklogs()
    return self.categoryList

  def getTracPathsInCat(self, cat):
    # return a list of tracklogs in a given category
    if not self.tracklogList:
      self.listAvailableTracklogs()
    return filter(lambda x: x['cat'] == cat,  self.tracklogList)

  
  def setTracklogPathCategory(self,path,cathegory):
    pass
#    """set a cathegory for tracklog identified by path"""
#    # does the path/tracklog exist ?
#    if path not in self.tracklogPathList:
#      # we try to reload the tracklog list
#      self.listAvailableTracklogs()
#      if path not in self.tracklogPathList:
#        return # tracklog does not exist, so we return
#
#    # tracklog exists so we can set its cathegory
#    catData = self.get('tracklogPathCathegory', {})
#    catData[path] = cathegory
#    # update the persistent list
#    self.set('tracklogPathCathegory', catData)
#
#    index = self.getIndexForPath(path)
#    # update the current in memmory list
#    self.tracklogList[index]['cat'] = cathegory

  # from:
  # http://www.5dollarwhitebox.org/drupal/node/84
  def convertBytes(self, bytes):
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

#  def load(self):
#    start = clock()
#
#    try:
#      f = open(self.cachePath, 'r')
#      cache = cPickle.load(f)
#
#      self.cache = cache
#    except:
#      print "loadTracklogs: loading cache from file failed"
#      self.cache = {}
#
#    print "Loading from cache took %1.2f ms" % (1000 * (clock() - start))
#
#    files = []
#    if os.path.exists(self.tracklogFolder):
#      files = os.listdir(self.tracklogFolder)
#      files = filter(lambda x: x != '.svn', files)
#
#
#      print self.tracklogFolder
#      print os.path.exists(self.tracklogFolder)
#      for file in files:
#        try:
#          self.loadTracklog(self.tracklogFolder + file)
#        except:
#          "loading tracklog failed: %s" % file
#
#    self.cleanCache(files)
#    self.save()
#    print "Loading tracklogs took %1.2f ms" % (1000 * (clock() - start))

  def save(self):
    try:
      f = open(self.cachePath, 'w')
      cPickle.dump(self.cache, f)
      f.close()
    except:
      print "loadTracklogs: cant store tracklog data to cache, tracklogs wil be loaded from files next time"

#  def saveClusters(self, clusters):

  def setPathAsActiveTracklog(self, path):
    self.set('activeTracklogPath', path)

  def loadPathList(self, pathList):
    print "loading path list"
    start = clock()
    count = len(pathList)
    index = 1
    self.sendMessage('notification:loading %d tracklogs#1' % count)
    for path in pathList:
      self.loadTracklog(path, False)
      self.sendMessage('notification:%d of %d loaded#1' % (index, count))
      index = index + 1

    elapsed = (1000 * (clock() - start))
    print "Loading tracklogs took %1.2f ms" % elapsed
    self.save()
    self.cleanCache()
    self.sendMessage('notification:%d tracks loaded in %1.2f ms#1' % (count, elapsed) )


  def loadTracklog(self, path, notify=True):
    """load a GPX file to datastructure"""
    # is the cache loaded
    if self.cache == {}:
      # load the cache
      self.loadCache()

    # just to be sure, refresh the tracklog list if needed
    if self.tracklogList == []:
      self.listAvailableTracklogs()

    start = clock()
    self.filename = path

    file = None

    try:
      file = open(path, 'r')
    except:
      print "loading tracklo failed: %s" % path

    if notify:
      self.sendMessage('notification:loading %s#1' % path)

    if(file): # TODO: add handling of other than GPX files
      track = gpx.Trackpoints() # create new Trackpoints object
#      print track
      # lets assume we have only GPX 1.1 files TODO: 1.1 and 1.0
      try:
        track.import_locations(file, "1.1") # load a gpx file into it
      except Exception, e:
        print "loading tracklog failed: %s" % e
        if notify:
          self.sendMessage('notification:loading tracklog failed#2')
        return
#      print file
#      print track
      file.close()

      type="GPX" #TODO: more formats support

      self.tracklogs[path] = GPXTracklog(track, path, type, self.cache, self.save)

      print "Loading %s took %1.2f ms" % (path,(1000 * (clock() - start)))
      if notify:
        self.sendMessage('notification:loaded in %1.2f ms' % (1000 * (clock() - start)))
    else:
      print "No file"


  def storeRouteAndSetActive(self, route, name='', cat='misc'):
    path = self.storeRoute(route, name, cat)
    self.set('activeTracklogPath', path)

  def storeRoute(self, route, name="", cat='misc'):
    """store a route, found by Google Directions to a GPX file,
       then load this file to tracklogs list,
       return resulting path
       or None when storing fails"""
    newTracklog = gpx.Trackpoints()
    trackpoints = map(lambda x: gpx.Trackpoint(x[0],x[1]), route)
    newTracklog.append(trackpoints)

    timeString = strftime("%Y%m%d#%H-%M-%S", gmtime())
    # gdr = Google Directions Result, TODO: alternate prefixes when we have more routing providers

    name = name.encode('ascii', 'ignore')
    filename = "gdr_" + name + timeString + ".gpx"
    # TODO: store to more formats ?
    return self.storeTracklog(newTracklog, filename, cat, "GPX")


  def storeTracklog(self,tracklog,filename,cat,type,refresh="True"):
    """store tracklog and return the resulting path"""
    folder = self.tracklogFolder
    path = folder + cat +'/'
    # does the directory exist ?
    if not os.path.exists(path):
      # try to create the directory
      try:
        os.makedirs(path)
      except:
        self.sendMessage('notification:Error: tracks folder unusable#3')
        return None
    # is it a directory ?
    if not os.path.isdir(path):
      self.sendMessage('Error: tracks folder unusable#3')
      return None

    if type=="GPX":
      # try to create the file
      try:
        xmlTree = tracklog.export_gpx_file()
        f = open(path+filename, 'w')
        xmlTree.write(f)
        f.close()
      except:
        self.sendMessage('notification:Error: saving tracklog failed#3')
        return None

    """refresh the available tracklog list,
    so the new tracklog shows up"""
    if refresh:
      self.listAvailableTracklogs()
    # TODO: incremental addition of new tracklogs without relisting
    print "%s" % filename
    print "saved successfully"
    return (path+filename)


  def simplePythagoreanDistance(self, x1,y1,x2,y2):
      dx = x2 - x1
      dy = y2 - y1
      return math.sqrt(dx**2 + dy**2)

#  def adjustAproximateCircle(self, points, radius):
#    """test wheter all points are inside the preliminary circle,
#    if not, adjust the radius acordingly"""
##    for point in points:

  # found on:
  # http://www.quanative.com/2010/01/01/server-side-marker-clustering-for-google-maps-with-python/
  def clusterTrackpoints(self, trackpointsList , cluster_distance):
    """
    Groups points that are less than cluster_distance pixels apart at
    a given zoom level into a cluster.
    """
    points = [{'latitude': point.latitude,'longitude': point.longitude} for point in trackpointsList[0]]
    self.set('clPoints', points)
    clusters = []
    while len(points) > 0:
        point1 = points.pop()
        cluster = []
        for point2 in points[:]:

            pixel_distance = geo.distance(point1['latitude'],
                                           point1['longitude'],
                                            point2['latitude'],
                                           point2['longitude'])

            if pixel_distance < cluster_distance:
                points.remove(point2)
                cluster.append(point2)

        # add the first point to the cluster
        if len(cluster) > 0:
            cluster.append(point1)
            clusters.append(cluster)
        else:
            clusters.append([point1])

    return clusters



class tracklog():
  """A basic class representing a tracklog."""
  def __init__(self, trackpointsList, filename, type):
    self.trackpointsList = trackpointsList # here will be the actual list of trackpoints
    self.filename = filename # the filename as used when loading the list from file
    self.type = type
    """
  tracklog types: (for now)
  'gpx'= a GPX tracklog
  'kml'= a KML tracklog
  'nmea' = a NMEA log file
  """
    self.tracklogName = filename # custom name for the tracklog, by default the filename
    self.tracklogDescription = "" # description of the tracklog

  def getFilename(self):
    return self.filename

  def getName(self):
    """returns tracklog name"""
    return self.tracklogName

  def setName(name):
    """sets tracklog name"""
    self.tracklogName = name

  def getType(self):
    """returns tracklog name"""
    return self.type
  
  def getDescription(self):
    """returns tracklog description"""
    return self.tracklogDescription

  def setDescription(description):
    """sets tracklog description"""
    self.tracklogDescription = description

class GPXTracklog(tracklog):
  """A class representing a GPX tracklog."""
  def __init__(self, trackpointsList, filename, type, cache, save):
    tracklog.__init__(self, trackpointsList, filename, type)
    tracklog.type = 'GPX'
    self.routeInfo = None # a dictionary for storing route information
    # TODO: set this automaticaly

    filename = self.filename

    self.cache = cache
    self.save = save

    self.clusters = []

    self.elevation = None

    self.perElevList = None

    # dowe have any points to process ?
    if self.trackpointsList == []:
      # no points, we are done :)
      return

    if filename in cache:
      print "loading from cache"
      self.clusters = cache[filename].clusters
      self.routeInfo = cache[filename].routeInfo
      if self.routeInfo != None:
        self.elevation = True
      self.perElevList = cache[filename].perElevList
      
    else:
      print "creating clusters,routeInfo and perElevList: %s" % filename
      clusterDistance = 5 # cluster points to clusters about 5 kilometers in diameter
      self.clusters = []

      rawClusters = geo.clusterTrackpoints(trackpointsList, clusterDistance) # we cluster the points
      for cluster in rawClusters: # now we find for each cluster a circle encompasing all points
        (centreX,centreY,radius) = geo.circleAroundPointCluster(cluster)
        self.clusters.append(clusterOfPoints(cluster, centreX, centreY, radius))

      self.checkElevation()

      if self.elevation == True:
        self.getPerElev()
      else:
        self.perElevList = None

      ci = CacheItem(self.clusters, self.routeInfo, self.perElevList)
      cache[filename] = ci
      

#    self.checkElevation()
#
#    if self.elevation == True:
#      self.getPerElev()


  def modified(self):
    """the tracklog has been modified, recount all the statistics and clusters"""
    # TODO: implement this ? :D
    self.checkElevation() # update the elevation statistics
    if self.elevation == True:
      self.getPerElev() # update the periodic elevation data

  def checkElevation(self):
    pointsWithElevation = filter(lambda x: x.elevation != None, self.trackpointsList[0])
    if pointsWithElevation: # do we have some points with known elevation ?
      self.elevation = True
      self.routeInfo = {}
      # there we have the poinsts, that contain the highest, lowest, first and last point
      firstPoint = pointsWithElevation[0]
      lastPoint = pointsWithElevation[len(pointsWithElevation)-1]
      # now we use some lambdas, to find the lowest and highest point
      maxElevationPoint = (max(pointsWithElevation, key=lambda x: x.elevation))
      minElevationPoint = (min(pointsWithElevation, key=lambda x: x.elevation))
      # just the highest/lowest elevations in numerical form
      maxElevation = float(maxElevationPoint.elevation)
      minElevation = float(minElevationPoint.elevation)
      difference = maxElevation - minElevation
      middle = minElevation + (difference/2)
      firstElevation = float(firstPoint.elevation)
      lastElevation = float(lastPoint.elevation)
      """because there are many possible statiastics about a given route with elevation,
      we will store them in a disctionary, so new onec can be quickly added as needed"""
#      self.routeInfo['firstPoint'] = firstPoint
#      self.routeInfo['lastPoint'] = lastPoint
#      self.routeInfo['maxElevationPoint'] = maxElevationPoint
#      self.routeInfo['minElevationPoint'] = minElevationPoint
      self.routeInfo['maxElevation'] = maxElevation
      self.routeInfo['minElevation'] = minElevation
      self.routeInfo['middle'] = middle
      self.routeInfo['firstElevation'] = firstElevation
      self.routeInfo['lastElevation'] = lastElevation
    else:
      self.elevation = False

  def replaceFile(self):
    """
    we output the tree structure of the gpx xml back to the file
    this can also meen, that some info that we didnt load to the tree will be lost
    also atributes that were changed after the initial load will be written in the current (changed) state
    """
    f = open(self.filename, "w") # open the old file
    xmlTree = self.trackpointsList.export_gpx_file() # get the element tree
    xmlTree.write(f) # overwrite the old file with the new structure
    print "%s has been replaced by the current in memory version" % self.filename
    del self.cache[self.filename] # the file has been modified, so it must be cached again
    self.save() # save the cache to disk


  def getPerElev(self):
    self.perElevList = geo.perElevList(self.trackpointsList)



class CacheItem():
  """class representing a cache item"""
  def __init__(self, clusters, routeInfo=None, perElevList=None):
    self.clusters = clusters
    self.routeInfo = routeInfo
    self.perElevList = perElevList

class clusterOfPoints():
  """A basic class representing a cluster of nearby points."""
  def __init__(self, pointsList, centreX, centreY, radius):
    self.pointsList = pointsList # points in the cluster
    """coordinates of the circle encompasing all points"""
    self.centreX = centreX
    self.centreY = centreY
    self.radius = radius #radius of the circle


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
