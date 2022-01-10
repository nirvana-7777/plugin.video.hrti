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
from lib.hrti_api2 import HRTiAPI
from lib.common import Common

_HANDLE = int(sys.argv[1])
_URL = sys.argv[0]

plugin = Common(
    addon=xbmcaddon.Addon(),
    addon_handle=_HANDLE,
    addon_url=_URL
)

api = HRTiAPI(plugin)
channels = api.get_channels()
catalog_structure = api.get_catalog_structure()

CATEGORIES = ['TV Channels', 'Radio Channels']


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
    current_node = catalog_structure
    parent_category = ""
    if path is not None:
        sections = path_parse("/"+path)
        i = 0
        while i < len(sections):
            current_node = get_children(current_node, sections[i])
            parent_category = sections[i]
            i += 1
    count = 0
    for child in current_node:
        if child['ParentReferenceId'] == parent_category:
            list_item = xbmcgui.ListItem(label=plugin.get_dict_value(child, 'Name'))
            list_item.setArt({'thumb': plugin.get_dict_value(child, 'PosterLandscape'),
                              'fanart': plugin.get_dict_value(child, 'PosterLandscape')})
            list_item.setInfo('video', {'title': plugin.get_dict_value(child, 'Name'),
                                        'genre': plugin.get_dict_value(child, 'Name'),
                                        'mediatype': 'video'})
            if path is None:
                url = get_url(action='listing', category=plugin.get_dict_value(child, 'ReferenceId'))
            else:
                url = get_url(action='listing', category=path+"/"+plugin.get_dict_value(child, 'ReferenceId'))
            is_folder = True
            xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
            count += 1
    if count == 0:
        catalog = api.get_catalog(parent_category, 250, 1)
        # number = catalog['NumberOfItems']
        # print(catalog)
        for catalog_entry in catalog['Items']:
            title = plugin.get_dict_value(catalog_entry, 'Title')
            landscape = plugin.get_dict_value(catalog_entry, 'PosterLandscape')
            portrait = plugin.get_dict_value(catalog_entry, 'PosterPortrait')
            # catalog_entry['VodData'] AvailableFrom, Duration, ProductionYear

            series_data = plugin.get_dict_value(catalog_entry, 'SeriesData')
            if len(series_data) == 0:
                item_is_series = False
            else:
                item_is_series = True

            # catalog_entry['SeriesData'] {'LastEpisodeNumber': 1,
            # 'LastSeasonNumber': 1, 'SeriesName': '',
            # 'SeriesReferenceId': '44425aa1-0a72-7f51-9371-046be46ed537'}
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
                url = get_url(action='play', video=plugin.get_dict_value(catalog_entry, 'ReferenceId'))
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
    xbmcplugin.setPluginCategory(_HANDLE, 'My Video Collection')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_HANDLE, 'videos')
    # Get video categories
    categories = get_categories()
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.

        # list_item.setArt({'thumb': VIDEOS[category][0]['thumb'],
        #                'icon': VIDEOS[category][0]['thumb'],
        #               'fanart': VIDEOS[category][0]['thumb']})

        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
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
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    # xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


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
    for channel in channels:
        if (plugin.get_dict_value(channel, 'Radio') and category == 'Radio Channels')\
                or (not plugin.get_dict_value(channel, 'Radio') and category == 'TV Channels'):
            list_item = xbmcgui.ListItem(label=plugin.get_dict_value(channel, 'Name'))
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

            url = get_url(action='play', video=plugin.get_dict_value(channel, 'StreamingURL'))
            # Add the list item to a virtual Kodi folder.
            # is_folder = False means that this item won't open any sub-list.
            is_folder = False
            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
            # Add a sort method for the virtual folder items (alphabetically, ignore articles)
            # xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


def authorize_and_play(filename, contenttype, content_ref_id, video_store_ids, channel_id):
    print("Filename: "+filename)
    parts = urlparse(filename)
    directories = parts.path.strip('/').split('/')
    contentdrmid = directories[0] + "_" + directories[1]
    result = api.authorize_session(contenttype, content_ref_id, contentdrmid, video_store_ids, channel_id)
    api.report_session_event(plugin.get_dict_value(result, 'SessionId'), content_ref_id)

    user_agent = "kodi plugin for hrti.hrt.hr (python)"

    license_str = api.get_license()
    list_item = xbmcgui.ListItem(path=filename)

    list_item.setMimeType('application/xml+dash')
    list_item.setContentLookup(False)

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
    seasons = api.get_seasons(ref_id)
    xbmcplugin.setPluginCategory(_HANDLE, 'Seasons')
    xbmcplugin.setContent(_HANDLE, 'tvshows')
    for season in seasons:
        list_item = xbmcgui.ListItem(label=plugin.get_dict_value(season, 'Title'))
        list_item.setArt({'thumb': plugin.get_dict_value(season, 'PosterLandscape'),
                          'icon': plugin.get_dict_value(season, 'PosterLandscape'),
                          'fanart': plugin.get_dict_value(season, 'PosterPortrait')})
        list_item.setInfo('video', {'title': plugin.get_dict_value(season, 'Title'),
                                    'genre': plugin.get_dict_value(season, 'Title'),
                                    'mediatype': 'video'})
        url = get_url(action='episodes', category=ref_id+'/'+plugin.get_dict_value(season, 'ReferenceId'))
        is_folder = True
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_HANDLE)


def list_episodes(ref_id):
    xbmcplugin.setPluginCategory(_HANDLE, 'Episodes')
    xbmcplugin.setContent(_HANDLE, 'episodes')
    sections = path_parse("/" + ref_id)
    series_id = sections[0]
    season_id = sections[1]
    episodes = api.get_episodes(series_id, season_id)
    for episode in episodes:
        list_item = xbmcgui.ListItem(label=plugin.get_dict_value(episode, 'Title'))
        list_item.setArt({'thumb': plugin.get_dict_value(episode, 'PosterLandscape'),
                          'icon': plugin.get_dict_value(episode, 'PosterLandscape'),
                          'fanart': plugin.get_dict_value(episode, 'PosterPortrait')})
        list_item.setInfo('video', {'title': plugin.get_dict_value(episode, 'Title'),
                                    'genre': plugin.get_dict_value(episode, 'Title'),
                                    'mediatype': 'video'})
        list_item.setProperty('IsPlayable', 'true')
        metadata = {'mediatype': 'video'}
        list_item.setInfo('video', metadata)

        url = get_url(action='play', video=plugin.get_dict_value(episode, 'ReferenceId'))
        is_folder = False
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    xbmcplugin.endOfDirectory(_HANDLE)


def play_video(path):
    """
    Play a video by the provided path.
    :param path: Fully-qualified video URL
    :type path: str
    """
    parts = urlparse(path)
    if parts.scheme == "":
        voddetails = api.get_vod_details(path)
        print(voddetails)
        filename = plugin.get_dict_value(voddetails, 'FileName')
        content_type = plugin.get_dict_value(voddetails, 'Type')
        video_store_ids = plugin.get_dict_value(voddetails, 'SVODVideostores')
        if content_type != 'series':
            authorize_and_play(filename, content_type, path, video_store_ids, None)
    else:
        for channel in channels:
            if path == plugin.get_dict_value(channel, 'StreamingURL'):
                refid = plugin.get_dict_value(channel, 'ReferenceID')
                if plugin.get_dict_value(channel, 'Radio'):
                    content_type = "rlive"
                else:
                    content_type = "tlive"
                authorize_and_play(path, content_type, refid, None, refid)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    deviceid = plugin.uniq_id()
    api.DEVICE_ID = deviceid
    xbmc.log("DeviceID: "+str(deviceid),  level=xbmc.LOGDEBUG)

    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    print("Params" + str(params))
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            if params['category'] == 'TV Channels' or params['category'] == 'Radio Channels':
                list_videos(params['category'])
            else:
                list_subcategories(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        elif params['action'] == 'series':
            # Play a video from a provided URL.
            list_seasons(params['category'])
        elif params['action'] == 'episodes':
            # Play a video from a provided URL.
            list_episodes(params['category'])
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