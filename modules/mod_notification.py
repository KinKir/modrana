from __future__ import with_statement # for python 2.5
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# This module provides notification support.
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
import threading
from core.backports import six
from modules.base_module import RanaModule
import time

from core.signal import Signal
from core.threads import threadMgr
from core import gs


def getModule(m, d, i):
    return Notification(m, d, i)


class Notification(RanaModule):
    """This module provides notification support."""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.notificationText = ""
        self.timeout = 5
        self.position = 'middle'
        self.expirationTimestamp = time.time()
        self.draw = False
        self.redrawn = None
        self.wipOverlayEnabled = Signal()
        self._showWorkInProgressOverlay = False
        self.workStartTimestamp = None
        self._wipOverlayText = ""
        # this indicates if the notification about
        # background processing should be shown
        self._tasks = {}
        self._tasksLock = threading.RLock()

        ## for WiP overlay testing
        #self._tasks = {
        #  "foo" : ("foo", None),
        #  "bar" : ("bar", None),
        #  "baz" : ("baz", None)
        #}

        # key is an unique task name (unique for each instance of a task)
        # and value is a (status, progress) tuple
        self.tasksChanged = Signal()

        # connect thread manager signals to task status changes
        threadMgr.threadStatusChanged.connect(self.setTaskStatus)
        threadMgr.threadProgressChanged.connect(self.setTaskProgress)
        threadMgr.threadRemoved.connect(self.removeTask)

        # also with GTK GUI, assure screen is redrawn properly
        # when WiP overlay changes
        if gs.GUIString == "GTK":
            self.wipOverlayEnabled.connect(self._doRefresh)
            self.tasksChanged.connect(self._doRefresh)

    def _doRefresh(self, ignore):
        self.set('needRedraw', True)

    def handleMessage(self, message, messageType, args):
        """the first part is the message, that will be displayed,
           there can also by some parameters, delimited by #
           NEW: you can also use a message list for the notification
                first goes 'm', the message and then the timeout in seconds


           EXAMPLE: ml:notification:m:Hello world!;5
           """

        if messageType == 'ml' and message == 'm':
            # advanced message list based notification
            if args:
                timeout = self.timeout
                if len(args) >= 2:
                    timeout = float(args[1])
                messageText = args[0]
                self.handleNotification(messageText, timeout)

        elif messageType == 'ml' and message == 'workInProgressOverlay':
            if args:
                if args[0] == "enable":
                    self._startWorkInProgressOverlay()
                if args[0] == "disable":
                    self._stopWorkInProgressOverlay()

        elif messageType and message == "cancelTask":
            if args:
                self.cancelTask(args)

        else:
            parameterList = message.split('#')
            if len(parameterList) >= 2:
                messageText = parameterList[0]
                timeout = self.timeout
                self.handleNotification(messageText, timeout)
                if len(parameterList) == 2:
                    try:
                        timeout = int(parameterList[1]) # override the default timeout
                    except Exception:
                        self.log.exception("wrong timeout, using default 5 seconds")
                self.handleNotification(messageText, timeout)
            else:
                self.log.error("wrong message: %s", message)

    def setTaskStatus(self, taskName, status):
        """Set textual status of the given WiP task

        :param taskName: task to modify
        :type taskName: str
        :param status: textual task status
        :type status: str
        """
        with self._tasksLock:
            oldStatus, progress = self._tasks.get(taskName, (None, None))
            # replace the task with updated one
            self._tasks[taskName] = (status, progress)
        self.tasksChanged(self._tasks)
        if status:
            self._startWorkInProgressOverlay()

    def setTaskProgress(self, taskName, progress):
        """Set numeric progress of the given WiP task

        :param taskName: task to modify
        :type taskName: str
        :param progress: numeric task progress in the range of 0.0 to 1.0
        :type progress: float
        """
        with self._tasksLock:
            status, oldProgress = self._tasks.get(taskName, (None, None))
            # replace the task with updated one
            self._tasks[taskName] = (status, progress)
        self.tasksChanged(self._tasks)
        if progress is not None:
            self._startWorkInProgressOverlay()

    def removeTask(self, taskName):
        """Remove given task from WiP tracking

        :param taskName: name of the task to cancel
        :type taskName: str
        """
        with self._tasksLock:
            try:
                del self._tasks[taskName]
                self.tasksChanged(self._tasks)
            except KeyError:
                self.log.error("error, can't remove unknown task: %s", taskName)
        if self._tasks == {}:
            self._stopWorkInProgressOverlay()

    def cancelTask(self, taskName):
        """Cancel a task - this both cancels the callback for the thread
        handling the task and removes the task from tracking

        :param taskName: task to cancel
        :type taskName: str
        """
        threadMgr.cancel_thread(taskName)
        # and finally stop tracking the task
        self.removeTask(taskName)
        self.log.info("task %s has been cancelled", taskName)

    def _startWorkInProgressOverlay(self):
        """start background work notification"""
        if not self._showWorkInProgressOverlay:
            self._showWorkInProgressOverlay = True
            self.workStartTimestamp = time.time()
            self.wipOverlayEnabled(True)

    def _stopWorkInProgressOverlay(self):
        """stop background work notification"""
        self._showWorkInProgressOverlay = False
        self.wipOverlayEnabled(False)

    #def getWorkInProgressOverlayText(self):
    #  elapsedSeconds = int(time.time() - self.workStartTimestamp)
    #  if elapsedSeconds: # 0s doesnt look very good :)
    #    return "%s %d s" % (self.wipOverlayText, elapsedSeconds)
    #  else:
    #    return self.wipOverlayText

    def drawWorkInProgressOverlay(self, cr):
        proj = self.m.get('projection', None) # we also need the projection module
        viewport = self.get('viewport', None)
        menus = self.m.get('menu', None)
        with self._tasksLock:
            if self._tasks and proj and viewport and menus:
                # we need to have both the viewport and projection modules available
                # also the menu module for the text

                taskCount = len(self._tasks)

                # background
                cr.set_source_rgba(0.5, 0.5, 1, 0.5)
                (sx, sy, w, h) = viewport
                itemHeight = h * 0.2
                (bx, by, bw, bh) = (0, 0, w, itemHeight * taskCount)
                cr.rectangle(bx, by, bw, bh)
                cr.fill()

                taskIndex = 0
                for taskName, taskState in six.iteritems(self._tasks):
                    # cancel button coordinates
                    cbdx = min(w, h) / 5.0
                    cbdy = cbdx
                    cbx1 = (sx + w) - cbdx
                    cby1 = sy + cbdy * taskIndex

                    # cancel button
                    self.drawCancelButton(cr, coords=(cbx1, cby1, cbdx, cbdy), taskName=taskName)

                    status, progress = taskState

                    # draw the text
                    border = min(w / 20.0, h / 20.0)
                    menus.showText(cr, status, bx + border, by + border + itemHeight * taskIndex,
                                   bw - 2 * border - cbdx, 30, "white")
                    taskIndex += 1

    def drawCancelButton(self, cr, coords=None, taskName=None):
        """draw the cancel button
        TODO: this and the other context buttons should be moved to a separate module,
        named contextMenu or something in the same style"""
        menus = self.m.get('menu', None)
        click = self.m.get('clickHandler', None)
        if menus and click:
            if coords: #use the provided coords
                (x1, y1, dx, dy) = coords
            else: # use the bottom right corner
                (x, y, w, h) = self.get('viewport')
                dx = min(w, h) / 5.0
                dy = dx
                x1 = (x + w) - dx
                y1 = y
                # the cancel button sends a cancel message to onlineServices
            # to disable currently running operation
            menus.drawButton(cr, x1, y1, dx, dy, '#<span foreground="red">cancel</span>', "generic:;0.5;;0.5;;", '')
            if taskName:
                message = "ms:notification:cancelTask:%s" % taskName
                click.registerXYWH(x1, y1, dx, dy, message, layer=2)
            else:
                click.registerXYWH(x1, y1, dx, dy, "onlineServices:cancelOperation", layer=2)


    def handleNotification(self, message, timeout=None, icon=""):
        """Handle a notification request

        As on some platforms, such as on Maemo 5 Fremantle, system
        notifications should only be triggered from the main thread,
        we pass the notification request to the main loop, to be
        dispatched once the main GUI thread becomes idle
        """

        cron = self.m.get("cron", None)
        if cron:
            cron.addIdle(self._dispatchNotification, [message, timeout, icon])

    def _dispatchNotification(self, message, timeout, icon):
        """Dispatch a notification using the most optimal method for the
        current device & platform combination

        NOTE: This method should be run from the main thread as there might be
        issues otherwise (such as the "Xlib: unexpected async reply" errors).
        """
        # TODO: icon support
        if timeout is None:
            timeout = self.timeout

        self.log.info("message: %s, timeout: %s", message, timeout)

        # if some module sends a notification during init, the device module might not be loaded yet
        if self.modrana.dmod and self.modrana.gui:
            if self.dmod.hasNotificationSupport(): # use platform specific method
                self.log.info("notification@dmod: message: %s, timeout: %s", message, timeout)
                self.dmod.notify(message, int(timeout) * 1000)
            elif self.modrana.gui.hasNotificationSupport():
                self.modrana.gui.notify(message, timeout, icon)
            else:
                self._startCustomNotification(message, timeout, icon)
        else:
            self._startCustomNotification(message, timeout, icon)

    def _startCustomNotification(self, message, timeout, icon=""):
        self.log.info("message: %s, timeout: %s", message, timeout)
        self.position = 'middle'
        self.notificationText = message
        self.expirationTimestamp = time.time() + timeout
        self.draw = True # enable drawing of notifications
        self.set('needRedraw', True) # make sure the notification is displayed

    def drawMasterOverlay(self, cr):
        """this function is called by the menu module, both in map mode and menu mode
        -> its bit of a hack, but we can """
        self.drawNotification(cr)
        if self._showWorkInProgressOverlay:
            self.drawWorkInProgressOverlay(cr)

    def drawNotification(self, cr):
        """Draw the notifications on the screen on top of everything."""
        if time.time() <= self.expirationTimestamp:
            proj = self.m.get('projection', None)
            (x1, y1) = proj.screenPos(0.5, 0.5) # middle fo the screen
            cr.set_font_size(30)
            text = self.notificationText
            cr.set_source_rgba(0, 0, 1, 0.45) # transparent blue
            extents = cr.text_extents(text)
            (w, h) = (extents[2], extents[3])
            (x, y) = (x1 - w / 2.0, y1 - h / 2.0)
            cr.set_line_width(2)
            cr.set_source_rgba(0, 0, 1, 0.45) # transparent blue
            (rx, ry, rw, rh) = (x - 0.25 * w, y - h * 1.5, w * 1.5, (h * 2))
            cr.rectangle(rx, ry, rw, rh) # create the transparent background rectangle
            cr.fill()
            cr.set_source_rgba(1, 1, 1, 0.95) # slightly transparent white
            cr.move_to(x + 10, y)
            cr.show_text(text) # show the transparent notification text
            cr.stroke()
            cr.fill()
        else:
            self.draw = False # we are finished, disable drawing notifications
