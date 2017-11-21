from core import logger
from core.decoder import Decoder
from core.downloader import Downloader
from core.xbmcutils import XBMCUtils
import urllib

try:
    import json
except:
    import simplejson as json

import sys

class Youtube(Downloader):

    MAIN_URL = "https://www.youtube.com"
    SEARCH_URL = "https://www.youtube.com/results?search_query="

    @staticmethod
    def getChannels(page='0'):
        x = []
        if str(page) == '0':
            page=Youtube.MAIN_URL+"/"
            html = Youtube.getContentFromUrl(page,"",Youtube.cookie,"")
            logger.debug("html: "+html)
            jsonScript = Decoder.extract('ytInitialGuideData = ',';',html)
            x = Youtube.extractMainChannelsJSON(jsonScript)
            element = {}
            element["title"] = XBMCUtils.getString(11018)
            element["page"] = 'search'
            x.append(element)
        elif '/channel/' in page or '/trending' in page:
            headers = Youtube.buildHeaders()
            response = Youtube.getContentFromUrl(url=str(page+"?pbj=1"),headers=headers,launchLocation=True)
            try:
                jsonResponse = json.loads(response)
                logger.debug("parsed json from '"+page+"', continue...")
                logger.debug("json is: "+response)
                try:
                    logger.debug("using way 1...")
                    x = Youtube.extractVideosFromJSON(jsonResponse[1]["response"])
                except:
                    logger.debug("fails way 1, using way 2...")
                    x = Youtube.extractVideosFromSpecialChannelJSON(jsonResponse[1]["response"])
                    pass
            except:
                logger.error("Could not parse response: "+str(response))
                pass
        elif str(page) == 'search':
            keyboard = XBMCUtils.getKeyboard()
            keyboard.doModal()
            text = ""
            if (keyboard.isConfirmed()):
                text = keyboard.getText()
                text = urllib.quote_plus(text)

                headers = Youtube.buildHeaders()
                response = Youtube.getContentFromUrl(url=str(Youtube.SEARCH_URL+text+"?pbj=1"), headers=headers)
                try:
                    jsonResponse = json.loads(response)
                    logger.debug("parsed search json with text: '" + page + "', continue...")
                    x = Youtube.extractVideosFromSpecialChannelJSON(jsonResponse[1]["response"])
                except:
                    logger.error("Could not parse response: " + str(response))
                logger.debug("finished search logic!")
        else:
            element = Youtube.extractTargetVideoJSON(page)
            x.append(element)
        return x

    @staticmethod
    def extractTargetVideoJSON(page):
        title = ''
        link = ''
        thumbnail = ''
        headers = Youtube.buildHeaders()
        response = Youtube.getContentFromUrl(url=str(page + "?pbj=1"), headers=headers)
        logger.debug("response is: "+response)
        try:
            responseJ = Decoder.extract('ytplayer.config = ','};',response)+"}"
            logger.debug("json extracted is: " + responseJ)
            jsonResponse = json.loads(responseJ)
            logger.debug("json loaded")
            bruteVideoInfo = jsonResponse["args"]
            logger.debug("obtained brute video info...")
            title = bruteVideoInfo["title"]
            url = bruteVideoInfo["adaptive_fmts"]
            url = Decoder.extract('url=',",",url)
            url = urllib.unquote(url)
            #url = url[:-1]
            thumbnail = bruteVideoInfo["thumbnail_url"]
            logger.debug("extracted final url: "+url)
            '''
            content = Youtube.getContentFromUrl(url=url)
            logger.debug("content extracted: "+content)
            if '<BaseURL>' in content:
                link = Decoder.rExtract('<BaseURL>','</BaseURL>',content)
            else:
                logger.info("No video url found :(")
                pass
            '''
            logger.debug("parsed video info")
        except:
            logger.error("error parsing video info")
            pass
        element = {}
        element["title"] = title
        element["link"] = link
        element["thumbnail"] = thumbnail
        element["finalLink"] = True
        return element


    @staticmethod
    def buildHeaders():
        headers = {}
        headers["accept-language"] = "es-ES,es;q=0.9"
        headers["x-youtube-client-version"] = "2.20171120"
        headers["user-agent"] = Downloader.USER_AGENT_CHROME
        headers["x-youtube-client-name"] = '1'
        return headers

    @staticmethod
    def extractMainChannelsJSON(jsonScript):
        x = []
        jsonList = json.loads(jsonScript)
        for jsonElement in jsonList['items'][1]["guideSectionRenderer"]["items"]:
            title = ''
            url = ''
            thumbnail = ''
            element = {}
            element2 = jsonElement["guideEntryRenderer"]
            if element2.has_key('title'):
                title = element2['title']
            if element2.has_key('thumbnail'):
                thumbnail = element2['thumbnail']['thumbnails'][0]['url']
                if 'https' not in thumbnail:
                    thumbnail = 'https:'+thumbnail
            if element2.has_key('navigationEndpoint'):
                url = element2['navigationEndpoint']['webNavigationEndpointData']['url']
                if 'youtube.com' not in url:
                    url = 'https://youtube.com'+url
            element = {}
            element["title"] = title
            element["page"] = url
            element["thumbnail"] = thumbnail
            x.append(element)

        return x

    @staticmethod
    def extractVideosFromChannelJSON(jsonScript):
        x = []
        jsonList = json.loads(jsonScript)
        x = Youtube.extractVideosFromJSON(jsonList)
        return x

    @staticmethod
    def extractVideosFromJSON(jsonList):
        x = []
        for jsonElements in jsonList['contents']['twoColumnBrowseResultsRenderer']["tabs"][0]['tabRenderer']['content']['sectionListRenderer']['contents']:
            logger.debug("inside first for...")
            #-> itemSectionRenderer -> contents [0] -> shelfRenderer -> content -> horizontalListRenderer -> items [0-11] (4) -> gridVideoRenderer
            for jsonElement in jsonElements['itemSectionRenderer']['contents'][0]['shelfRenderer']['content']['horizontalListRenderer']['items']:
                logger.debug("inside second for...")
                title = ''
                url = ''
                thumbnail = ''
                element2 = jsonElement["gridVideoRenderer"]
                if element2.has_key('title'):
                    title = element2['title']['simpleText']
                if element2.has_key('thumbnail'):
                    thumbnail = element2['thumbnail']['thumbnails'][0]['url']
                    if 'https' not in thumbnail:
                        thumbnail = 'https:' + thumbnail
                if element2.has_key('videoId'):
                    url = element2['videoId']
                    url = 'https://youtube.com/watch?v='+url
                element = {}
                element["title"] = title
                element["page"] = url
                element["thumbnail"] = thumbnail
                element["finalLink"] = True
                logger.debug("append: "+title+", page: "+url+", thumb: "+thumbnail)
                x.append(element)
        return x

    @staticmethod
    def extractVideosFromSpecialChannelJSON(jsonScript):
        x = []
        jsonList = json.loads(jsonScript)
        if jsonList['contents']['twoColumnBrowseResultsRenderer'].has_key('tabs'):
            targets = jsonList['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']
        elif jsonList['contents']['twoColumnBrowseResultsRenderer'].has_key('primaryContents'):
            targets = jsonList['contents']['twoColumnBrowseResultsRenderer']['primaryContents']
        for jsonElements in targets['sectionListRenderer']['contents']:
            if jsonList['contents']['twoColumnBrowseResultsRenderer'].has_key('tabs'):
                content = jsonElements['itemSectionRenderer']['contents'][0]['shelfRenderer']['content']
                if content.has_key('horizontalListRenderer'):
                    for jsonElement in content['horizontalListRenderer']['items']:
                        element2 = jsonElement["gridVideoRenderer"]
                        element = Youtube.extractVideoElement(element2)
                        x.append(element)
                if content.has_key('expandedShelfContentsRenderer'):
                    for jsonElement in content['expandedShelfContentsRenderer']['items']:
                        element2 = jsonElement["videoRenderer"]
                        element = Youtube.extractVideoElement(element2)
                        x.append(element)
            else: #search
                content = jsonElements['itemSectionRenderer']['contents']
                for jsonElement in content:
                    element2 = jsonElement["videoRenderer"]
                    element = Youtube.extractVideoElement(element2)
                    x.append(element)

        return x

    @staticmethod
    def extractVideoElement(element2):
        title = ''
        url = ''
        thumbnail = ''
        if element2.has_key('title'):
            title = element2['title']['simpleText']
        if element2.has_key('thumbnails'):
            thumbnail = element2['thumbnail']['thumbnails'][0]['url']
            if 'https' not in thumbnail:
                thumbnail = 'https:' + thumbnail
        if element2.has_key('videoId'):
            url = element2['videoId']
            url = 'https://youtube.com/watch?v=' + url
        element = {}
        element["title"] = title
        element["page"] = url
        element["thumbnail"] = thumbnail
        element["finalLink"] = True
        return element