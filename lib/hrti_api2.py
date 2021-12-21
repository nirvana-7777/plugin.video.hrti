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
        self.__ip = self.get_ip()
        xbmc.log("hrti init with IP: " + str(self.__ip), level=xbmc.LOGDEBUG)

    @staticmethod
    def get_ip():
        url = "https://hrti.hrt.hr/api/api/ott/getIPAddress"
        r = requests.get(url)
        return r.json()
