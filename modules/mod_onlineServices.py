#!/usr/bin/python
#----------------------------------------------------------------------------
# Module for communication with various online services.
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
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
from base_module import ranaModule
import urllib
import googlemaps
import threading
import time

def getModule(m,d):
  return(onlineServices(m,d))

class onlineServices(ranaModule):
  """Module for communication with various online services."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.routingThread = None
    self.drawOverlay = False
    self.workStartTimestamp = None # for show elapsed time since the online request has been sent

  def handleMessage(self, message, type, args):
    if message == "cancelOperation":
      """this message is sent when the user presses the "cancel search" button
         it should:
         * make sure there are no results returned after the button is pressed
         * remove the cancel button and the "working" overlay """
      self.stop()
      
  def elevFromGeonames(self, lat, lon):
    """get elevation in meters for the specified latitude and longitude from geonames"""
    url = 'http://ws.geonames.org/srtm3?lat=%f&lng=%f' % (lat,lon)
    try:
      query = urllib.urlopen(url)
    except:
      "onlineServices: getting elevation from geonames retuned an error"
      return 0
    return query.read()

  def elevFromGeonamesBatch(self, latLonList):
    """
    get elevation in meters for the specified latitude and longitude from geonames
    it is possible to ask for up to 20 coordinates at once
    """
    maxCoordinates = 20 #geonames only allows 20 coordinates per query
    latLonElevList = []
    tempList = []
#    mainLength = len(latLonList)
    while len(latLonList) > 0:

      tempList = latLonList[0:maxCoordinates]
      latLonList = latLonList[maxCoordinates:len(latLonList)]

      lats = ""
      lons = ""
      for point in tempList:
        lats += "%f," % point[0]
        lons += "%f," % point[1]

# TODO: maybe add switching ?
#      url = 'http://ws.geonames.org/astergdem?lats=%s&lngs=%s' % (lats,lons)
      url = 'http://ws.geonames.org/srtm3?lats=%s&lngs=%s' % (lats,lons)
      try:
        query = urllib.urlopen(url)
      except:
        "onlineServices: getting elevation from geonames retuned an error"
        results = "0"
        for i in range(1, len(tempList)):
          results = results + " 0"
      try:
        results = query.read().split('\r\n')
        query.close()
      except:
        "onlineServices: elevation string from geonames has a wrong format"
        results = "0"
        for i in range(1, len(tempList)):
          results = results + " 0"

      index = 0
      for point in tempList: # add the results to the new list with elevation
        latLonElevList.append((point[0],point[1],int(results[index])))
        index = index +1

    return latLonElevList


  def getGmapsInstance(self):
    """get a google maps wrapper instance"""
    key = self.get('googleAPIKey', None)
    if key == None:
      print "onlineServices: a google API key is needed for using the google maps services"
      return None
    gmap = googlemaps.GoogleMaps(key)
    return gmap

  def googleLocalQuery(self, query):
    gmap = self.getGmapsInstance()
    numresults = int(self.get('GLSResults', 8))
    local = gmap.local_search(query, numresults)
    return local

  def googleLocalQueryLL(self, query, lat, lon):
    separator = " "
    LL = "%f,%f" % (lat,lon)
    queryWithLL = query + separator + LL
    local = self.googleLocalQuery(queryWithLL)
    return local



  def googleDirectionsAsync(self, start, destination, outputHandler, key):
    """a background running googledirections query
       outputHandler will be proided with the results + the specified key string"""
    self.routingThread = self.Worker(self, "onlineRouteLL", (start, destination), outputHandler, key)
    self.routingThread.daemon = True
    self.routingThread.start()

  def googleDirections(self ,start, destination):
    '''
    Get driving directions from Google.
    start and directions can be either coordinates tupples or address strings
    '''
    gmap = self.getGmapsInstance()

    otherOptions=""
    if self.get('routingAvoidHighways', False): # optionally avoid highways
      otherOptions = otherOptions + 'h'
    if self.get('routingAvoidToll', False): # optionally avoid toll roads
      otherOptions = otherOptions + 't'

    # respect travel mode
    mode = self.get('mode', None)
    if mode != None:
      type = ""
      if mode == 'cycle':
        type = "b"
      elif mode == 'foot':
        type = "w"
      elif mode == 'train' or mode == 'bus':
        type = 'r'

      parameters = type + otherOptions # combine type and aother parameters
      dir = {'dirflg': parameters}  # create a dictionary entry with all current parameters
      self.get('directionsLanguage', 'en en')
      # the google language code is the seccond part of this whitespace delimited string
      googleLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[1]
      dir['hl'] = googleLanguageCode

      try:
        directions = gmap.directions(start, destination, dir)
      except:
        print "onlineServices:Gdirections:bad response to travel mode:%s, using default" % mode
        try:
          directions = gmap.directions(start, destination)
        except Exception, e:
          if e.status == 604:
            print "onlineServices:Gdirections:ruting failed -> no route found" % e
            self.sendMessage("ml:notification:m:No route found;3")
          else:
            print "onlineServices:Gdirections:ruting failed with exception:\n%s" % e

          directions = []

    else:
      directions = gmap.directions(start, destination)

    return directions

  def googleDirectionsLL(self ,lat1, lon1, lat2, lon2):
    start = (lat1, lon1)
    destination = (lat2, lon2)
    return self.googleDirections(start, destination)

  def googleGeocode(self, adress):
    pass

  def googleReverseGeocode(self, lat, lon):
    gmap = self.getGmapsInstance()
    address = gmap.latlng_to_address(lat,lon)
    return address

  def enableOverlay(self):
    """enable the "working" overlay + set timestamp"""
    self.sendMessage('ml:notification:backgroundWorkNotify:enable|ms:route:cancelButton:enable')
    self.workStartTimestamp = time.time()

  def disableOverlay(self):
    """disable the "working" overlay + disable the timestamp"""
    self.sendMessage('ml:notification:backgroundWorkNotify:disable|ms:route:cancelButton:disable')
    self.workStartTimestamp = None

  def stop(self):
    """called either after the worker thread finishes or after pressing the cacnel button"""
    self.disableOverlay()
    self.routingThread.dontReturnResult()

  def drawOpInProgressOverlay(self,cr):
      message = self.routingThread.getStatusMessage()
      if self.workStartTimestamp:
        elapsedSeconds = int(time.time() - self.workStartTimestamp)
        if elapsedSeconds: # 0s doesnt look very good :)
          message = message + " %d s" % elapsedSeconds
      proj = self.m.get('projection', None) # we also need the projection module
      vport = self.get('viewport', None)
      if proj and vport:
        # we need to have the viewport and projection module available

        # background
        cr.set_source_rgba(0.5, 0.5, 1, 0.5)
        (sx,sy,w,h) = vport
        (bx,by,bw,bh) = (0,0,w,h*0.2)
        cr.rectangle(bx,by,bw,bh)
        cr.fill()

        menus = self.m.get('menu', None)
        border = min(w/20.0,h/20.0)
        menus.showText(cr, message, bx+border, by+border, bw-2*border,30, "white")

  class Worker(threading.Thread):
    """a worker thread for asynchronous online services access"""
    def __init__(self,callback, type, argsTupple, outputHandler, key):
      threading.Thread.__init__(self)
      self.callback = callback # should be a onlineServicess module instance
      self.type = type
      self.argsTupple = argsTupple
      self.outputHandler = outputHandler
      self.key = key # a key for the output handler
      self.statusMessage = ""
      self.returnResult = True
      print "onlineServices: worker initialized"
    def run(self):
      print "onlineServices: worker starting"

      if self.type == "onlineRoute" or self.type == "onlineRouteLL":
        if len(self.argsTupple) == 2:
          (start, destination) = self.argsTupple
          self.setStatusMessage("online routing in progress...")
          self.callback.enableOverlay()
          # get the route
          directions = self.getOnlineRoute(start,destination)

          if type == "onlineRouteLL":
            # reverse geocode the start and destination coordinates (for the info menu)
            (fromLat,fromLon) = start
            (toLat,toLon) = destination
            self.setStatusMessage("geocoding start")
            startAddress = self.reverseGeocode(fromLat,fromLon)
            self.setStatusMessage("geocoding destination")
            destinationAddress = self.reverseGeocode(toLat,toLon)
          else:
            startAddress = "start address unknown"
            destinationAddress = "destination address unknown"
          self.setStatusMessage("online routing done")
          # send the results to the output handler
          if self.returnResult: # check if our reulst is expected and should be returned to the oputpt handler
            self.outputHandler(self.key, (directions, startAddress, destinationAddress))
          print "onlineServices: worker finished"
          self.callback.stop()

    def getStatusMessage(self):
      return self.statusMessage
    def setStatusMessage(self, message):
      self.statusMessage = message

    def getOnlineRoute(self, start, destination):
      return self.callback.googleDirections(start, destination)

    def reverseGeocode(self, lat, lon):
      return self.callback.googleReverseGeocode(lat,lon)

    def dontReturnResult(self):
      self.returnResult = False

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
