#!/usr/bin/python
#----------------------------------------------------------------------------
# Handle option menus
#----------------------------------------------------------------------------
# Copyright 2008, Oliver White
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
import marshal
import os
import modrana_utils

def getModule(m,d,i):
  return(options(m,d,i))

class options(ranaModule):
  """Handle options"""
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.options = {}

    # profile folder
    modRanaProfileFolderName = '.modrana'
    userHomePath = os.getenv("HOME")
    self.profileFolderPath = os.path.join(userHomePath, modRanaProfileFolderName)
    # check the profile path and create the folders if necessary
    modrana_utils.createFolderPath(self.profileFolderPath)

    # load persistant options
    self.load()
    self.on = '<span color="green">ON</span>'
    self.off = '<span color="red">OFF</span>'

  def getProfilePath(self):
    """return path to the profile folder"""
    # check if it exists and create it if not
    modrana_utils.createFolderPath(self.profileFolderPath)
    return self.profileFolderPath

  def getOptionsFilePath(self):
    """return path to the options store filename"""
    # check if it exists and create it if not
    return os.path.join(self.getProfilePath(),"options.bin")

  def getCacheFolderPath(self):
    cacheFolderPath = os.path.join(self.getProfilePath(), "cache")
    modrana_utils.createFolderPath(cacheFolderPath)
    return cacheFolderPath

  def getTracklogsFolderPath(self):
    if self.dmod:
      if self.dmod.hasCustomTracklogFolderPath():
        return self.dmod.getCustomTracklogFolderPath()
      else:
        return os.path.join(self.getProfilePath(),"tracklogs")
    else:
      return os.path.join(self.getProfilePath(),"tracklogs")

  def _getCategoryID(self, id):
    return "opt_cat_%s" % id # get a standardized id

  def addCategory(self,name,inId,icon,actionPrefix="",actionSufix=""):
    """this metohod shuld be run only after menu module instance
    is vailable in self.menuModule and the options manu is clared,
    eq. has at least the escape button"""
    # firs we add the category button to the options
    id = self._getCategoryID(inId) # get a standardized id
    action="%sset:menu:%s%s" % (actionPrefix,id,actionSufix)
    self.menuModule.addItem('options', name, icon, action)
    # intilize menu for the new category menu
    self.menuModule.clearMenu(id,"set:menu:options")
    # as a convenience, return the id
    return inId

  def _getGroupId(self, catId, id):
    parrentId = self._getCategoryID(catId)
    return "%s_opt_group_%s" % (parrentId, id)
  
  def addGroup(self,name,id,parrentId,icon,actionPrefix="",actionSufix=""):
    """this method ads a new (empty) options group to category specified by
    catId, as a convenience feature, the id of the new group is returned"""
    catId = self._getCategoryID(parrentId)
    id = self._getGroupId(parrentId, id) # get a standardized id
    action="%sset:menu:%s%s" % (actionPrefix,id,actionSufix)
    self.menuModule.addItem(catId, name, icon, action)
    self.options[id] = ["set:menu:%s" % catId,0,[]]
    return id

  def addBoolOption(self, title, variable, group, default=None, action=None):
    on = self.on
    off = self.off
    if action:
      self.addOption(title,variable,((False,off,action),(True,on,action)),group,default)
    else:
      self.addOption(title,variable,((False,off),(True,on)),group,default)

  def addEditOption(self, title, variable, group, label="Edit variable", description=None):
    choices = {"type":"showAndEditVariable",
               "label": label,
               "description": description
              }
    self.addOption(title, variable, choices, group, None)

  def addOption(self, title, variable, choices, group, default=None):

    newOption = (title,variable, choices,group,default)
    if self.options.has_key(group):
      self.options[group][2].append(newOption)
    else:
      print "options: group %s does not exist, call addGroup to create it first" % group

  def removeOption(self, categoryId, groupId, variable):
    """remova an option given by group and variable name"""

    group = self._getGroupId(categoryId, groupId)

    if self.options.has_key(group):
      remove = lambda x:x[1]==variable
      self.options[group][2][:] = [x for x in self.options[group][2] if not remove(x)]
    else:
      print "options: group %s does not exist, so option with variable %s can not be removed" % (group,variable)

#  def optionExists(self, categoryId, groupId):
    
  def firstTime(self):
    """Create a load of options.  You can add your own options in here,
    or alternatively create them at runtime from your module's firstTime()
    function by calling addOption.  That would be best if your module is
    only occasionally used, this function is best if the option is likely
    to be needed in all installations"""
    self.menuModule = self.m.get("menu", None)
    self.menuModule.clearMenu("options")

    # shotcuts
    addCat = self.addCategory
    addGroup = self.addGroup
    addOpt = self.addOption
    addBoolOpt = self.addBoolOption

    # * the Map category *
    catMap = addCat("Map", "map", "map")

    # ** map layers
    group = addGroup("Map layers", "map_layers", catMap, "generic")
    tiles = self.m.get("mapTiles", None)
    if(tiles):
      tileOptions = [("","None")]
      layers = tiles.layers().items()
      layers.sort()
      for name,layer in layers:
        tileOptions.append((name, layer.get('label',name)))
      addOpt("Main map", "layer", tileOptions, group, "mapnik")


      # ** Overlay
      group = addGroup("Map overlay", "map_overlay", catMap, "generic")
      addBoolOpt("Map as overlay", "overlay", group, False)

      addOpt("Main map", "layer", tileOptions, group, "mapnik")
      addOpt("Background map", "layer2", tileOptions, group, "osma")

      addOpt("Transparency ratio:", "transpRatio",
              [("0.25,1","overlay:25%"),
              ("0.5,1","overlay:50%"),
              ("0.75,1","overlay:75%"),
              ("1,1","overlay:100%")],
               group,
               "0.5,1")

      # ** Rotation
      group = addGroup("Rotation", "map_rotation", catMap, "generic")
      addBoolOpt("Rotate map in direction of travel", "rotateMap", group, False)

      # ** Scaling
      group = addGroup("Scaling", "map_scaling", catMap, "generic")
      addOpt("Map scale", "mapScale",
                   [(1,"1X"),
                    (2,"2X"),
                    (4,"4X")],
                     group,
                     1)

      # ** centering
      group = addGroup("Centering", "centering", catMap, "generic")
      addBoolOpt("Centre map", "centred", group, True)

      addOpt("Centering shift", "posShiftDirection",
        [("down","shift down"),
         ("up","shift up"),
         ("left","shift left"),
         ("right","shift right"),
         (False,"don't shift")],
         group,
         "down")

      addOpt("Centering shift amount", "posShiftAmount",
        [(0.25,"25%"),
         (0.5,"50%"),
         (0.75,"75%"),
         (1.0,"edge of the screen")],
         group,
         0.75)

      changedMsg = "mapView:centeringDisableTresholdChanged"
      addOpt("Disable by dragging", "centeringDisableTreshold",
        [(2048,"normal drag - <i>default</i>",changedMsg),
         (15000,"long drag",changedMsg),
         (40000,"realy long drag",changedMsg),
         (80000,"extremely long drag",changedMsg),
         (False,self.off,changedMsg)],
         group,
         2048)

      # ** dragging
      group = addGroup("Dragging", "dragging", catMap, "generic")
      # check if we are on a powerful device or not and set the default accordingly
      if self.dmod.simpleMapDragging():
        defaultMode = "staticMapDrag"
      else:
        defaultMode = "default"

      addOpt("Map dragging", "mapDraggingMode",
        [("default","full redraw - <i>default</i>","mapView:dragModeChanged"),
         ("staticMapDrag","drag visible map - <i>fastest</i>", "mapView:dragModeChanged")],
         group,
         defaultMode)

      # ** tile storage
      group = addGroup("Tile storage", "tile_storage", catMap, "generic")
      addOpt("Tile storage", "tileStorageType",
                   [('files',"files (default, more space used)"),
                    ('sqlite',"sqlite (new, less space used)")],
                     group,
                     'files')
      addBoolOpt("Store downloaded tiles", "storeDownloadedTiles", group, True)

    # * the view category *
    catView = addCat("View", "view", "view")

    # ** GUI
    group = addGroup("GUI", "gui", catView, "generic")
    addOpt("Hide main buttons", "hideDelay",
                 [("never","never hide buttons"),
                  ("5","hide buttons after 5 seconds"),
                  ("10","hide buttons after 10 seconds"),
                  ("15","hide buttons after 15 seconds"),
                  ("30","hide buttons after 30 seconds"),
                  ("60","hide buttons after 1 minute"),
                  ("120", "hide buttons after 2 minutes")],
                   group,
                   "10")

    addOpt("GUI Rotation", "rotationMode",
                 [("auto","automatic","device:modeChanged"),
                  ("landscape","landscape","device:modeChanged"),
                  ("portrait","portrait","device:modeChanged")],
                   group,
                   "auto")


    # ** screen
    """only add if supported on device"""
    display = self.m.get('display', None)
    if display:
      if display.screenBlankingControlSupported():
        group = addGroup("Screen", "screen", catView, "generic")
        addOpt("Keep display ON", "screenBlankingMode",
        [("always", "always", "display:blankingModeChanged"),
         ("centred", "while centred", "display:blankingModeChanged"),
         ("moving", "while moving", "display:blankingModeChanged"),
         ("movingInFullscreen", "while moving in fullscreen", "display:blankingModeChanged"),
         ("fullscreen", "while in fullscreen", "display:blankingModeChanged"),
         ("gpsFix", "while there is a GPS fix", "display:blankingModeChanged"), #TODO: while there is actually a GPS lock
         ("never", "never", "display:blankingModeChanged")],
         group,
         "always")
      if display.usesDashboard():
        addBoolOpt("Redraw when on dashboard", "redrawOnDashboard", group, False)

      # ** themes
      icons = self.m.get('icons', None)
      if icons:
        group = addGroup("Themes", "themes", catView, "generic")
        defaultTheme = icons.defaultTheme
        themeList = icons.getThemeList()
        # check if current theme exists
        currentTheme = self.get('currentTheme', None)
        if currentTheme != None:
          if currentTheme not in themeList:
            self.set('currentTheme', defaultTheme) # theme not valid, reset to default

        themeChangedMessage = "icons:themeChanged"
        nameValueList = map(lambda x: (x,x,themeChangedMessage), themeList)
        
        addOpt("Current theme", "currentTheme",
        nameValueList,
         group,
         defaultTheme)


    # ** units
    group = addGroup("formats#Units and", "units", catView, "generic")
    addOpt("Units", "unitType",
                 [("km","use kilometers"),
                  ("mile", "use miles")],
                   group,
                   "km")

    addOpt("Time format", "currentTimeFormat",
                 [("24h","24 hours"),
                  ("12h", "12 hours")],
                   group,
                   "24h")

    # ** menus
    group = addGroup("Menus", "menus", catView, "generic")
    addOpt("Listable menu rows", "listableMenuRows",
                 [(2,"2 rows"),
                  (3,"3 rows"),
                  (4,"4 rows"),
                  (5,"5 rows"),
                  (6,"6 rows")],
                   group,
                   4)


    if self.dmod.hasButtons():
      # TODO: change this once there are more options for key shortcuts
      # * the Keys category *
      catKeys = addCat("Keys", "keys", "keys")
      # * Device buttons
      group = addGroup("Device buttons", "device_buttons", catKeys, "n900")
      if self.dmod.hasVolumeKeys():
        addBoolOpt("Use volume keys for zooming", "useVolumeKeys", group, True, "device:updateKeys")


    # * the Navigation category
    catNavigation = addCat("Navigation", "navigation", "navigation")

    # * turn by turn navigation
    group = addGroup("Turn by turn", "turn_by_turn", catNavigation, "generic")

    addOpt("Autostart navigation", "autostartNavigationDefaultOnAutoselectTurn",
      [('disabled',"OFF"),
       ('enabled',"ON")],
       group,
       'enabled')

    addOpt("Make final turn announcement at", "pointReachedDistance",
      [(10,"10 m"),
       (20,"20 m"),
       (30,"30 m"),
       (60,"60 m"),
       (100,"100 m"),
       (200,"200 m"),
       (300,"300 m"),
       (500,"500 m")],
       group,
       30)

    addOpt("Announce turns at least this far ahead", "minAnnounceDistance",
      [(10,"10 m"),
       (20,"20 m"),
       (30,"30 m"),
       (60,"60 m"),
       (100,"100 m"),
       (200,"200 m"),
       (300,"300 m"),
       (500,"500 m")],
       group,
       100)

    addOpt("Announce turns at least this long ahead", "minAnnounceTime",
      [(5,"5 s"),
       (10,"10 s"),
       (20,"20 s"),
       (30,"30 s"),
       (45,"45 s"),
       (60,"60 s"),
       (90,"90 s")],
       group,
       10)

    # Note: actual values are in m/s, accurate to 2 decimal places.  We
    # store them as strings so lookup will work reliably.
    addOpt("Increase turn announcement time above", "minAnnounceSpeed",
      [("5.56","20 km/h (12 mph)"),
       ("8.33","30 km/h (20 mph)"),
       ("11.11","40 km/h (25 mph)"),
       ("13.89","50 km/h (30 mph)"),
       ("22.22","80 km/h (50 mph)"),
       ("27.78","100 km/h (60 mph)")],
       group,
       "13.89")

    # Note: actual values are in m/s, accurate to 2 decimal places.  We
    # store them as strings so lookup will work reliably.
    addOpt("Constant turn announcement time above", "maxAnnounceSpeed",
      [("13.89","50 km/h (30 mph)"),
       ("22.22","80 km/h (50 mph)"),
       ("27.78","100 km/h (60 mph)"),
       ("33.33","120 km/h (75 mph)"),
       ("44.44","160 km/h (100 mph)")],
       group,
       "27.78")

    addOpt("Maximum turn announcement time", "maxAnnounceTime",
      [(20,"20 s"),
       (30,"30 s"),
       (45,"45 s"),
       (60,"60 s"),
       (90,"90 s"),
       (120,"120 s")],
       group,
       60)

    # Note: these are exponents, stored as strings so lookup will work reliably.
    addOpt("Announcment time increase type", "announcePower",
      [("1.0","Linear with speed"),
       ("0.5","Very quickly, then linear"),
       ("0.75","Quickly, then linear"),
       ("1.5","Slowly, then linear"),
       ("2.0","Quite slowly, then linear"),
       ("4.0","Very slowly, then quite fast")],
       group,
       "2.0")


    # * navigation language
    group = addGroup("Language", "tbt_language", catNavigation, "generic")

    # in the first string: first one goes to espeak, the seccond part goes to Google
    directionsLanguages =[('ca ca', 'Catalan'),
                          ('zh-yue zh-TW', 'Chinese(Cantonese)'),
                          ('zh zh-CN', 'Chinese(Mandarin)'),
                          ('hr hr', 'Croatian'),
                          ('cs cs', 'Czech'),
                          ('nl nl', 'Dutch'),
                          ('en en', 'English'),
                          ('fi fi', 'Finnish'),
                          ('fr fr', 'French'),
                          ('de de', 'German'),
                          ('el el', 'Greek'),
                          ('hi hi', 'Hindi'),
                          ('hu hu', 'Hungarian'),
                          ('id id', 'Indonesian'),
                          ('it it', 'Italian'),
                          ('lv lv', 'Latvian'),
                          ('no no', 'Norwegian'),
                          ('pl pl', 'Polish'),
                          ('pt pt-BR', 'Portuguese(Brazil)'),
                          ('pt-pt pt-PT', 'Portuguese(European)'),
                          ('ro ro', 'Romanian'),
                          ('ru ru', 'Russian'),
                          ('sr sr', 'Serbian'),
                          ('sk sk', 'Slovak'),
                          ('es es', 'Spanish'),
                          ('ta ta', 'Tamil'),
                          ('tr tr', 'Turkish'),
                          ('vi vi', 'Vietnamese')]

    addOpt("Language for directions", 'directionsLanguage',
         directionsLanguages,
         group,
         "en en") # TODO: use locale for default language ?

    addOpt("read Cyrillic with", "voiceNavigationCyrillicVoice",
      [('ru',"Russian voice"),
       (False,"current voice")],
       group,
       'ru')


    # ** online routing submenu
    group = addGroup("Online routing", "online_routing", catNavigation, "generic")
    addBoolOpt("Avoid major highways ", "routingAvoidHighways", group, False)

    addBoolOpt("Avoid toll roads", "routingAvoidToll", group, False)

    # * the POI category
    catPOI = addCat("POI", "poi", "opt_poi")

    # ** POI storage
    group = addGroup("POI storage", "poi_storage", catPOI, "generic")
    addOpt("POI database", "POIDBFilename",
      [("poi.db","shared with Mappero (EXPERIMENTAL)","storePOI:reconnectToDb"),
       ("modrana_poi.db","modRana only (default)", "storePOI:reconnectToDb")],
       group,
       "modrana_poi.db")

    """ExportPOIDatabaseToCSV is just a dummy value,
       we just need to send a dump message to storePOI"""
    addOpt("Export POI Database to CSV", "EportPOIDatabaseToCSV",
      [("dump","click to export","storePOI:dumpToCSV"),
       ("dump","click to export","storePOI:dumpToCSV")],
       group,
       "dump")

    # ** online POI search
    group = addGroup("Online search", "poi_online", catPOI, "generic")
    addOpt("Google local search ordering", "GLSOrdering",
      [("default","ordering from Google"),
       ("distance", "order by distance")
      ],
       group,
       "default")

    addOpt("Google local search results", "GLSResults",
      [("8","max 8 results"),
       ("16", "max 16 results"),
       ("32", "max 32 results")],
       group,
       "8")


    addOpt("Google local search captions", "drawGLSResultCaptions",
      [("True","draw captions"),
       ("False", "dont draw captions")],
       group,
       "True")

    # * the Location category *
    catLocation = addCat("Location", "location", "gps_satellite")

    # ** GPS
    group = addGroup("GPS", "gps", catLocation, "generic")
    addBoolOpt("GPS", "GPSEnabled", group, True, "location:checkGPSEnabled")
    if self.dmod.locationType() == 'gpsd':
      knots = "knots per second"
      meters = "meters per second"
      if self.device == 'neo':
        knots = "knots per second (old SHR)"
        meters = "meters per second (new SHR)"
      addOpt("GPSD reports speed in","gpsdSpeedUnit",
      [('knotsPerSecond', knots),
       ('metersPerSecond', meters)],
       group,
       'knotsPerSecond')

    # * the Network category *
    catNetwork = addCat("Network", "network", "network")
    # * network *
    group = addGroup("Network usage", "network_usage", catNetwork, "generic")
    addOpt("Network", "network",
#      [("off","No use of network"),
      [("minimal", "Only for important data"),
       ("full", "Unlimited use of network")],
       group,
       "full")

    addOpt("Max nr. of threads for tile auto-download","maxAutoDownloadThreads2",
      [(5, "5"),
       (10, "10 (default)"),
       (20, "20"),
       (30, "30"),
       (40, "40"),
       (50, "50")],
       group,
       10)

    # * the Sound category *
    catSound = addCat("Sound", "sound", "sound")
    # * sound output
    group = addGroup("Sound output", "sound_output", catSound, "sound")

    addBoolOpt("Application wide sound output", "soundEnabled", group, True)

    # * espeak group
    group = addGroup("Voice", "voice_out", catSound, "espeak")

    addOpt("Voice parameters","voiceParameters",
      [("auto", "<b>automatic</b>","ms:options:espeakParams:auto"),
       ("manual", "<b>manual</b>", "ms:options:espeakParams:manual")],
       group,
       "auto")

    if self.get('voiceParameters', None) == "manual":
      self._updateVoiceManual('add')

       

#    addOpt("Network", "threadedDownload",
##      [("off","No use of network"),
#      [("True", "Use threads for download"),
#       ("False", "Dont use threads for download")],
#       "network",
#       "on")

#    addBoolOpt("Logging", "logging", "logging", True)
#    options = []
#    for i in (1,2,5,10,20,40,60):
#      options.append((i, "%d sec" % i))
#    addOpt("Frequency", "log_period", options, "logging", 2)

#    addBoolOpt("Vector maps", "vmap", "map", True)


#             [("0.5,0.5","over:50%,back:50%"),
#              ("0.25,0.75","over:25%,back:75%"),
#              ("0.75,0.25","over:75%,back:50%")],
#               "map",
#               "0.5,0.5")



#    addBoolOpt("Old tracklogs", "old_tracklogs", "map", False)
#    addBoolOpt("Latest tracklog", "tracklog", "map", True)

    # * the Debug category
    catDebug = addCat("Debug", "debug", "debug")

    # ** redraw
    group = addGroup("Redrawing", "redrawing", catDebug, "generic")
    addBoolOpt("Print redraw time to terminal", "showRedrawTime", group, False, "display:checkShowRedrawTime")
    # ** logging
    group = addGroup("Logging", "logging", catDebug, "generic")
    addBoolOpt("Log modRana stdout to file", "loggingStatus", group, False, "log:checkLoggingStatus")
    # ** tiles
    group = addGroup("Tiles", "tiles", catDebug, "generic")
    addBoolOpt("Print tile cache status to terminal", "reportTileCachStatus", group, False)
    addBoolOpt("Tile loading status to terminal", "tileLoadingDebug", group, False)
    addBoolOpt("Redraw screen once a new tile is loaded", "tileLoadedRedraw", group, True)
    addBoolOpt("Remove dups berofe batch dl", "checkTiles", group, False)
    # ** tracklog drawing
    group = addGroup("Tracklogs", "tracklogs", catDebug, "generic")
    addBoolOpt("Debug circles", "debugCircles", group, False)
    addBoolOpt("Debug squares", "debugSquares", group, False)
    # ** navigation
    group = self.addGroup("Navigation", "navigation", catDebug, "generic")
    addBoolOpt("Print Turn-By-Turn triggers", "debugTbT", group, False)
    # ** gps
    group = self.addGroup("GPS", "gps", catDebug, "generic")
    addBoolOpt("Show N900 GPS-fix", "n900GPSDebug", group, False)



#    addOpt("Tracklogs", "showTracklog",
#    [(False, "Dont draw tracklogs"),
#     ("simple", "Draw simple tracklogs")],
#     "view",
#     False)
    self._setUndefinedToDefault()

  def _setUndefinedToDefault(self):
    # Set all undefined options to default values
    for category,options in self.options.items():
      for option in options[2]:
        (title,variable,choices,category,default) = option
        if(default != None):
          if(not self.d.has_key(variable)):
            self.set(variable, default)


  def save(self):
    print "options: saving options"
    try:
      f = open(self.getOptionsFilePath(), "w")
      marshal.dump(self.d, f)
      f.close()
      print "options: successfully saved"
    except IOError:
      print "Can't save options"

  def load(self):
    try:
      f = open(self.getOptionsFilePath(), "r")
      newData = marshal.load(f)
      f.close()
      if 'tileFolder' in newData: #TODO: do this more elegantly
        del newData['tileFolder']
      if 'tracklogFolder' in newData: #TODO: do this more elegantly
        del newData['tracklogFolder']
      for k,v in newData.items():
        self.set(k,v)
    except Exception, e:
      print "options: exception while loading saved options:\n%s" % e
      #TODO: a yes/no dialog for clearing (renaming with timestamp :) the corrupted options file (options.bin)
      self.sendMessage('ml:notification:m:Loading saved options failed;7')

    self.overrideOptions()

  def overrideOptions(self):
    """
    without this, there would not be any projcetion values at start,
    becuase modRana does not know, what part of the map to show
    """
    self.set('centred', True) # set centering to True at start to get setView to run
    self.set('editBatchMenuActive', False)

  
  def handleMessage(self, message, type, args):
    if type=="ml" and message=="scroll":
      (direction,menuName) = args
      index = self.options[menuName][1]
      maxIndex = len(self.options[menuName][2])-1
      if direction == "up" and index > 0:
        newIndex = index - 1
        self.options[menuName][1] = newIndex
      elif direction == "down" and index < maxIndex:
        newIndex = index + 1
        self.options[menuName][1] = newIndex
    elif(message == "save"):
      self.save()
    elif type=="ms" and message == "espeakParams":
      # switch between espeak parameter modes
      if args == "manual":
        self._updateVoiceManual("remove")
      elif args == "auto":
        self._updateVoiceManual("add")

    elif type == "ml" and message == "editVariable":
      (variable, label, description) = args
      initialText = self.get(variable, "")
      entry = self.m.get('textEntry', None)
      if entry:
        key = "editVariable_%s" % variable
        entry.entryBox(self,key, label, initialText, description)

  def _updateVoiceManual(self, action):
    """add or remove custom voce parameters option items"""

    if action == "add":
      groupId = self._getGroupId("sound", "voice_out")
      description="<b>Note:</b> <tt>%language%</tt> will be replaced by current language code, <tt>%message%</tt> will be replaced by the message and <tt>%qmessage%</tt> will be replaced by the message in quotes"

      self.addEditOption("Edit voice string", "voiceString", groupId, "Edit voice string", description=description)

      message = "ms:voice:resetStringToDefault:espeak"
      self.addOption("Reset voice string with <b>Espeak</b> default", "placeholder",
      [("foo","<i>click to use this default</i>",message)],
       groupId,
       "foo")

    elif action == "remove":
      self.removeOption("sound", "voice_out", "voiceString")
      self.removeOption("sound", "voice_out", "placeholder")

  def handleTextEntryResult(self, key, result):
    (type, variable) = key.split("_", 1)
    if type == "editVariable":
      print "editing variable: %s with: %s" % (variable, result)
      self.set(variable,result)

  def drawMenu(self, cr, menuName):
    """Draw menus"""
    if(menuName[0:5] != "opt_c"):
      return
    if(not self.options.has_key(menuName)):
      return
    
    # Find the screen
    if not self.d.has_key('viewport'):
      return
   
    if(self.menuModule):
      
      # elements allocation
      (e1,e2,e3,e4,alloc) = self.menuModule.threePlusOneMenuCoords()
      (x1,y1) = e1
      (x2,y2) = e2
      (x3,y3) = e3
      (x4,y4) = e4
      (w1,h1,dx,dy) = alloc

      (cancelButtonAction, firstItemIndex, options) = self.options[menuName]

      # Top row:
      # * parent menu
      timeout = self.modrana.msLongPress
      self.menuModule.drawButton(cr, x1, y1, dx, dy, "", "up", cancelButtonAction, timedAction=(timeout,"set:menu:None"))
      # * scroll up
      self.menuModule.drawButton(cr, x2, y2, dx, dy, "", "up_list", "ml:options:scroll:up;%s" % menuName)
      # * scroll down
      self.menuModule.drawButton(cr, x3, y3, dx, dy, "", "down_list", "ml:options:scroll:down;%s" % menuName)

      # One option per row
      for row in (0,1,2):
        index = firstItemIndex + row
        numItems = len(options)
        cAction = None
        if(0 <= index < numItems):
          (title,variable,choices,category,default) = options[index]
          # What's it set to currently?
          value = self.get(variable, None)

          # Lookup the description of the currently-selected choice.
          # (if any, use str(value) if it doesn't match any defined options)
          # Also lookup the _next_ choice in the list, because that's what
          # we will set the option to if it's clicked

          if type(choices) is dict:
            optionType = choices["type"]
            label = choices["label"]
            description = choices["description"]

            if optionType == "showAndEditVariable":
              valueDescription = self.get(variable, "variable is not set yet")
              valueDescription = "<tt><b>%s</b></tt>" % valueDescription
              payload = "%s;%s;%s" % (variable, label, description)
              onClick = "ml:options:editVariable:%s|set:needRedraw:True" % payload

          else: # toggle button

            nextChoice = choices[0]
            valueDescription = str(value)
            useNext = False
            for c in choices:
              (cVal, cName) = (c[0],c[1])
              if(useNext):
                nextChoice = c
                useNext = False
              if(str(value) == str(cVal)):
                valueDescription = cName
                useNext = True
                if len(c) == 3:
                  cAction = c[2]

            # What should happen if this option is clicked -
            # set the associated option to the next value in sequence
            onClick = "set:%s:%s" % (variable, str(nextChoice[0]))
            if cAction:
              onClick += "|%s" % cAction
            onClick += "|options:save"
            onClick += "|set:needRedraw:1"

          y = y4 + (row) * dy
          w = w1 - (x4-x1)
          
          # Draw background and make clickable
          self.menuModule.drawButton(cr,
            x4,
            y,
            w,
            dy,
            None,
            "generic", # background for a 3x1 icon
            onClick)

          border = 20

          # 1st line: option name
          self.menuModule.showText(cr, title+":", x4+border, y+border, w-2*border)

          # 2nd line: current value
          self.menuModule.showText(cr, valueDescription, x4 + 0.15 * w, y + 0.6 * dy, w * 0.85 - border)

          # in corner: row number
          self.menuModule.showText(cr, "%d/%d" % (index+1, numItems), x4+0.85*w, y+3*border, w * 0.15 - border, 20)

#  def checkProfilePath(self):
#    """check if the profile folder exists, try to create it if not"""
#    if os.path.exists(self.getProfilePath()):
#      return True
#    else:
#      try:
#        os.makedirs(self.profileFolderPath)
#        print "creating profile folder in: %s" % self.profileFolderPath
#        return True
#      except Exception, e:
#        print "options:Creating profile folder in path: %s failed:\n%s" % (self.profileFolderPath, e)
#        return False

  def shutdown(self):
    """save the dictionary on exit"""
    self.save()

if(__name__ == "__main__"):
  a = options({},{'viewport':(0,0,600,800)})
  a.firstTime()
