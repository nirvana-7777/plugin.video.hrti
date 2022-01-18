import requests
import base64
import json

try:
    import http.cookiejar
except ImportError:
    import cookielib
import xbmc


class HRTiAPI:
    hrtiBaseUrl = "https://hrti.hrt.hr/api/api/ott/"
    hsapiBaseUrl = "https://hsapi.aviion.tv/client.svc/json/"
    session = requests.Session()

    def __init__(self, plugin):
        self.plugin = plugin
        self.USERID = None
        self.__ip = self.get_ip(self)
        self.__drmid = None
        self.__user_agent = 'kodi plugin for hrti.hrt.hr (python)'
        self.DEVICE_ID = None
        self.TOKEN = ''
        self.__device_reference_id = self.plugin.get_setting('devicereferenceid')

    def api_post(self, url, payload, referer):

        cookie_header = None
        for cookie in self.session.cookies:
            if cookie.domain == '.hrti.hrt.hr':
                cookie_header = cookie.name + "=" + cookie.value

        headers = {
            'connection': 'keep-alive',
            'deviceid': self.DEVICE_ID,
            'operatorreferenceid': 'hrt',
            'authorization': 'Client ' + self.TOKEN,
            'ipaddress': str(self.__ip),
            'content-type': 'application/json',
            'accept': 'application/json, text/plain, */*',
            'user-agent': self.__user_agent,
            'devicetypeid': self.__device_reference_id,
            'origin': 'https://hrti.hrt.hr',
            'referer': referer,
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': cookie_header
        }
        response = self.session.post(url, headers=headers, data=payload)
        result = None
        if response.status_code == 200 and response.headers.get('content-type') == "application/json; charset=utf-8":
            errorcode = response.json().get("ErrorCode")
            errordesc = response.json().get("ErrorDescription")
            if errorcode != 0:
                self.plugin.dialog_ok(str(url) + " raised error " + str(errorcode) + ": " + str(errordesc))
            else:
                result = response.json().get("Result")
        else:
            self.plugin.dialog_ok("HRTi API Call for " +
                                  url + " did not respond 200 OK or JSON but "+str(response.status_code))
        return result

    @staticmethod
    def get_ip(self):
        url = self.hrtiBaseUrl+"getIPAddress"
        r = self.session.get(url)
        return r.json()

    def grant_access(self, username, password):
        url = self.hrtiBaseUrl+"GrantAccess"

        payload = json.dumps({
            "Username": username,
            "Password": password,
            "OperatorReferenceId": "hrt"
        })

        referer = "https://hrti.hrt.hr/signin"
        result = self.api_post(url, payload, referer)

        if result is not None:
            self.TOKEN = result['Token']
            self.plugin.set_setting('token', self.TOKEN)
            tokenvalidfrom = result['ValidFrom']
            tokenvalidto = result['ValidTo']
            self.USERID = result['Customer']['CustomerId']
            email = result['Customer']['Email']
            firstname = result['Customer']['FirstName']
            lastname = result['Customer']['LastName']
            language = result['Customer']['LanguageReferenceId']
            geoblocked = result['Customer']['GeoblockingEnabled']
            videostoreenabled = result['Customer']['VideostoreEnabled']
            pvrhours = result['Customer']['NPVRHours']
            self.plugin.set_setting('customerid', self.USERID)
            self.plugin.set_setting('email', email)
            self.plugin.set_setting('firstname', firstname)
            self.plugin.set_setting('lastname', lastname)
            self.plugin.set_setting('language', language)
            self.plugin.set_setting('geoblocked', str(geoblocked))
            self.plugin.set_setting('videostoreenabled', str(videostoreenabled))
            self.plugin.set_setting('pvrhours', str(pvrhours))
            validfrom = self.plugin.get_date_from_epoch(tokenvalidfrom)
            validto = self.plugin.get_date_from_epoch(tokenvalidto)
            self.plugin.set_setting('validfrom', str(validfrom))
            self.plugin.set_setting('validto', str(validto))
            xbmc.log("hrti grant access: " + str(result), level=xbmc.LOGDEBUG)
        return result

    def register_device(self):

        url = self.hsapiBaseUrl+"RegisterDevice"

        payload = json.dumps({
            "DeviceSerial": self.DEVICE_ID,
            "DeviceReferenceId": self.__device_reference_id,
            "IpAddress": str(self.__ip),
            "ConnectionType": self.plugin.get_setting('connectiontype'),
            "ApplicationVersion": self.plugin.get_setting('applicationversion'),
            "DrmId":  self.DEVICE_ID,
            "OsVersion": self.plugin.get_setting('osversion'),
            "ClientType": self.plugin.get_setting('clienttype')
        })
        referer = "https://hrti.hrt.hr/"
        result = self.api_post(url, payload, referer)
        return result

    def get_content_rating(self):

        url = self.hsapiBaseUrl + "ContentRatingsGet"

        payload = json.dumps({})
        referer = "https://hrti.hrt.hr/"
        result = self.api_post(url, payload, referer)
        return result

    def get_profiles(self):

        url = self.hsapiBaseUrl + "ProfilesGet"

        payload = json.dumps({})
        referer = "https://hrti.hrt.hr/"
        result = self.api_post(url, payload, referer)
        return result

    def get_channels(self):

        url = self.hrtiBaseUrl + "GetChannels"

        payload = json.dumps({})
        referer = "https://hrti.hrt.hr/signin"
        result = self.api_post(url, payload, referer)
        return result

    def get_catalog_structure(self):

        url = self.hrtiBaseUrl + "GetCatalogueStructure"

        payload = json.dumps({})
        referer = "https://hrti.hrt.hr/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_catalog(self, reference_id, max_number, page):

        url = self.hrtiBaseUrl + "GetCatalogue"

        payload = json.dumps({
            "ReferenceId": reference_id,
            "ItemsPerPage": max_number,
            "PageNumber": page,
        })
        referer = "https://hrti.hrt.hr/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_vod_details(self, reference_id):

        url = self.hrtiBaseUrl + "GetVodDetails"

        payload = json.dumps({
            "ReferenceId": reference_id,
        })
        referer = "https://hrti.hrt.hr/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_programme(self, channelids, starttime, endtime):

        url = self.hrtiBaseUrl + "GetProgramme"

        payload = json.dumps({
            "ChannelReferenceIds": channelids,
            "StartTime": starttime,
            "EndTime": endtime
        })
        referer = "https://hrti.hrt.hr/home"
        result = self.api_post(url, payload, referer)
        return result

    def get_epg_details(self, channelid, referenceid):

        url = self.hrtiBaseUrl + "GetEpgDetails"

        payload = json.dumps({
            "ChannelReferenceId": channelid,
            "ReferenceId": referenceid,
        })
        referer = "https://hrti.hrt.hr/live/programme"
        result = self.api_post(url, payload, referer)
        return result

    def get_devices(self):

        url = self.hsapiBaseUrl + "DeviceInstancesGet"

        payload = json.dumps({
        })
        referer = "https://hrti-selfcare.hrt.hr/"
        result = self.api_post(url, payload, referer)
        return result

    def authorize_session(self, contenttype, contentrefid, contentdrmid,
                          videostorerefids, channelid, starttime, endtime):

        url = self.hrtiBaseUrl + "AuthorizeSession"

        payload = json.dumps({
            "ContentType": contenttype,
            "ContentReferenceId": contentrefid,
            "ContentDrmId": contentdrmid,
            "VideostoreReferenceIds": videostorerefids,
            "ChannelReferenceId": channelid,
            "Starttime": starttime,
            "EndTime": endtime
        })
        xbmc.log("Authorize Session: " + str(payload), level=xbmc.LOGDEBUG)
        if channelid is None:
            referer = "https://hrti.hrt.hr/videostore"
        else:
            referer = "https://hrti.hrt.hr/live/"
            if contenttype == "tlive":
                referer += "tv?channel=' + str(channelid)"
            else:
                referer += "radio"
        result = self.api_post(url, payload, referer)
        if result is not None:
            self.__drmid = result['DrmId']
        return result

    def report_session_event(self, sessionid, channelid):

        url = self.hrtiBaseUrl + "ReportSessionEvent"

        payload = json.dumps({
            "SessionEventId": 1,
            "SessionId": sessionid
        })
        if channelid is None:
            referer = "https://hrti.hrt.hr/videostore"
        else:
            referer = "https://hrti.hrt.hr/live/"
            referer += "tv?channel=' + str(channelid)"
        result = self.api_post(url, payload, referer)
        return result

    def get_seasons(self, series_ref_id):

        url = self.hrtiBaseUrl + "GetSeasons"

        payload = json.dumps({
            "SeriesReferenceId": series_ref_id
        })
        referer = "https://hrti.hrt.hr/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_episodes(self, series_ref_id, season_ref_id):

        url = self.hrtiBaseUrl + "GetEpisodes"

        payload = json.dumps({
            "SeriesReferenceId": series_ref_id,
            "SeasonReferenceId": season_ref_id
        })
        referer = "https://hrti.hrt.hr/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_radio_metadata(self, channel_ref_id):

        url = self.hrtiBaseUrl + "GetRadioEventMetadata"

        payload = json.dumps({
            "ChannelReferenceId": channel_ref_id,
        })
        referer = "https://hrti.hrt.hr/live/radio"
        result = self.api_post(url, payload, referer)
        return result

    def get_device_instances(self):

        url = self.hsapiBaseUrl + "DeviceInstancesGet"

        payload = json.dumps({
        })
        referer = "https://hrti-selfcare.hrt.hr/"
        result = self.api_post(url, payload, referer)
        return result

    def logout(self):

        url = self.hsapiBaseUrl + "DeviceInstanceDelete"

        payload = json.dumps({
            "Serial": self.DEVICE_ID,
        })
        referer = "https://hrti.hrt.hr/"
        result = self.api_post(url, payload, referer)
        return result

    def get_license(self):
        # Prepare for drm keys
        drm_license = {'userId': self.USERID, 'sessionId': self.__drmid, 'merchant': 'aviion2'}
        xbmc.log("DRM License: " + str(drm_license), level=xbmc.LOGDEBUG)
        try:
            license_str = base64.b64encode(json.dumps(drm_license))
            return license_str
        except Exception as e:
            license_str = base64.b64encode(json.dumps(drm_license).encode("utf-8"))
            return str(license_str, "utf-8")
