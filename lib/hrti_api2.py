import requests
import base64
import json

try:
    import http.cookiejar
except ImportError:
    import cookielib
import xbmc


class HRTiAPI:
    hrtiBaseUrl = "https://hrti.hrt.hr"
    hsapiBaseUrl = "https://hsapi.aviion.tv"
    session = requests.Session()

    def __init__(self, plugin):
        self.plugin = plugin

        self._auth = None
        self.logged_in = False
        self.__userid = None
        username = self.plugin.get_setting("username")
        if username == '':
            username = 'anonymoushrt'
        password = self.plugin.get_setting("password")
        if password == '':
            password = 'an0nPasshrt'
        self.__username = username
        self.__password = password
        self.__ip = self.get_ip(self)
        self.__drmid = None
        self.__user_agent = 'kodi plugin for hrti.hrt.hr (python)'
        self.DEVICE_ID = self.plugin.get_setting('device_id')
        self.TOKEN = self.plugin.get_setting('token')
        if self.TOKEN == '':
            self.TOKEN = 'lAWX321gC0Gc5c4d7QGg3g7CbuTPbavEeQuhKRyebvaQWEaWO2N8kmqwKNSUc8Gw'
        xbmc.log("hrti init with IP: " + str(self.__ip), level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with User: " + username, level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with PW: " + password, level=xbmc.LOGDEBUG)
        xbmc.log("hrti init with Cookie: " + str(self.session.cookies), level=xbmc.LOGDEBUG)
        self.grant_access()
        self.register_device()
        self.get_content_rating()
        self.get_profiles()

    def get_headers(self, host, referer):

        cookie_header = None
        for cookie in self.session.cookies:
            if cookie.domain == '.hrti.hrt.hr':
                cookie_header = cookie.name + "=" + cookie.value

        headers = {
            'host': host,
            'connection': 'keep-alive',
            'deviceid': self.DEVICE_ID,
            'operatorreferenceid': 'hrt',
            'authorization': 'Client ' + self.TOKEN,
            'ipaddress': str(self.__ip),
            'content-type': 'application/json',
            'accept': 'application/json, text/plain, */*',
            'user-agent': self.__user_agent,
            'devicetypeid': '6',
            'origin': 'https://hrti.hrt.hr',
            'referer': referer,
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': cookie_header
        }
        return headers

    @staticmethod
    def get_ip(self):
        url = self.hrtiBaseUrl+"/api/api/ott/getIPAddress"
        r = self.session.get(url)
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
            'User-Agent': self.__user_agent,
            # 'sec-fetch-site': 'same-origin',
            # 'sec-fetch-mode': 'cors',
            # 'sec - fetch - dest': 'empty',
            'Cookie': cookie_header
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
            'User-Agent':  self.__user_agent,
            'IPAddress': str(self.__ip),
            'OperatorReferenceId': 'hrt',
            'Cookie': cookie_header
        }

        response = self.session.post(url, headers=headers, data=payload)

        print(response.text)
        xbmc.log("hrti status code: " + str(response.status_code), level=xbmc.LOGDEBUG)
        if response.status_code == 200:
            print(response.headers.get('content-type'))
            self.logged_in = True
            result = response.json().get("Result")
            print(result)
            if not (result is None):
                self.TOKEN = result['Token']
                self.plugin.set_setting('token', self.TOKEN)
                validfrom = result['ValidFrom']
                validto = result['ValidTo']
                self.__userid = result['Customer']['CustomerId']
                email = result['Customer']['Email']
                print(self.TOKEN)
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
            else:
                self.plugin.dialog_ok(response.json().get("ErrorDescription"))
        return response.status_code

    def register_device(self):

        url = self.hsapiBaseUrl+"/client.svc/json/RegisterDevice"

        payload = json.dumps({
            "DeviceSerial": self.DEVICE_ID,
            "DeviceReferenceId": "6",
            "IpAddress": str(self.__ip),
            "ConnectionType": "LAN/WiFi",
            "ApplicationVersion": "5.62.5",
            "DrmId":  self.DEVICE_ID,
            "OsVersion": "Linux",
            "ClientType": "Chrome 96"
        })
        host = "hsapi.aviion.tv"
        referer = "https://hrti.hrt.hr/"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)
        return response.status_code

    def get_content_rating(self):

        url = self.hsapiBaseUrl + "/client.svc/json/ContentRatingsGet"

        payload = json.dumps({})
        host = "hsapi.aviion.tv"
        referer = "https://hrti.hrt.hr/"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)
        return response.status_code

    def get_profiles(self):

        url = self.hsapiBaseUrl + "/client.svc/json/ProfilesGet"

        payload = json.dumps({})
        host = "hsapi.aviion.tv"
        referer = "https://hrti.hrt.hr/"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)
        return response.status_code

    def get_channels(self):

        url = self.hrtiBaseUrl + "/api/api/ott/GetChannels"

        payload = json.dumps({})
        host = "hrti.hrt.hr"
        referer = "https://hrti.hrt.hr/signin"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)

        result = response.json().get("Result")
        return result

    def get_catalog_structure(self):

        url = self.hrtiBaseUrl + "/api/api/ott/GetCatalogueStructure"

        payload = json.dumps({})
        host = "hrti.hrt.hr"
        referer = "https://hrti.hrt.hr/videostore"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)
        result = response.json().get("Result")
        return result

    def get_catalog(self, reference_id, max_number, page):

        url = self.hrtiBaseUrl + "/api/api/ott/GetCatalogue"

        payload = json.dumps({
            "ReferenceId": reference_id,
            "ItemsPerPage": max_number,
            "PageNumber": page,
        })
        host = "hrti.hrt.hr"
        referer = "https://hrti.hrt.hr/videostore"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)
        result = response.json().get("Result")
        return result

    def get_vod_details(self, reference_id):

        url = self.hrtiBaseUrl + "/api/api/ott/GetVodDetails"

        payload = json.dumps({
            "ReferenceId": reference_id,
        })
        host = "hrti.hrt.hr"
        referer = "https://hrti.hrt.hr/videostore"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)

        result = response.json().get("Result")
        return result

    def get_programme(self, channelids, starttime, endtime):

        url = self.hrtiBaseUrl + "/api/api/ott/GetProgramme"

        payload = json.dumps({
            "ChannelReferenceIds": channelids,
            "StartTime": starttime,
            "EndTime": endtime
        })
        host = "hrti.hrt.hr"
        referer = "https://hrti.hrt.hr/home"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)

        result = response.json().get("Result")
        return result

    def authorize_session(self, contenttype, contentrefid, contentdrmid, videostorerefids, channelid):

        url = self.hrtiBaseUrl + "/api/api/ott/AuthorizeSession"

        payload = json.dumps({
            "ContentType": contenttype,
            "ContentReferenceId": contentrefid,
            "ContentDrmId": contentdrmid,
            "VideostoreReferenceIds": videostorerefids,
            "ChannelReferenceId": channelid,
            "Starttime": None,
            "EndTime": None
        })
        host = "hrti.hrt.hr"
        if channelid is None:
            referer = "https://hrti.hrt.hr/videostore"
        else:
            referer = "https://hrti.hrt.hr/live/"
            if contenttype == "tlive":
                referer += "tv?channel=' + str(channelid)"
            else:
                referer += "radio"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)

        result = response.json().get("Result")
        errorcode = response.json().get("ErrorCode")
        errordesc = response.json().get("ErrorDescription")
        if errorcode != 0:
            self.plugin.dialog_ok(errordesc)
        else:
            self.__drmid = result['DrmId']
        return result

    def report_session_event(self, sessionid, channelid):

        url = self.hrtiBaseUrl + "/api/api/ott/ReportSessionEvent"

        payload = json.dumps({
            "SessionEventId": 1,
            "SessionId": sessionid
        })
        host = "hrti.hrt.hr"
        if channelid is None:
            referer = "https://hrti.hrt.hr/videostore"
        else:
            referer = "https://hrti.hrt.hr/live/"
            referer += "tv?channel=' + str(channelid)"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)
        result = response.json().get("Result")
        return result

    def get_seasons(self, series_ref_id):

        url = self.hrtiBaseUrl + "/api/api/ott/GetSeasons"

        payload = json.dumps({
            "SeriesReferenceId": series_ref_id
        })
        host = "hrti.hrt.hr"
        referer = "https://hrti.hrt.hr/videostore"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)
        result = response.json().get("Result")
        return result

    def get_episodes(self, series_ref_id, season_ref_id):

        url = self.hrtiBaseUrl + "/api/api/ott/GetEpisodes"

        payload = json.dumps({
            "SeriesReferenceId": series_ref_id,
            "SeasonReferenceId": season_ref_id
        })
        host = "hrti.hrt.hr"
        referer = "https://hrti.hrt.hr/videostore"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)
        result = response.json().get("Result")
        return result

    def logout(self):

        url = self.hsapiBaseUrl + "/client.svc/json/DeviceInstanceDelete"

        payload = json.dumps({
            "Serial": self.DEVICE_ID,
        })
        host = "hsapi.aviion.tv"
        referer = "https://hrti.hrt.hr/"
        headers = self.get_headers(host, referer)
        response = self.session.post(url, headers=headers, data=payload)
        return response.status_code

    def get_license(self):
        # Prepare for drm keys
        drm_license = {'userId': self.__userid, 'sessionId': self.__drmid, 'merchant': 'aviion2'}
        try:
            license_str = base64.b64encode(json.dumps(drm_license))
            return license_str
        except Exception as e:
            license_str = base64.b64encode(json.dumps(drm_license).encode("utf-8"))
            return str(license_str, "utf-8")
