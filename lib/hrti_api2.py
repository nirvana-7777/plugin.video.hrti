import requests
import time
import base64
import json

import xbmc


class HRTiAPI:
    user_agent = "kodi plugin for hrti.hr (python)"

    def __init__(self, username, password):
        self._auth = None
        self.logged_in = False
        self.__username = username
        self.__password = password

