# Module: main
# Author: Nirvana
# Created on: 20.12.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Example video plugin that is compatible with Kodi 19.x "Matrix" and above
"""
import sys
from urllib.parse import urlencode, urlparse, parse_qsl
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import posixpath
from lib.hrti_api import HRTiAPI
from lib.common import Common

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer


_HANDLE = int(sys.argv[1])
_URL = sys.argv[0]

plugin = Common(
    addon=xbmcaddon.Addon(),
    addon_handle=_HANDLE,
    addon_url=_URL
)

cache = StorageServer.StorageServer("HRTi", 24)
api = HRTiAPI(plugin)
username = plugin.get_setting("username")
password = plugin.get_setting("password")
token = plugin.get_setting("token")
userid = plugin.get_setting("customerid")
ip = plugin.get_setting("ip")
if token == '' or \
        token == 'lAWX321gC0Gc5c4d7QGg3g7CbuTPbavEeQuhKRyebvaQWEaWO2N8kmqwKNSUc8Gw' or \
        userid == "" or \
        ip == "":
    api.get_ip()
    api.get_env()
    api.get_conf()
    login_result = api.grant_access(username, password)
    if login_result is None:
        plugin.dialog_ok("Login has failed, check credentials! Using default credentials for this session")
        api.grant_access('anonymoushrt', 'an0nPasshrt')
    api.register_device()
    api.get_content_rating()
    api.get_profiles()
else:
    api.USERID = userid
    api.TOKEN = token
    api.IP = ip
device_id = plugin.get_setting("device_id")
if device_id == "":
    device_id = plugin.uniq_id()
    plugin.set_setting("device_id", device_id)
    api.register_device()
    api.get_content_rating()
    api.get_profiles()
api.DEVICE_ID = device_id
xbmc.log("UserID: " + str(api.USERID), level=xbmc.LOGDEBUG)
xbmc.log("Token: " + str(api.TOKEN), level=xbmc.LOGDEBUG)
xbmc.log("DeviceID: " + str(api.DEVICE_ID), level=xbmc.LOGDEBUG)

CATEGORIES = [plugin.addon.getLocalizedString(30030),
              plugin.addon.getLocalizedString(30031),
              plugin.addon.getLocalizedString(30032)]


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.
    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return '{}?{}'.format(_URL, urlencode(kwargs))


def get_categories():
    """
    Get the list of video categories.
    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or API.
    .. note:: Consider using `generator functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.
    :return: The list of video categories
    :rtype: types.GeneratorType
    """
    return CATEGORIES


def path_parse(path_string, *, normalize=True, module=posixpath):
    result = []
    if normalize:
        tmp = module.normpath(path_string)
    else:
        tmp = path_string
    while tmp != "/":
        (tmp, item) = module.split(tmp)
        result.insert(0, item)
    return result


def get_children(node, wanted_subcategory):
    children = None
    for child in node:
        if plugin.get_dict_value(child, 'ReferenceId') == wanted_subcategory:
            children = plugin.get_dict_value(child, 'Children')
    return children


def list_subcategories(path):
    current_node = cache.cacheFunction(api.get_catalog_structure)
    parent_category = ""
    if path is not None:
        sections = path_parse("/" + path)
        i = 0
        while i < len(sections):
            current_node = get_children(current_node, sections[i])
            parent_category = sections[i]
            i += 1
    count = 0
    xbmcplugin.setPluginCategory(_HANDLE, parent_category)
    for child in current_node:
        if plugin.get_dict_value(child, 'ParentReferenceId') == parent_category:
            list_item = xbmcgui.ListItem(label=plugin.get_dict_value(child, 'Name'))
            landscape = plugin.get_dict_value(child, 'PosterLandscape')
            list_item.setArt({'thumb': landscape,
                              'icon': landscape,
                              'fanart': landscape})
            list_item.setInfo('video', {'title': plugin.get_dict_value(child, 'Name'),
                                        'genre': plugin.get_dict_value(child, 'Name'),
                                        'mediatype': 'video'})
            if path is None:
                url = get_url(action='listing', category=plugin.get_dict_value(child, 'ReferenceId'))
            else:
                url = get_url(action='listing', category=path + "/" + plugin.get_dict_value(child, 'ReferenceId'))
            is_folder = True
            xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
            count += 1
    if count == 0:
        catalog = cache.cacheFunction(api.get_catalog, parent_category, 250, 1)
        # number = catalog['NumberOfItems'] TODO: handle more than 250 items
        for catalog_entry in catalog['Items']:
            title = plugin.get_dict_value(catalog_entry, 'Title')
            landscape = plugin.get_dict_value(catalog_entry, 'PosterLandscape')
            portrait = plugin.get_dict_value(catalog_entry, 'PosterPortrait')
            # catalog_entry['VodData'] AvailableFrom, Duration, ProductionYear
            # TODO: additional info from VodData
            series_data = plugin.get_dict_value(catalog_entry, 'SeriesData')
            if len(series_data) == 0:
                item_is_series = False
            else:
                item_is_series = True

            # catalog_entry['Type']
            # catalog_entry['VodCategoryNames']
            # catalog_entry['AvailableFrom']
            list_item = xbmcgui.ListItem(label=title)
            list_item.setArt({'thumb': landscape,
                              'icon': landscape,
                              'fanart': portrait})
            if not item_is_series:
                list_item.setProperty('IsPlayable', 'true')
                metadata = {'mediatype': 'video'}
                list_item.setInfo('video', metadata)
                vid_ref = plugin.get_dict_value(catalog_entry, 'ReferenceId')
                url = get_url(action='play', video=vid_ref)
                cm = [(plugin.addon.getLocalizedString(30033),
                       'RunPlugin(plugin://plugin.video.hrti/?action=voddetails&id=' + str(vid_ref) + ')')]
                list_item.addContextMenuItems(cm, replaceItems=False)
                # Add the list item to a virtual Kodi folder.
                # is_folder = False means that this item won't open any sub-list.
                is_folder = False
            else:
                url = get_url(action='series', category=plugin.get_dict_value(series_data, 'SeriesReferenceId'))
                is_folder = True
            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)

    if path is not None:
        xbmcplugin.endOfDirectory(_HANDLE)


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_HANDLE, 'HRTi categories')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_HANDLE, 'videos')
    # Get video categories
    categories = get_categories()
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        list_item.setInfo('video', {'title': category,
                                    'genre': category,
                                    'mediatype': 'video'})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', category=category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    list_subcategories(None)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


def get_now_event(epg_list):
    now_event = None
    if epg_list is not None:
        now = plugin.get_time_now()
        for event in epg_list:
            event_start = plugin.get_dict_value(event, 'TimeStartUnixEpoch')
            event_end = plugin.get_dict_value(event, 'TimeEndUnixEpoch')
            if event_start <= now <= event_end:
                now_event = event
    return now_event


def list_videos(category):
    """
    Create the list of playable videos in the Kodi interface.
    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_HANDLE, category)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_HANDLE, 'videos')
    # Get the list of videos in the category.
    # Iterate through videos.
    channels = cache.cacheFunction(api.get_channels)
    if channels is not None:
        channelids = []
        for channel in channels:
            channelids.append(plugin.get_dict_value(channel, 'ReferenceId'))
        start = "/Date(" + str(plugin.get_time_offset(-4)) + ")/"
        end = "/Date(" + str(plugin.get_time_offset(4)) + ")/"
        programmes = cache.cacheFunction(api.get_programme, channelids, start, end)
        for channel in channels:
            if (plugin.get_dict_value(channel, 'Radio') and category == plugin.addon.getLocalizedString(30031)) or \
                    (not plugin.get_dict_value(channel, 'Radio') and category == plugin.addon.getLocalizedString(30030)):
                channel_epg = None
                for programme in programmes:
                    if plugin.get_dict_value(programme, 'ReferenceID') == plugin.get_dict_value(channel, 'ReferenceId'):
                        channel_epg = plugin.get_dict_value(programme, 'EpgList')
                if channel_epg is not None:
                    now = get_now_event(channel_epg)
                else:
                    now = None
                label = plugin.get_dict_value(channel, 'Name') + str(" | ") + plugin.get_dict_value(now, 'Title')
                list_item = xbmcgui.ListItem(label=label)
                list_item.setArt({'thumb': plugin.get_dict_value(channel, 'Icon'),
                                  'icon': plugin.get_dict_value(channel, 'Icon'),
                                  'fanart': plugin.get_dict_value(channel, 'Icon')})
                list_item.setProperty('IsPlayable', 'true')

                # for video in videos:
                # Create a list item with a text label and a thumbnail image.
                # list_item = xbmcgui.ListItem(label=video['name']
                # Set additional info for the list item.
                # 'mediatype' is needed for skin to display info for this ListItem correctly.
                if plugin.get_dict_value(channel, 'Radio'):
                    metadata = {'mediatype': 'audio'}
                    list_item.setInfo('music', metadata)
                else:
                    metadata = {'mediatype': 'video'}
                    list_item.setInfo('video', metadata)

                url = get_url(action='play',
                              video=plugin.get_dict_value(channel, 'StreamingURL'),
                              referenceid=plugin.get_dict_value(now, 'ReferenceId'))
                # Add the list item to a virtual Kodi folder.
                # is_folder = False means that this item won't open any sub-list.
                is_folder = False
                # Add our item to the Kodi virtual folder listing.
                xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
            elif category == plugin.addon.getLocalizedString(30032):
                list_item = xbmcgui.ListItem(label=plugin.get_dict_value(channel, 'Name'))
                list_item.setArt({'thumb': plugin.get_dict_value(channel, 'Icon'),
                                  'icon': plugin.get_dict_value(channel, 'Icon'),
                                  'fanart': plugin.get_dict_value(channel, 'Icon')})
                url = get_url(action='EPG', channel=plugin.get_dict_value(channel, 'ReferenceId'))
                is_folder = True
                # Add our item to the Kodi virtual folder listing.
                xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    # xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


def list_epg(channel):
    channelids = [channel]
    epg_before = -int(plugin.get_setting("epgbefore"))
    epg_after = int(plugin.get_setting("epgafter"))
    start = "/Date(" + str(plugin.get_time_offset(epg_before)) + ")/"
    end = "/Date(" + str(plugin.get_time_offset(epg_after)) + ")/"
    programmes = cache.cacheFunction(api.get_programme, channelids, start, end)
    xbmcplugin.setContent(_HANDLE, 'images')
    if programmes is not None:
        programme = programmes[0]
        epglist = plugin.get_dict_value(programme, 'EpgList')
        timenow = plugin.get_datetime_now()
        for item in epglist:
            timestart = str(plugin.get_date_from_epoch(plugin.get_dict_value(item, 'TimeStart'))) + \
                        " | " + str(plugin.get_time_from_epoch(plugin.get_dict_value(item, 'TimeStart')))
            entry = timestart + " | " + plugin.get_dict_value(item, 'Title')
            event_is_finished = timenow > plugin.get_datetime_from_epoch(plugin.get_dict_value(item, 'TimeEnd'))
            if event_is_finished:
                entry = '[COLOR green]' + entry + '[/COLOR]'
            list_item = xbmcgui.ListItem(label=entry)
            list_item.setArt({'thumb': plugin.get_dict_value(item, 'ImagePath'),
                              'icon': plugin.get_dict_value(programme, 'Icon'),
                              'fanart': plugin.get_dict_value(item, 'ImagePath')})
            epg_ref = plugin.get_dict_value(item, 'ReferenceId')
            url = get_url(action='play', video=str(channelids[0]), referenceid=epg_ref)
            list_item.setProperty('IsPlayable', 'true')
            cm = [(plugin.addon.getLocalizedString(30033),
                   'RunPlugin(plugin://plugin.video.hrti/?action=epgdetails&channel=' +
                   str(channelids[0]) + '&id=' + str(epg_ref) + ')')]
            list_item.addContextMenuItems(cm, replaceItems=False)
            if plugin.get_dict_value(programme, 'Radio'):
                metadata = {'mediatype': 'audio'}
                list_item.setInfo('music', metadata)
            else:
                metadata = {'mediatype': 'video'}
                list_item.setInfo('video', metadata)
            is_folder = False
            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_HANDLE)


def get_category_text(cat_id):
    categories = cache.cacheFunction(api.get_channel_categories)
    for category in categories:
        if plugin.get_dict_value(category, 'ReferenceID') == str(cat_id):
            return plugin.get_dict_value(category, 'Name')
    return ''


def get_metadata_vod(vod_details):
    actors = plugin.get_dict_value(vod_details, 'Actors')
    if actors is None:
        actors = ''
    directors = plugin.get_dict_value(vod_details, 'Directors')
    if directors is None:
        directors = ''
    rating = plugin.get_dict_value(vod_details, 'ContentRating')
    rating_str = ""
    if rating is not None and rating != "":
        rating_str = "PG-"+str(rating)

    metadata = {'plot': plugin.get_dict_value(vod_details, 'Description'),
                'genre': plugin.get_dict_value(vod_details, 'AssetCategory'),
                'cast': actors.split(","),
                'director': directors.split(","),
                'writer': plugin.get_dict_value(vod_details, 'Writers'),
                'episode': plugin.get_dict_value(vod_details, 'EpisodeNr'),
                'season': plugin.get_dict_value(vod_details, 'SeasonNr'),
                'year': plugin.get_dict_value(vod_details, 'ProductionYear'),
                'rating': plugin.get_dict_value(vod_details, 'AssetRatingAverage'),
                'studio': plugin.get_dict_value(vod_details, 'Producers'),
                'country': plugin.get_dict_value(vod_details, 'ProductionCountries'),
                'duration': int(plugin.get_dict_value(vod_details, 'DurationInFrames') / 1500),
                'mpaa': rating_str}
    return metadata


def parse_credits(epg_credits):
    cast = []
    directors = []
    for credit in epg_credits:
        role = plugin.get_dict_value(credit, 'Role')
        if role == 'actor':
            cast.append(plugin.get_dict_value(credit, 'Value'))
        if role == 'director':
            directors.append(plugin.get_dict_value(credit, 'Value'))
    return cast, directors


def get_metadata_epg(epg_details):
    category_reference = plugin.get_dict_value(epg_details, 'CategoryReferenceID')
    try:
        int(category_reference)
        category_text = get_category_text(category_reference)
    except ValueError:
        category_text = category_reference
    rating = plugin.get_dict_value(epg_details, 'ContentRating')
    rating_str = ""
    if rating is not None and rating != "":
        rating_str = "PG-"+str(rating)
    epg_credits = plugin.get_dict_value(epg_details, 'Credits')
    cast, directors = parse_credits(epg_credits)
    episode = plugin.get_dict_value(epg_details, 'EpisodeNr')
    season = plugin.get_dict_value(epg_details, 'SeasonNr')

    if episode != '' or season != '':
        metadata = {'plot': plugin.get_dict_value(epg_details, 'DescriptionLong'),
                    'plotoutline': plugin.get_dict_value(epg_details, 'DescriptionShort'),
                    'duration': int(plugin.get_dict_value(epg_details, 'Duration')) * 60,
                    'episode': episode,
                    'season': season,
                    'cast': cast,
                    'director': directors,
                    'genre': category_text,
                    'mpaa': rating_str}
    else:
        metadata = {'plot': plugin.get_dict_value(epg_details, 'DescriptionLong'),
                    'plotoutline': plugin.get_dict_value(epg_details, 'DescriptionShort'),
                    'duration': int(plugin.get_dict_value(epg_details, 'Duration')) * 60,
                    'cast': cast,
                    'director': directors,
                    'genre': category_text,
                    'mpaa': rating_str}
    return metadata


def authorize_and_play(filename, contenttype, content_ref_id, video_store_ids,
                       channel_id, epg_ref_id, starttime, endtime):
    parts = urlparse(filename)
    directories = parts.path.strip('/').split('/')
    contentdrmid = str(directories[0]) + "_" + str(directories[1])
    result = api.authorize_session(contenttype, content_ref_id, contentdrmid,
                                   video_store_ids, channel_id, starttime, endtime)
    authorized = plugin.get_dict_value(result, 'Authorized')
    if not authorized:
        plugin.dialog_ok("Authorization has failed - Check Credentials - Relogin")
    if not api.report_session_event(plugin.get_dict_value(result, 'SessionId'), content_ref_id):
        plugin.dialog_ok("Report Session has failed - Re-login")
    user_agent = "kodi plugin for hrti.hrt.hr (python)"

    license_str = api.get_license()
    list_item = xbmcgui.ListItem(path=filename)

    list_item.setMimeType('application/xml+dash')
    list_item.setContentLookup(False)

    if contenttype == "episode" or contenttype == "vod":
        vod_details = cache.cacheFunction(api.get_vod_details, content_ref_id)
        metadata = get_metadata_vod(vod_details)
        list_item.setInfo('video', metadata)
        subtitles = plugin.get_dict_value(vod_details, 'Subtitles')
        if subtitles is not None:
            sl = []
            for subtitle in subtitles:
                sl.append(plugin.get_dict_value(subtitle, 'SubtitleURL'))
            list_item.setSubtitles(sl)

    if epg_ref_id is not None:
        epg_details = cache.cacheFunction(api.get_epg_details, channel_id, epg_ref_id)
        metadata = get_metadata_epg(epg_details)
        list_item.setInfo('video', metadata)
        list_item.setArt({'thumb': plugin.get_dict_value(epg_details, 'ImagePath')})

    list_item.setProperty('inputstream', 'inputstream.adaptive')
    list_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    list_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    list_item.setProperty('inputstream.adaptive.license_key',
                          "https://lic.drmtoday.com/license-proxy-widevine/cenc/" +
                          "|User-Agent=" + user_agent +
                          "&Content-Type=text%2Fplain" +
                          "&origin=https://hrti.hrt.hr" +
                          "&referer=https://hrti.hrt.hr" +
                          "&dt-custom-data=" + license_str + "|R{SSM}|JBlicense")

    list_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')

    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=list_item)


def list_seasons(ref_id):
    seasons = cache.cacheFunction(api.get_seasons, ref_id)
    xbmcplugin.setPluginCategory(_HANDLE, 'Seasons')
    xbmcplugin.setContent(_HANDLE, 'tvshows')
    for season in seasons:
        list_item = xbmcgui.ListItem(label=plugin.get_dict_value(season, 'Title'))
        list_item.setArt({'thumb': plugin.get_dict_value(season, 'PosterLandscape'),
                          'icon': plugin.get_dict_value(season, 'PosterLandscape'),
                          'fanart': plugin.get_dict_value(season, 'PosterPortrait')})
        list_item.setInfo('video', {'title': plugin.get_dict_value(season, 'Title'),
                                    'genre': plugin.get_dict_value(season, 'VodCategoryNames'),
                                    'mediatype': 'video'})
        vid_ref = plugin.get_dict_value(season, 'ReferenceId')
        cm = [(plugin.addon.getLocalizedString(30033),
               'RunPlugin(plugin://plugin.video.hrti/?action=voddetails&id=' + str(vid_ref) + ')')]
        list_item.addContextMenuItems(cm, replaceItems=False)
        url = get_url(action='episodes', category=ref_id + '/' + vid_ref)
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_HANDLE)


def list_episodes(ref_id):
    xbmcplugin.setPluginCategory(_HANDLE, 'Episodes')
    xbmcplugin.setContent(_HANDLE, 'episodes')
    sections = path_parse("/" + ref_id)
    series_id = sections[0]
    season_id = sections[1]
    episodes = cache.cacheFunction(api.get_episodes, series_id, season_id)
    for episode in episodes:
        episode_data = plugin.get_dict_value(episode, 'EpisodeData')
        list_item = xbmcgui.ListItem(label=plugin.get_dict_value(episode, 'Title'))
        list_item.setArt({'thumb': plugin.get_dict_value(episode, 'PosterLandscape'),
                          'icon': plugin.get_dict_value(episode, 'PosterLandscape'),
                          'fanart': plugin.get_dict_value(episode, 'PosterPortrait')})
        list_item.setInfo('video', {'title': plugin.get_dict_value(episode, 'Title'),
                                    'season': plugin.get_dict_value(episode_data, 'SeasonNr'),
                                    'episode': plugin.get_dict_value(episode_data, 'EpisodeNr'),
                                    'mpaa': "PG-" + str(plugin.get_dict_value(episode_data, 'ContentRating')),
                                    'mediatype': 'video'})
        list_item.setProperty('IsPlayable', 'true')
        vid_ref = plugin.get_dict_value(episode, 'ReferenceId')
        cm = [(plugin.addon.getLocalizedString(30033),
               'RunPlugin(plugin://plugin.video.hrti/?action=voddetails&id=' + str(vid_ref) + ')')]
        list_item.addContextMenuItems(cm, replaceItems=False)

        url = get_url(action='play', video=vid_ref)
        is_folder = False
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_HANDLE)


def display_info(ref_id):
    vod_details = cache.cacheFunction(api.get_vod_details, ref_id)
    metadata = get_metadata_vod(vod_details)
    list_item = xbmcgui.ListItem(label=plugin.get_dict_value(vod_details, 'Title'))
    list_item.setInfo('video', metadata)
    list_item.setArt({'poster': plugin.get_dict_value(vod_details, 'PosterPortrait'),
                      'landscape': plugin.get_dict_value(vod_details, 'PosterLandscape')})
    dialog = xbmcgui.Dialog()
    dialog.info(list_item)


def display_epg(channel_id, ref_id):
    epg_details = cache.cacheFunction(api.get_epg_details, channel_id, ref_id)
    metadata = get_metadata_epg(epg_details)
    list_item = xbmcgui.ListItem(label=plugin.get_dict_value(epg_details, 'Title'))
    list_item.setInfo('video', metadata)
    list_item.setArt({'poster': plugin.get_dict_value(epg_details, 'ImagePath'),
                      'landscape': plugin.get_dict_value(epg_details, 'ImagePath')})
    dialog = xbmcgui.Dialog()
    dialog.info(list_item)


def play_video(path, epg_ref_id):
    """
    Play a video by the provided path.
    :param path: Fully-qualified video URL
    :param epg_ref_id EPG Reference
    :type path: str
    """
    parts = urlparse(path)
    if epg_ref_id is None:
        voddetails = cache.cacheFunction(api.get_vod_details, path)
        filename = plugin.get_dict_value(voddetails, 'FileName')
        if filename is not None:
            content_type = plugin.get_dict_value(voddetails, 'Type')
            video_store_ids = plugin.get_dict_value(voddetails, 'SVODVideostores')
            if content_type != 'series':
                authorize_and_play(filename, content_type, path, video_store_ids, None, None, None, None)
        else:
            api.register_device()
    else:
        channels = cache.cacheFunction(api.get_channels)
        for channel in channels:
            if parts.scheme == "":
                refid = plugin.get_dict_value(channel, 'ReferenceID')
                if path == refid:
                    event = cache.cacheFunction(api.get_epg_details, refid, epg_ref_id)
                    metadata = {'plot': plugin.get_dict_value(event, 'DescriptionLong'),
                                'plotoutline': plugin.get_dict_value(event, 'DescriptionShort')}
                    timeend = plugin.get_datetime_from_epoch(plugin.get_dict_value(event, 'TimeEnd'))
                    if plugin.get_datetime_now() < timeend:
                        url = plugin.get_dict_value(channel, 'StreamingUrl')
                        if plugin.get_dict_value(channel, 'Radio'):
                            content_type = "rlive"
                        else:
                            content_type = "tlive"
                        list_item = xbmcgui.ListItem(path=url)
                        list_item.setInfo('video', metadata)
                        list_item.setArt({'thumb': plugin.get_dict_value(event, 'ImagePath'),
                                          'fanart': plugin.get_dict_value(event, 'ImagePath')})
                        authorize_and_play(url, content_type, refid, None, refid, epg_ref_id, None, None)
                    else:
                        url = plugin.get_dict_value(event, 'FileName')
                        if plugin.get_dict_value(channel, 'Radio'):
                            content_type = "thepg"
                        else:
                            content_type = "thepg"
                        authorize_and_play(url, content_type, epg_ref_id, None, refid,
                                           epg_ref_id, plugin.get_dict_value(event, 'TimeStart'),
                                           plugin.get_dict_value(event, 'TimeEnd'))
            else:
                if path == plugin.get_dict_value(channel, 'StreamingURL'):
                    refid = plugin.get_dict_value(channel, 'ReferenceID')
                    if plugin.get_dict_value(channel, 'Radio'):
                        content_type = "rlive"
                    else:
                        content_type = "tlive"
                    authorize_and_play(path, content_type, refid, None, refid, epg_ref_id, None, None)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    xbmc.log(("Params: " + str(params)), level=xbmc.LOGDEBUG)
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            if params['category'] == plugin.addon.getLocalizedString(30030) or \
                    params['category'] == plugin.addon.getLocalizedString(30031) or \
                    params['category'] == plugin.addon.getLocalizedString(30032):
                list_videos(params['category'])
            else:
                list_subcategories(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            try:
                epg_ref_id = params['referenceid']
            except KeyError:
                epg_ref_id = None
            play_video(params['video'], epg_ref_id)
        elif params['action'] == 'series':
            # Play a video from a provided URL.
            list_seasons(params['category'])
        elif params['action'] == 'episodes':
            # Play a video from a provided URL.
            list_episodes(params['category'])
        elif params['action'] == 'EPG':
            list_epg(params['channel'])
        elif params['action'] == 'voddetails':
            display_info(params['id'])
        elif params['action'] == 'epgdetails':
            display_epg(params['channel'], params['id'])
        elif params['action'] == 'logout':
            api.logout()
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
