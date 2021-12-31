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
    hrtiBaseUrl = "https://hrti.hrt.hr"
    hsapiBaseUrl = "https://hsapi.aviion.tv"
    session = requests.Session()

    def __init__(self, username, password):
        #        self.plugin = plugin
        self._auth = None
        self.logged_in = False
        self.__userid = None
        self.__username = username
        self.__password = password
        self.__ip = self.get_ip(self)
        self.__token = None
        # self.__device_id = "a8dc5ca6-8932-4932-88b6-6aee5d843624"
        xbmc.log("hrti init with IP: " + str(self.__ip), level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with User: " + username, level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with PW: " + password, level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with Cookie: " + str(self.session.cookies), level=xbmc.LOGDEBUG)
        self.grant_access()
        self.register_device()
        self.get_content_rating()
        self.get_profiles()

    @staticmethod
    def get_ip(self):
        url = self.hrtiBaseUrl+"/api/api/ott/getIPAddress"
        r = self.session.get(url)
        # r = requests.get(url)
        # self.cookie = r.cookies
        print(r.headers)
        print(r.json())
        return r.json()

    def grant_access(self):
        cookie_header = None
        for cookie in self.session.cookies:
            print('cookie domain = ' + cookie.domain)
            print('cookie name = ' + cookie.name)
            print('cookie value = ' + cookie.value)
            print('*************************************')
            if cookie.domain == '.hrti.hrt.hr':
                cookie_header = cookie.name+"="+cookie.value
        print(cookie_header)
        url = "https://hrti.hrt.hr/api/api/ott/GrantAccess"
        payload = {
            "Username": self.__username,
            "Password": self.__password,
            "OperatorReferenceId": "hrt"
        }
        xbmc.log("hrti payload: " + str(payload), level=xbmc.LOGDEBUG)
        headers = {
            'content-type': 'application/json',
            'accept': 'application/json, text/plain, */*',
            # 'authorization': 'Client lAWX321gC0Gc5c4d7QGg3g7CbuTPbavEeQuhKRyebvaQWEaWO2N8kmqwKNSUc8Gw',
            # 'Connection': 'keep-alive',
            'content-length': '107',
            # 'deviceid': 'a8dc5ca6-8932-4932-88b6-6aee5d843624',
            # 'DeviceTypeId': '6',
            'Host': 'hrti.hrt.hr',
            'IPAddress': str(self.__ip),
            'OperatorReferenceId': 'hrt',
            # 'sec-ch-ua-mobile': '?0',
            # 'Origin': 'https://hrti.hrt.hr',
            # 'Referer': 'https://hrti.hrt.hr/signin',
            # 'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            # 'sec-ch-ua-platform': '"Linux"',
            # 'accept-encoding': 'gzip, deflate, br',
            # 'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'User-Agent': self.user_agent,
            # 'sec-fetch-site': 'same-origin',
            # 'sec-fetch-mode': 'cors',
            # 'sec - fetch - dest': 'empty',
            'Cookie': cookie_header
            # 'Cookie': 'G_ENABLED_IDPS=google; __gfp_64b=dvp3hBZb2fPYy3qzSZtVq.Ry9tKP.Qk5fq.vGYYpDin.27|1638888286; g_state={"i_p":1640256389790,"i_l":3,"i_t":1640340704876}; ',
            # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }
        self._auth = None
        # r = requests.post(url, json=payload, headers=headers, cookies=self.cookie)
        print(json.dumps(headers))
        print(json.dumps(payload))
        print(url)
        # self.session.headers.update({'user-agent': self.user_agent})
        # self.session.headers.update({'content-type': 'application/json'})
        # self.session.headers.update({'content-length': '107'})
        # self.session.headers.update({'deviceid': 'a8dc5ca6-8932-4932-88b6-6aee5d843624'})
        # self.session.headers.update({'host': 'hrti.hrt.hr'})
        # self.session.headers.update({'cookie': cookie_header})
        # print(self.session.headers)
        # r = self.session.post(url, json=json.dumps(payload), headers=headers)
        url = self.hrtiBaseUrl+"/api/api/ott/GrantAccess"

        payload = json.dumps({
            "Username": self.__username,
            "Password": self.__password,
            "OperatorReferenceId": "hrt"
        })
        headers = {
            'content-type': 'application/json',
            'User-Agent': self.user_agent,
            'IPAddress': str(self.__ip),
            'OperatorReferenceId': 'hrt',
            'Cookie': cookie_header
        }

        response = self.session.post(url, headers=headers, data=payload)

        print(response.text)
        xbmc.log("hrti status code: " + str(response.status_code), level=xbmc.LOGDEBUG)
        if response.status_code == 200:
            print(response.headers.get('content-type'))
            # self._auth = r.json()
            self.logged_in = True
            # result = r.get('Result')
            # token = result.get()
            result = response.json().get("Result")
            print(result)
            self.__token = result['Token']
            validfrom = result['ValidFrom']
            validto = result['ValidTo']
            self.__userid = result['Customer']['CustomerId']
            email = result['Customer']['Email']
            print(self.__token)
            print(validfrom)
            print(validto)
            print(self.__userid)
            print(email)
            # print(result.json().get("ValidFrom"))
            # print(result.json().get("ValidTo"))
            # print(json.dumps(parsed_json, indent=4, sort_keys=True))
            print(response.json())
            # xbmc.log("hrti grant access: " + str(r.json()), level=xbmc.LOGDEBUG)
            xbmc.log("hrti grant access: " + response.text, level=xbmc.LOGDEBUG)
            # self._auth["expires"] = time.time() + self._auth["expires_in"]
        return response.status_code

    def register_device(self):

        url = self.hsapiBaseUrl+"/client.svc/json/RegisterDevice"

        payload = json.dumps({
            "DeviceSerial": "b6a50484-93a0-4afb-a01c-8d17e059feda",
            "DeviceReferenceId": "6",
            "IpAddress": str(self.__ip),
            "ConnectionType": "LAN/WiFi",
            "ApplicationVersion": "5.62.5",
            "DrmId": "b6a50484-93a0-4afb-a01c-8d17e059feda",
            "OsVersion": "Linux",
            "ClientType": "Chrome 96"
        })

        headers = {
            'host': 'hsapi.aviion.tv',
            'connection': 'keep-alive',
            'content-length': '257',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'authorization': 'Client '+self.__token,
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'sec-ch-ua-platform': '"Linux"',
            'origin': 'https://hrti.hrt.hr',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://hrti.hrt.hr/',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        response = self.session.post(url, headers=headers, data=payload)

        print(response.headers.get('content-type'))
        print(response.text)
        return response.status_code

    def get_content_rating(self):

        url = self.hsapiBaseUrl + "/client.svc/json/ContentRatingsGet"

        payload = json.dumps({})

        headers = {
            'host': 'hsapi.aviion.tv',
            'connection': 'keep-alive',
            'content-length': '2',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'authorization': 'Client '+self.__token,
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'sec-ch-ua-platform': '"Linux"',
            'origin': 'https://hrti.hrt.hr',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://hrti.hrt.hr/',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        response = self.session.post(url, headers=headers, data=payload)

        print(response.headers.get('content-type'))
        print(response.text)
        return response.status_code

    def get_profiles(self):

        url = self.hsapiBaseUrl + "/client.svc/json/ProfilesGet"

        payload = json.dumps({})

        headers = {
            'host': 'hsapi.aviion.tv',
            'connection': 'keep-alive',
            'content-length': '2',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'authorization': 'Client '+self.__token,
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'sec-ch-ua-platform': '"Linux"',
            'origin': 'https://hrti.hrt.hr',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://hrti.hrt.hr/',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        response = self.session.post(url, headers=headers, data=payload)

        print(response.headers.get('content-type'))
        print(response.text)
        return response.status_code

    def get_channels(self):

        url = self.hrtiBaseUrl + "/api/api/ott/GetChannels"

        cookie_header = None
        for cookie in self.session.cookies:
            if cookie.domain == '.hrti.hrt.hr':
                cookie_header = cookie.name + "=" + cookie.value

        payload = json.dumps({})
        headers = {
            'host': 'hrti.hrt.hr',
            'connection': 'keep-alive',
            'content-length': '2',
            'deviceid': 'b6a50484-93a0-4afb-a01c-8d17e059feda',
            'operatorreferenceid': 'hrt',
            'sec-ch-ua-mobile': '?0',
            'authorization': 'Client '+self.__token,
            'ipaddress': str(self.__ip),
            'content-type': 'application/json',
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'devicetypeid': '6',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'sec-ch-ua-platform': '"Linux"',
            'origin': 'https://hrti.hrt.hr',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://hrti.hrt.hr/signin',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': cookie_header
        }

        response = self.session.post(url, headers=headers, data=payload)

        print(response.headers.get('content-type'))
        print(response.text)
        result = response.json().get("Result")
        return result


    def get_programme(self, channelIDs, starttime, endtime):

        url = self.hrtiBaseUrl + "/api/api/ott/GetProgramme"

        cookie_header = None
        for cookie in self.session.cookies:
            if cookie.domain == '.hrti.hrt.hr':
                cookie_header = cookie.name + "=" + cookie.value

        payload = json.dumps({
            "ChannelReferenceIds": channelIDs,
            "StartTime": starttime,
            "EndTime": endtime
        })
        headers = {
            'host': 'hrti.hrt.hr',
            'connection': 'keep-alive',
            'content-length': '2',
            'deviceid': 'b6a50484-93a0-4afb-a01c-8d17e059feda',
            'operatorreferenceid': 'hrt',
            'sec-ch-ua-mobile': '?0',
            'authorization': 'Client '+self.__token,
            'ipaddress': str(self.__ip),
            'content-type': 'application/json',
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'devicetypeid': '6',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'sec-ch-ua-platform': '"Linux"',
            'origin': 'https://hrti.hrt.hr',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://hrti.hrt.hr/home',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': cookie_header
        }

        response = self.session.post(url, headers=headers, data=payload)

        print(response.headers.get('content-type'))
        print(response.text)
        result = response.json().get("Result")
        return result


    def authorize_session(self, channelID):

        url = self.hrtiBaseUrl + "/api/api/ott/AuthorizeSession"

        cookie_header = None
        for cookie in self.session.cookies:
            if cookie.domain == '.hrti.hrt.hr':
                cookie_header = cookie.name + "=" + cookie.value

        payload = json.dumps({
            "ContentType": "tlive",
            "ContentReferenceId": "40013",
            "ContentDrmId": "hrtliveorigin_hrt1.smil",
            "VideostoreReferenceIds": None,
            "ChannelReferenceId": "40013",
            "StartTime": None,
            "EndTime": None
        })
        headers = {
            'host': 'hrti.hrt.hr',
            'connection': 'keep-alive',
            'content-length': '2',
            'deviceid': 'b6a50484-93a0-4afb-a01c-8d17e059feda',
            'operatorreferenceid': 'hrt',
            'sec-ch-ua-mobile': '?0',
            'authorization': 'Client '+self.__token,
            'ipaddress': str(self.__ip),
            'content-type': 'application/json',
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'devicetypeid': '6',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'sec-ch-ua-platform': '"Linux"',
            'origin': 'https://hrti.hrt.hr',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://hrti.hrt.hr/live/tv?channel=40013',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': cookie_header
        }

        response = self.session.post(url, headers=headers, data=payload)

        print(response.headers.get('content-type'))
        print(response.text)
        result = response.json().get("Result")
        return result

    def getLicense(self):
        # Prepare for drm keys
        # {"userId": "8140543", "sessionId": "xpk8juE5T3-HKqAxM6WAKLjqeC4EmxcvRScuF0n3X2o.", "merchant": "aviion2"}
        # license = {'merchant': 'exaring', 'sessionId': 'default', 'userId': 'userHandle'}
        license = {'userId': self.__userid, 'sessionId': '6:hrt:8140543:b6a50484-93a0-4afb-a01c-8d17e059feda', 'merchant': 'aviion2'}
        # license = {"userId": self.__userid, "sessionId": "default", "merchant": "aviion2"}
        try:
            license_str = base64.b64encode(json.dumps(license))
            return license_str
        except Exception as e:
            license_str = base64.b64encode(json.dumps(license).encode("utf-8"))
            return str(license_str, "utf-8")

