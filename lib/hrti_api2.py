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
        self.__ip = self.get_ip(self)
        self.__session = requests.session()
        # self.__device_id = "a8dc5ca6-8932-4932-88b6-6aee5d843624"
        xbmc.log("hrti init with IP: " + str(self.__ip), level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with User: " + username, level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with PW: " + password, level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with Cookie: " + str(self.__session.cookies), level=xbmc.LOGDEBUG)
        self.grant_access()

    @staticmethod
    def get_ip(self):
        url = "https://hrti.hrt.hr/api/api/ott/getIPAddress"
        r = self.__session.get(url)
        # r = requests.get(url)
        # self.cookie = r.cookies
        return r.json()

    def grant_access(self):
        url = "https://hrti.hrt.hr/api/api/ott/GrantAccess"
        payload = {'Username': self.__username, 'Password': self.__password, 'OperatorReferenceId': 'hrt'}
        xbmc.log("hrti payload: " + str(payload), level=xbmc.LOGDEBUG)
        headers = {'Authorization': 'Client lAWX321gC0Gc5c4d7QGg3g7CbuTPbavEeQuhKRyebvaQWEaWO2N8kmqwKNSUc8Gw',
                   'Content-Type': 'application/json',
                   'Accept': 'application/json, text/plain, */*',
                   'Connection': 'keep-alive',
                   'content-length': '88',
                   'DeviceId': 'a8dc5ca6-8932-4932-88b6-6aee5d843624',
                   'DeviceTypeId': '6',
                   'Host': 'hrti.hrt.hr',
                   'IPAddress': str(self.__ip),
                   'OperatorReferenceId': 'hrt',
                   'sec-ch-ua-mobile': '?0',
                   'Origin': 'https://hrti.hrt.hr',
                   'Referer': 'https://hrti.hrt.hr/signin',
                   'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                   'sec-ch-ua-platform': '"Linux"',
                   'accept-encoding': 'gzip, deflate, br',
                   'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
                   'sec-fetch-site': 'same-origin',
                   'sec-fetch-mode': 'cors',
                   'sec - fetch - dest': 'empty',
                   'Cookie': 'TS0177c9b9=014e8828817d2e4bc56cfaabd7b676c92d3bbefefd4bcfffe1c083a87c72151bf86f679d9b094caa488850275c2b3754eca404fac3',
                   # 'Cookie': 'G_ENABLED_IDPS=google; __gfp_64b=dvp3hBZb2fPYy3qzSZtVq.Ry9tKP.Qk5fq.vGYYpDin.27|1638888286; g_state={"i_p":1640256389790,"i_l":3,"i_t":1640340704876}; ',
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
        self._auth = None
        # r = requests.post(url, json=payload, headers=headers, cookies=self.cookie)
        r = self.__session.post(url, json=payload, headers=headers)
        xbmc.log("hrti status code: " + str(r.status_code), level=xbmc.LOGDEBUG)
        if r.status_code == 200:
            # self._auth = r.json()
            self.logged_in = True
            # result = r.get('Result')
            # token = result.get()
            # json_data = json.loads(r.text)
            # print(json.dumps(parsed_json, indent=4, sort_keys=True))
            # xbmc.log("hrti grant access: " + str(r.json()), level=xbmc.LOGDEBUG)
            xbmc.log("hrti grant access: " + r.text, level=xbmc.LOGDEBUG)
            # self._auth["expires"] = time.time() + self._auth["expires_in"]
        return r.status_code
