# -*- coding: utf-8 -*-
# Related to config_controller
# Test code for config modules

# This files is part of anki-web-browser addon
# @author ricardo saturnino
# ------------------------------------------------

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')

import unittest
import src.config as cc

from PyQt5 import QtWidgets
app = QtWidgets.QApplication(sys.argv)

class ConfigServiceTester(unittest.TestCase):

    _tested = cc.ConfigService()

    def test_loadOK(self):
        cc.currentLocation = os.path.dirname(os.path.realpath(__file__))
        os.remove(cc.currentLocation + '/' + cc.CONFIG_FILE)
        config = self._tested.load()
        self.assertIsNotNone(config)
        self.assertEqual(config.keepBrowserOpened, True)
        self.assertEqual(config.browserAlwaysOnTop, False)
        self.assertEqual(4, len(config.providers))


    def test_loadNoFile(self):
        try:
            config = self._tested.load(False)
            self.fail() # exception expected
        except:
            pass


    def test_loadAndSave(self):
        cc.currentLocation = os.path.dirname(os.path.realpath(__file__))
        config = self._tested.load(False)
        providers = config.providers
        providers.append(cc.ConfigHolder.Provider('Yahoo', 'https://www.yahoo.com/{}'))
        config.keepBrowserOpened = True
        self._tested._config = config

        return  # should not change the real file. Would break future tests
        self._tested.save()

    def test_validation(self):
        c = cc.ConfigHolder(browserAlwaysOnTop=True)
        self._tested.validate(c)
        try:
            c2 = 'Error'
            self._tested.validate(c2)
            self.fail() # exception expected
        except:
            pass
        
        try:
            c2 = cc.ConfigHolder()
            c2.providers = ['Oh no!']
            self._tested.validate(c2)
            self.fail() # exception expected
        except:
            pass

        try:
            c2 = cc.ConfigHolder(keepBrowserOpened='Now as string')
            self._tested.validate(c2)
            self.fail() # exception expected
        except:
            pass

    def test_valid_urls(self):
        ch = cc.ConfigHolder()
        ch.providers.append(cc.ConfigHolder.Provider('Google', 'https://www.google.com/search?tbm=isch&q={}'))
        ch.providers.append(cc.ConfigHolder.Provider('Sentence', 'http://sentence.yourdictionary.com/{}?direct_search_result=yes'))
        ch.providers.append(cc.ConfigHolder.Provider('issues#5', 'https://www.google.co.jp/search?tbm=isch&q={}+アニメ美少女'))
        self._tested.validate(ch)

    def test_sort_providers(self):
        ch = cc.ConfigHolder()
        ch.providers.append(cc.ConfigHolder.Provider('Google', 'https://www.google.com/search?tbm=isch&q={}'))
        ch.providers.append(cc.ConfigHolder.Provider('Amazon', 'http://amazon.com/{}?direct_search_result=yes'))
        ch.providers.append(cc.ConfigHolder.Provider('Facebook', 'https://www.facebook.com/{}'))
        self._tested.sortProviders(ch)

        self.assertEqual(ch.providers[0].name, 'Amazon')
        self.assertEqual(ch.providers[1].name, 'Facebook')

    def test_move_providerUp(self):
        ch = cc.ConfigHolder()
        ch.providers.append(cc.ConfigHolder.Provider('Google', 'https://www.google.com/search?tbm=isch&q={}'))
        ch.providers.append(cc.ConfigHolder.Provider('Amazon', 'http://amazon.com/{}?direct_search_result=yes'))
        ch.providers.append(cc.ConfigHolder.Provider('Facebook', 'https://www.facebook.com/{}'))

        self._tested.moveProvider(ch, 0, True)      # do nothing
        self.assertEqual(ch.providers[0].name, 'Google')

        self._tested.moveProvider(ch, 2, True)      # do nothing
        self.assertEqual(ch.providers[1].name, 'Facebook')

    def test_move_providerDown(self):
        ch = cc.ConfigHolder()
        ch.providers.append(cc.ConfigHolder.Provider('Google', 'https://www.google.com/search?tbm=isch&q={}'))
        ch.providers.append(cc.ConfigHolder.Provider('Amazon', 'http://amazon.com/{}?direct_search_result=yes'))
        ch.providers.append(cc.ConfigHolder.Provider('Facebook', 'https://www.facebook.com/{}'))

        self._tested.moveProvider(ch, 2, False)      # do nothing
        self.assertEqual(ch.providers[2].name, 'Facebook')

        self._tested.moveProvider(ch, 1, False)      # do nothing
        self.assertEqual(ch.providers[1].name, 'Facebook')

    def test_getInitialWindowSizeOk(self):
        ch = cc.ConfigHolder(initialBrowserSize="5050x30")
        self._tested._config = ch
        result = self._tested.getInitialWindowSize()
        self.assertEqual(5050, result[0])
        self.assertEqual(30, result[1])

    def test_getInitialWindowSizeInvalid(self):
        ch = cc.ConfigHolder(initialBrowserSize="3030-30")
        self._tested._config = ch
        result = self._tested.getInitialWindowSize()
        self.assertEqual(850, result[0])
        self.assertEqual(500, result[1])

class ConfigControllerTester(unittest.TestCase):

    cc.currentLocation = os.path.dirname(os.path.realpath(__file__))
    _tested = cc.ConfigController(None)
    
    def test_ItemSelection(self):
        self._tested.onSelectItem()
        self.assertTrue(self._tested._hasSelection)
        self._tested.onUnSelectItem()
        self.assertFalse(self._tested._hasSelection)


    def test_hasChanges(self):
        self._tested.onChangeItem()
        self.assertEqual(True, self._tested._pendingChanges)



if __name__ == '__main__':
    if '-view' in sys.argv:        
        main = QtWidgets.QMainWindow()
        view = cc.ConfigController(main)
        view.open()
        sys.exit(app.exec_())
    else:
        unittest.main()
