import requests
import time
import base64
import json

try:
    import http.cookiejar
except ImportError:
    import cookielib
import xbmc


class HRTiAPI:
    user_agent = "kodi plugin for hrti.hrt.hr (python)"

    def __init__(self, username, password):
        #        self.plugin = plugin
        self._auth = None
        self.logged_in = False
        self.__username = username
        self.__password = password
        self.__ip = self.get_ip()
        # self.__device_id = "a8dc5ca6-8932-4932-88b6-6aee5d843624"
        xbmc.log("hrti init with IP: " + str(self.__ip), level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with User: " + username, level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with PW: " + password, level=xbmc.LOGDEBUG)
        self.grant_access()

    @staticmethod
    def get_ip():
        url = "https://hrti.hrt.hr/api/api/ott/getIPAddress"
        r = requests.get(url)
        return r.json()

    def grant_access(self):
        url = "https://hrti.hrt.hr/api/api/ott/GrantAccess"
        payload = {'username': self.__username, 'password': self.__password, 'OperatorReferenceId': 'hrt'}
        headers = {'Authorization': 'Client lAWX321gC0Gc5c4d7QGg3g7CbuTPbavEeQuhKRyebvaQWEaWO2N8kmqwKNSUc8Gw',
                   'Content-Type': 'application/json',
                   'DeviceId': 'a8dc5ca6-8932-4932-88b6-6aee5d843624',
                   'DeviceTypeId': '6',
                   'Host': 'hrti.hrt.hr',
                   'IPAddress': str(self.__ip),
                   'OperatorReferenceId': 'hrt',
                   'Origin': 'https://hrti.hrt.hr',
                   'Referer': 'https://hrti.hrt.hr/signin',
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
        self._auth = None
        r = requests.post(url, data=payload, headers=headers)
        xbmc.log("hrti status code: " + str(r.status_code), level=xbmc.LOGDEBUG)
        if r.status_code == 200:
            self._auth = r.json()
            self.logged_in = True
            xbmc.log("hrti grant access: " + str(self._auth), level=xbmc.LOGDEBUG)
            self._auth["expires"] = time.time() + self._auth["expires_in"]
        return r.status_code
