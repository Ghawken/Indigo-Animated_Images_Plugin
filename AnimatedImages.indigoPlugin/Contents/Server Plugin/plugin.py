#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
import indigo
import sanic
from sanic import Sanic, response
from PIL import Image, ImageSequence
import io
import os
import logging

import traceback
import platform
import sys
from os import path
import datetime
import asyncio

from frame_server import ImageFrameServer

import threading

class IndigoLogHandler(logging.Handler):
    def __init__(self, display_name, level=logging.NOTSET):
        super().__init__(level)
        self.displayName = display_name

    def emit(self, record):
        """ not used by this class; must be called independently by indigo """
        logmessage = ""
        try:
            levelno = int(record.levelno)
            is_error = False
            is_exception = False
            if self.level <= levelno:  ## should display this..
                if record.exc_info !=None:
                    is_exception = True
                if levelno == 5:	# 5
                    logmessage = '({}:{}:{}): {}'.format(path.basename(record.pathname), record.funcName, record.lineno, record.getMessage())
                elif levelno == logging.DEBUG:	# 10
                    logmessage = '({}:{}:{}): {}'.format(path.basename(record.pathname), record.funcName, record.lineno, record.getMessage())
                elif levelno == logging.INFO:		# 20
                    logmessage = record.getMessage()
                elif levelno == logging.WARNING:	# 30
                    logmessage = record.getMessage()
                elif levelno == logging.ERROR:		# 40
                    logmessage = '({}: Function: {}  line: {}):    Error :  Message : {}'.format(path.basename(record.pathname), record.funcName, record.lineno, record.getMessage())
                    is_error = True
                if is_exception:
                    logmessage = '({}: Function: {}  line: {}):    Exception :  Message : {}'.format(path.basename(record.pathname), record.funcName, record.lineno, record.getMessage())
                    indigo.server.log(message=logmessage, type=self.displayName, isError=is_error, level=levelno)
                    if record.exc_info !=None:
                        etype,value,tb = record.exc_info
                        tb_string = "".join(traceback.format_tb(tb))
                        indigo.server.log(f"Traceback:\n{tb_string}", type=self.displayName, isError=is_error, level=levelno)
                        indigo.server.log(f"Error in plugin execution:\n\n{traceback.format_exc(30)}", type=self.displayName, isError=is_error, level=levelno)
                    indigo.server.log(f"\nExc_info: {record.exc_info} \nExc_Text: {record.exc_text} \nStack_info: {record.stack_info}",type=self.displayName, isError=is_error, level=levelno)
                    return
                indigo.server.log(message=logmessage, type=self.displayName, isError=is_error, level=levelno)
        except Exception as ex:
            indigo.server.log(f"Error in Logging: {ex}",type=self.displayName, isError=is_error, level=levelno)

################################################################################
class Plugin(indigo.PluginBase):
    ########################################
    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs):
        super().__init__(plugin_id, plugin_display_name, plugin_version, plugin_prefs)
        self.logger.debug("Initializing Frame Server Plugin.")

        ################################################################################
        # Setup Logging
        ################################################################################
        self.logger.setLevel(logging.DEBUG)
        try:
            self.logLevel = int(self.pluginPrefs["showDebugLevel"])
            self.fileloglevel = int(self.pluginPrefs["showDebugFileLevel"])
        except:
            self.logLevel = logging.INFO
            self.fileloglevel = logging.DEBUG

        self.logger.removeHandler(self.indigo_log_handler)

        self.indigo_log_handler = IndigoLogHandler(plugin_display_name, logging.INFO)
        ifmt = logging.Formatter("%(message)s")
        self.indigo_log_handler.setFormatter(ifmt)
        self.indigo_log_handler.setLevel(self.logLevel)
        self.logger.addHandler(self.indigo_log_handler)

        pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t%(levelname)s\t%(name)s.%(funcName)s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.plugin_file_handler.setFormatter(pfmt)
        self.plugin_file_handler.setLevel(self.fileloglevel)

        self.selected_region = plugin_prefs.get("region","")
        self.selected_country = plugin_prefs.get("country","")
        self.selected_lang = plugin_prefs.get("language","")
        self.selected_category = plugin_prefs.get("category","public")
        self.debug1 = plugin_prefs.get("debug1", False)


        system_version, product_version, longer_name = self.get_macos_version()
        self.logger.info("{0:=^130}".format(f" Initializing New Plugin Session for Plugin: {plugin_display_name} "))
        self.logger.info("{0:<30} {1}".format("Plugin name:", plugin_display_name))
        self.logger.info("{0:<30} {1}".format("Plugin version:", plugin_version))
        self.logger.info("{0:<30} {1}".format("Plugin ID:", plugin_id))
        self.logger.info("{0:<30} {1}".format("Indigo version:", indigo.server.version) )
        self.logger.info("{0:<30} {1}".format("System version:", f"{system_version} {longer_name}" ))
        self.logger.info("{0:<30} {1}".format("Product version:", product_version))
        self.logger.info("{0:<30} {1}".format("Silicon version:", str(platform.machine()) ))
        self.logger.info("{0:<30} {1}".format("Sanic Library version:", str(sanic.__version__)))
        self.logger.info("{0:<30} {1}".format("Python version:", sys.version.replace('\n', '')))
        self.logger.info("{0:<30} {1}".format("Python Directory:", sys.prefix.replace('\n', '')))

        self.debug1 = self.pluginPrefs.get('debug1', False)
        self.debug2 = self.pluginPrefs.get('debug2', False)
        self.logger.info(u"{0:=^130}".format(" End Initializing New Plugin  "))

        self.server_thread = None
        self.frame_server = ImageFrameServer(logger=self.logger)

    ########################################
    def get_macos_version(self):
        try:
            version, _, _ = platform.mac_ver()
            longer_version = platform.platform()
            self.logger.info(f"{version}")
            longer_name = self.get_macos_marketing_name(version)
            return version, longer_version, longer_name
        except:
            self.logger.debug("Exception:",exc_info=True)
            return "","",""

    def get_macos_marketing_name(self, version: str) -> str:
        """Return the marketing name for a given macOS version number."""
        versions = {
            "10.0": "Cheetah",
            "10.1": "Puma",
            "10.2": "Jaguar",
            "10.3": "Panther",
            "10.4": "Tiger",
            "10.5": "Leopard",
            "10.6": "Snow Leopard",
            "10.7": "Lion",
            "10.8": "Mountain Lion",
            "10.9": "Mavericks",
            "10.10": "Yosemite",
            "10.11": "El Capitan",
            "10.12": "Sierra",
            "10.13": "High Sierra",
            "10.14": "Mojave",
            "10.15": "Catalina",
            "11": "Big Sur",  # Just use the major version number for macOS 11+
            "12": "Monterey",
            "13": "Ventura",
            "14": "Sonoma",
        }
        major_version_parts = version.split(".")
        # If the version is "11" or later, use only the first number as the key
        if int(major_version_parts[0]) >= 11:
            major_version = major_version_parts[0]
        # For macOS "10.x" versions, use the first two numbers as the key
        else:
            major_version = ".".join(major_version_parts[:2])
        self.logger.debug(f"Major Version== {major_version}")
        return versions.get(major_version, f"Unknown macOS version for {version}")

    def startup(self):
        self.logger.debug("startup called")
        MAChome = os.path.expanduser("~") + "/"
        self.saveDirectory = MAChome + "Pictures/Indigo-AnimatedImages/"
        try:
            if not os.path.exists(self.saveDirectory):
                os.makedirs(self.saveDirectory)
        except:
            self.logger.error(f'Error Accessing Save Directory.{self.saveDirectory} ')
            pass

    def run_sanic_server(self):

        self.logger.debug("Within Run Sanic Server")
        app = Sanic("AnimatedImage")

        async def handle_gif_request(request, gif_name):
            # Since we're inside the class method, we can directly use self.frame_server
            if self.debug1:
                self.logger.debug(f"Handling GIF request {gif_name}")
            frame_data, content_type = await self.frame_server.get_next_frame(gif_name)
            return response.raw(frame_data, content_type=content_type)

        @app.middleware('request')
        async def add_custom_logging(request):
            if self.debug1:
                self.logger.debug(f"Received request for {request.path}")

        @app.exception(Exception)
        async def handle_exception(request, exception):
            if self.debug1:
                self.logger.debug(f"Exception occurred: {exception}", exc_info=False)

        try:
            # Now, adding the route without redundancy.
            app.add_route(handle_gif_request, '/<gif_name>', methods=['GET'])
            app.run(host="127.0.0.1", port=8405, debug=True, single_process=True, register_sys_signals=False )
            self.logger.debug("After App Run.")
        except:
            self.logger.exception("Exception in run sanic server:")

    def start_server_thread(self):
        if self.server_thread is None or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(target=self.run_sanic_server, args=(), daemon=True)
            self.server_thread.start()
            self.logger.debug("Sanic server thread started.")

    def shutdown(self):
        self.logger.debug("shutdown called")

        ########################################
    def updateVar(self, name, value):
        self.logger.debug(u'updatevar run.')
        if not ('Holiday' in indigo.variables.folders):
            # create folder
            folderId = indigo.variables.folder.create('Holiday')
            folder = folderId.id
        else:
            folder = indigo.variables.folders.getId('Holiday')

        if name not in indigo.variables:
            NewVar = indigo.variable.create(name, value=str(value).lower(), folder=folder)
        else:
            indigo.variable.updateValue(name, str(value).lower())
        return

    def runConcurrentThread(self: indigo.PluginBase) -> None:
        """
        If runConcurrentThread() is defined, then a new thread is automatically created
        and runConcurrentThread() is called in that thread after startup() has been called.

        runConcurrentThread() should loop forever and only return after self.stopThread
        becomes True. If this function returns prematurely then the plugin host process
        will log an error and attempt to call runConcurrentThread() again after several seconds.

        :return: None
        """
        self.logger.debug(f"Run Concurrent Loop Called")

        # Starting the Sanic server in a background thread
        self.start_server_thread()

        try:
            while True:
                if not self.server_thread.is_alive():
                    self.logger.warning("Sanic server thread died. Attempting to restart.")
                    self.start_server_thread()
                self.sleep(60)

        except self.StopThread:
            pass  # Optionally catch the StopThread exception and do any needed cleanup.

    #######################################
    ## Sanic


    ########################################
    def validateDeviceConfigUi(self, values_dict, type_id, dev_id):
        return (True, values_dict)

    ########################################
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        self.debugLog(u"closedPrefsConfigUi() method called.")

        if userCancelled:
            self.debugLog(u"User prefs dialog cancelled.")

        if not userCancelled:
            self.debugLevel = valuesDict.get('showDebugLevel', "10")
            self.debugLog(u"User prefs saved.")

            #self.logger.error(str(valuesDict))

            try:
                self.logLevel = int(valuesDict[u"showDebugLevel"])
            except:
                self.logLevel = logging.INFO

            self.indigo_log_handler.setLevel(self.logLevel)
            self.logger.debug(u"logLevel = " + str(self.logLevel))
            self.logger.debug(u"User prefs saved.")
            self.logger.debug(u"Debugging on (Level: {0})".format(self.debugLevel))

            self.debug1 = valuesDict.get('debug1', False)

            if self.selected_country !="":
                self.update_holidays()
        return True
