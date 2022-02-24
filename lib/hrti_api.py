import requests
import base64
import json

try:
    import http.cookiejar
except ImportError:
    import cookielib
import xbmc


class HRTiAPI:
    hrtiDomain = "https://hrti.hrt.hr"
    hrtiEnvUrl = hrtiDomain + "/assets/config/env.json"
    hrtiConfUrl = hrtiDomain + "/assets/config/config.production.json"
    session = requests.Session()

    def __init__(self, plugin):
        self.plugin = plugin
        self.USERID = None
        self.__drmid = None
        self.__user_agent = 'kodi plugin for hrti.hrt.hr (python)'
        self.DEVICE_ID = None
        self.TOKEN = ''
        self.IP = None
        self.__device_reference_id = self.plugin.get_setting('devicereferenceid')
        self.__operator_reference_id = self.plugin.get_setting('operatorreferenceid')
        self.__merchant = self.plugin.get_setting('merchant')
        self.hrtiBaseUrl = self.hrtiDomain + "/" + self.plugin.get_setting('webapiurl') + "/"
        self.hsapiBaseUrl = self.plugin.get_setting('apiurl') + "/"

    def api_post(self, url, payload, referer):

        cookie_header = None
        for cookie in self.session.cookies:
            if cookie.domain == '.hrti.hrt.hr':
                cookie_header = cookie.name + "=" + cookie.value

        headers = {
            'connection': 'keep-alive',
            'deviceid': self.DEVICE_ID,
            'operatorreferenceid': self.__operator_reference_id,
            'authorization': 'Client ' + self.TOKEN,
            'ipaddress': str(self.IP),
            'content-type': 'application/json',
            'accept': 'application/json, text/plain, */*',
            'user-agent': self.__user_agent,
            'devicetypeid': self.__device_reference_id,
            'origin': self.hrtiDomain,
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

    def get_ip(self):
        url = self.hrtiBaseUrl+"getIPAddress"
        r = self.session.get(url)
        if r is not None:
            self.IP = r.json()
            self.plugin.set_setting('ip', self.IP)
        return r.json()

    def get_env(self):
        url = self.hrtiEnvUrl
        r = self.session.get(url)
        if r is not None:
            env = r.json()
            appversion = self.plugin.get_dict_value(env, 'applicationVersion')
            self.plugin.set_setting('applicationversion', str(appversion))
        return r.json()

    def get_conf(self):
        url = self.hrtiConfUrl
        r = self.session.get(url)
        if r is not None:
            conf = r.json()
            apiurl = self.plugin.get_dict_value(conf, 'apiUrl')
            self.plugin.set_setting('apiurl', str(apiurl))
            webapi = self.plugin.get_dict_value(conf, 'webApiUrl')
            self.plugin.set_setting('webapiurl', str(webapi))
            operators = self.plugin.get_dict_value(conf, 'operators')
            hrtop = operators[0]
            merchant = self.plugin.get_dict_value(hrtop, 'playerMerchant')
            self.plugin.set_setting('merchant', str(merchant))
            selfcare = self.plugin.get_dict_value(hrtop, 'selfcareUrl')
            self.plugin.set_setting('selfcareurl', str(selfcare))
        return r.json()

    def grant_access(self, username, password):
        url = self.hrtiBaseUrl+"GrantAccess"

        payload = json.dumps({
            "Username": username,
            "Password": password,
            "OperatorReferenceId": self.__operator_reference_id
        })

        referer = self.hrtiDomain + "/signin"
        result = self.api_post(url, payload, referer)

        if result is not None and username != 'anonymoushrt':
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
            validfrom = self.plugin.get_datetime_from_epoch(tokenvalidfrom)
            validto = self.plugin.get_datetime_from_epoch(tokenvalidto)
            self.plugin.set_setting('validfrom', str(validfrom))
            self.plugin.set_setting('validto', str(validto))
            xbmc.log("hrti grant access: " + str(result), level=xbmc.LOGDEBUG)
        return result

    def is_token_valid(self):
        validfrom = self.plugin.get_setting('validfrom')
        validto = self.plugin.get_setting('validto')
        now = self.plugin.get_time_now()
        # print(validfrom)
        # print(now)
        # print(validto)
        if validfrom <= now <= validto:
            return True
        else:
            return False

    def register_device(self):

        url = self.hsapiBaseUrl+"RegisterDevice"

        payload = json.dumps({
            "DeviceSerial": self.DEVICE_ID,
            "DeviceReferenceId": self.__device_reference_id,
            "IpAddress": str(self.IP),
            "ConnectionType": self.plugin.get_setting('connectiontype'),
            "ApplicationVersion": self.plugin.get_setting('applicationversion'),
            "DrmId":  self.DEVICE_ID,
            "OsVersion": self.plugin.get_setting('osversion'),
            "ClientType": self.plugin.get_setting('clienttype')
        })
        referer = self.hrtiDomain + "/"
        result = self.api_post(url, payload, referer)
        return result

    def get_content_rating(self):

        url = self.hsapiBaseUrl + "ContentRatingsGet"

        payload = json.dumps({})
        referer = self.hrtiDomain + "/"
        result = self.api_post(url, payload, referer)
        return result

    def get_profiles(self):

        url = self.hsapiBaseUrl + "ProfilesGet"

        payload = json.dumps({})
        referer = self.hrtiDomain + "/"
        result = self.api_post(url, payload, referer)
        return result

    def get_channels(self):

        url = self.hrtiBaseUrl + "GetChannels"

        payload = json.dumps({})
        referer = self.hrtiDomain + "/signin"
        result = self.api_post(url, payload, referer)
        if result is None:
            device_id = self.plugin.uniq_id()
            self.plugin.set_setting("device_id", device_id)
            self.register_device()
        return result

    def get_catalog_structure(self):

        url = self.hrtiBaseUrl + "GetCatalogueStructure"

        payload = json.dumps({})
        referer = self.hrtiDomain + "/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_catalog(self, reference_id, max_number, page):

        url = self.hrtiBaseUrl + "GetCatalogue"

        payload = json.dumps({
            "ReferenceId": reference_id,
            "ItemsPerPage": max_number,
            "PageNumber": page,
        })
        referer = self.hrtiDomain + "/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_vod_details(self, reference_id):

        url = self.hrtiBaseUrl + "GetVodDetails"

        payload = json.dumps({
            "ReferenceId": reference_id,
        })
        referer = self.hrtiDomain + "/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_programme(self, channelids, starttime, endtime):

        url = self.hrtiBaseUrl + "GetProgramme"

        payload = json.dumps({
            "ChannelReferenceIds": channelids,
            "StartTime": starttime,
            "EndTime": endtime
        })
        referer = self.hrtiDomain + "/home"
        result = self.api_post(url, payload, referer)
        return result

    def get_epg_details(self, channelid, referenceid):

        url = self.hrtiBaseUrl + "GetEpgDetails"

        payload = json.dumps({
            "ChannelReferenceId": channelid,
            "ReferenceId": referenceid,
        })
        referer = self.hrtiDomain + "/live/programme"
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
            referer = self.hrtiDomain + "/videostore"
        else:
            referer = self.hrtiDomain + "/live/"
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
            referer = self.hrtiDomain + "/videostore"
        else:
            referer = self.hrtiDomain + "/live/"
            referer += "tv?channel=' + str(channelid)"
        result = self.api_post(url, payload, referer)
        return result

    def get_seasons(self, series_ref_id):

        url = self.hrtiBaseUrl + "GetSeasons"

        payload = json.dumps({
            "SeriesReferenceId": series_ref_id
        })
        referer = self.hrtiDomain + "/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_episodes(self, series_ref_id, season_ref_id):

        url = self.hrtiBaseUrl + "GetEpisodes"

        payload = json.dumps({
            "SeriesReferenceId": series_ref_id,
            "SeasonReferenceId": season_ref_id
        })
        referer = self.hrtiDomain + "/videostore"
        result = self.api_post(url, payload, referer)
        return result

    def get_radio_metadata(self, channel_ref_id):

        url = self.hrtiBaseUrl + "GetRadioEventMetadata"

        payload = json.dumps({
            "ChannelReferenceId": channel_ref_id,
        })
        referer = self.hrtiDomain + "/live/radio"
        result = self.api_post(url, payload, referer)
        return result

    def get_watch_later(self):

        url = self.hrtiBaseUrl + "GetWatchLater"

        payload = json.dumps({
        })
        referer = self.hrtiDomain + "/watch_later"
        result = self.api_post(url, payload, referer)
        return result

    def get_editors_choice(self):

        url = self.hrtiBaseUrl + "GetEditorsChoice"

        payload = json.dumps({
        })
        referer = self.hrtiDomain + "/editors_choice"
        result = self.api_post(url, payload, referer)
        return result

    def get_device_instances(self):

        url = self.hsapiBaseUrl + "DeviceInstancesGet"

        payload = json.dumps({
        })
        referer = "https://hrti-selfcare.hrt.hr/"
        result = self.api_post(url, payload, referer)
        return result

    def get_channel_categories(self):

        url = self.hrtiBaseUrl + "GetChannelCategories"

        payload = json.dumps({
        })
        referer = self.hrtiDomain + "/live/programme"
        result = self.api_post(url, payload, referer)
        return result

    def logout(self):

        url = self.hsapiBaseUrl + "DeviceInstanceDelete"

        payload = json.dumps({
            "Serial": self.DEVICE_ID,
        })
        referer = self.hrtiDomain + "/"
        result = self.api_post(url, payload, referer)
        self.plugin.set_setting('token', '')
        self.plugin.set_setting('validfrom', '')
        self.plugin.set_setting('validto', '')
        self.plugin.set_setting('device_id', '')
        return result

    def get_license(self):
        # Prepare for drm keys
        drm_license = {'userId': self.USERID, 'sessionId': self.__drmid, 'merchant': self.__merchant}
        xbmc.log("DRM License: " + str(drm_license), level=xbmc.LOGDEBUG)
        try:
            license_str = base64.b64encode(json.dumps(drm_license))
            return license_str
        except Exception as e:
            license_str = base64.b64encode(json.dumps(drm_license).encode("utf-8"))
            return str(license_str, "utf-8")
