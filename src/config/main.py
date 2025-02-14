# -*- coding: utf-8 -*-
# Handles Configuration reading, saving and the integration with the web UI
# Contains model, service and view controller for Config
#
# This files is part of anki-web-browser addon
# @author ricardo saturnino
# -------------------------------------------------------
from typing import List

from ..core import Feedback

import os
import json
import re
import shutil

currentLocation = os.path.dirname(os.path.realpath(__file__))
CONFIG_LOCATION = currentLocation + '/..'
CONFIG_FILE = 'config.json'

# ---------------------------------- Model ------------------------------


# noinspection PyPep8Naming
class ConfigHolder:
    SHORTCUT = 'Ctrl+Shift+B'
    RP_SHORT = 'F10'
    INITIAL_SIZE = '850x500'

    def __init__(self, keepBrowserOpened=True, browserAlwaysOnTop=False, menuShortcut=SHORTCUT, \
                 providers=[], initialBrowserSize=INITIAL_SIZE, enableDarkReader=False,
                 repeatShortcut=RP_SHORT, useSystemBrowser=False, groups=[], filteredWords=[], **kargs):
        self.providers = [Provider(**p) for p in providers]
        self.groups = [SearchGroup(**g) for g in groups]
        self.keepBrowserOpened = keepBrowserOpened
        self.browserAlwaysOnTop = browserAlwaysOnTop
        self.useSystemBrowser = useSystemBrowser
        self.menuShortcut = menuShortcut
        self.repeatShortcut = repeatShortcut
        self.filteredWords = filteredWords
        self.initialBrowserSize = initialBrowserSize
        self.enableDarkReader = enableDarkReader

    def toDict(self):
        res = dict({
            'keepBrowserOpened': self.keepBrowserOpened,
            'browserAlwaysOnTop': self.browserAlwaysOnTop,
            'useSystemBrowser': self.useSystemBrowser,
            'menuShortcut': self.menuShortcut,
            'repeatShortcut': self.repeatShortcut, 
            'providers': [p for p in map(lambda p: p.__dict__, self.providers)],
            'groups': [g for g in map(lambda g: g.__dict__, self.groups)],
            'filteredWords': self.filteredWords,
            'initialBrowserSize': self.initialBrowserSize,
            'enableDarkReader': self.enableDarkReader
        })
        return res


class Provider:

    def __init__(self, name, url, **kargs):
        self.name = name
        self.url = url


class SearchGroup:

    def __init__(self, name: str, providerList: List[str]):
        self.name = name
        self.providerList = providerList


# ------------------------------ Service class --------------------------
# noinspection PyPep8Naming,PyMethodMayBeStatic
class ConfigService:
    """
        Responsible for reading and storing configurations
    """
    _config = None
    _validURL = re.compile('^((http|ftp){1}s{0,1}://)([\w._/?&=%#,@]|-)+{}([\w._/?&=%#,;+]|-)*$')
    firstTime = None

    def getConfig(self):
        if not self._config:
            return self.load()
        return self._config        

    def load(self, createIfNotExists=True):
        Feedback.log('[INFO] Trying to read web file in {}'.format(self._configLocation()))
        try:
            conf = self._readFileToObj()
        except:
            conf = False

        if not conf and createIfNotExists:
            conf = self._createConfiguration()
        self._config = conf
        return conf

    def _readFileToObj(self) -> ConfigHolder:
        with open(self._configLocation()) as f:
            obj = json.load(f)
            Feedback.log(obj)
            conf = ConfigHolder(**obj)

        return conf

    def __writeToFile(self, config):
        """ Handles file writing... """

        bkpName = None  #
        try:
            if os.path.exists(self._configLocation()):
                bkpName = shutil.copyfile(self._configLocation(), self._configLocation() + '.bkp')
            with(open(self._configLocation(), 'w')) as cfgFile:
                json.dump(config.toDict(), cfgFile)
        except Exception as e:
            if bkpName:
                shutil.copyfile(bkpName, self._configLocation())  # restore
            Feedback.showError(e)
        finally:
            if bkpName:
                os.remove(bkpName)

    def _createConfiguration(self):
        """
            Creates a new default configuration file. 
            A simple JSON from a dictionary. Should be called only if the file doesn't exist yet
        """

        Feedback.log('[INFO] Creating a new web file in {}'.format(self._configLocation()))

        conf = ConfigHolder()

        # default providers
        conf.providers = [
            Provider('Google Web', 'https://google.com/search?q={}'),
            Provider('Google Translate', 'https://translate.google.com/#view=home&op=translate&sl=auto&tl=en&text={}'),
            Provider('Google Images', 'https://www.google.com/search?tbm=isch&q={}'),
            Provider('Forvo', 'https://forvo.com/search/{}/')]

        conf.groups = [SearchGroup('Google', ['Google Web', 'Google Translate', 'Google Images'])]

        self.__writeToFile(conf)
        self.firstTime = True
        return conf

    def _configLocation(self):
        return "%s/%s" % (currentLocation, CONFIG_FILE)

    def save(self, config):
        """ Save a given configuration """

        Feedback.log('Save: ', vars(config))

        if not config:
            return

        try:
            self.validate(config)
        except ValueError as ve:
            Feedback.showInfo(ve)
            return False
        
        Feedback.log('[INFO] Saving web file in {}'.format(self._configLocation()))
        self.__writeToFile(config)
        self._config = config
        Feedback.showInfo('Anki-Web-Browser configuration saved')
        return True

    def validate(self, config):
        """
            Checks the configuration before saving it. 
            Checks types and the URL from the providers
        """

        checkedTypes = [(config, ConfigHolder), (config.keepBrowserOpened, bool), (config.browserAlwaysOnTop, bool),
                        (config.useSystemBrowser, bool), (config.providers, list),
                        (config.enableDarkReader, bool)]
        for current, expected in checkedTypes:
            if not isinstance(current, expected):
                raise ValueError('{} should be {}'.format(current, expected))

        for name, url in map(lambda item: (item.name, item.url), config.providers):
            if not name or not url:
                raise ValueError('There is an illegal value for one provider (%s %s)' % (name, url))
            if not self._validURL.match(url):
                raise ValueError('Some URL is invalid. Check the URL and if it contains {} that will be replaced by ' +
                                 'the text: %s' % url)

        if not self.isValidSize(config.initialBrowserSize):
            raise ValueError('Initial browser size contains invalid values')

    # ---------------------------------- Validations ------------------------------------

    reDimensions = re.compile(r'\d+x\d+', re.DOTALL)

    def isValidSize(self, value: str):
        return self.reDimensions.match(value)

    def getInitialWindowSize(self) -> tuple:
        cValue = self._config.initialBrowserSize if hasattr(self._config, 'initialBrowserSize') else None
        if cValue:
            if self.reDimensions.findall(cValue):
                return tuple(map(lambda i: int(i), cValue.split('x')))
        return tuple(map(lambda i: int(i), self._config.INITIAL_SIZE.split('x')))


# -----------------------------------------------------------------------------
# global instances

service = ConfigService()
