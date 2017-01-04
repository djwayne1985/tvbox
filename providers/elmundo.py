import time
import re

import CommonFunctions as common

from core.downloader import Downloader
from core.decoder import Decoder
from core import logger

class ElMundo(Downloader):

    MAIN_URL = "http://www.elmundo.es"
    LAST_NEWS_RSS = "http://estaticos.elmundo.es/elmundo/rss/portada.xml"

    @staticmethod
    def getChannels(page):
        x = []
        if page == '0':
            url = ElMundo.LAST_NEWS_RSS
            logger.debug("news rss url is: "+url)
            bruteResult = ElMundo.getContentFromUrl(url=url,launchLocation=True,ajax=False,referer=ElMundo.MAIN_URL)
            logger.debug("brute response: "+bruteResult)
            lists = common.parseDOM(bruteResult, "item")
            if len(lists) > 0:
                logger.info("counted: " + str(len(lists)))
                for item in lists:
                    name = common.parseDOM(item, "title")[0].encode("utf-8")
                    link = common.parseDOM(item, "link")[0].encode("utf-8")
                    logger.info("Added: " + name + ", url: " + link)
                    element = {}
                    element["title"] = name.replace('<![CDATA[','').replace("]]>","")
                    element["link"] = link
                    try:
                        img = common.parseDOM(item, "media:content", ret="url")[0].encode("utf-8")
                        logger.debug("thumbnail is: "+img)
                        element["thumbnail"] = img
                    except:
                        logger.debug("Could not be extracted any img. :'(")
                    x.append(element)
        else:
            html = ElMundo.getContentFromUrl(url=page,launchLocation=True,referer=ElMundo.MAIN_URL).decode('iso-8859-15').encode('utf8')
            startRegex = '<article class="news-item" itemscope itemtype="http://schema.org/NewsArticle">'
            body = Decoder.extract(startRegex,'<h3 class="list-header">',html)
            if 'class="comentarios ' in body:
                body = body[:body.find('class="comentarios ')]
            if '<a href="#ancla_comentarios">' in body:
                replacedBy = Decoder.extract('<a href="#ancla_comentarios">',"</a>",body)
                logger.debug("removing: "+replacedBy)
                body = body.replace(replacedBy,"")
            logger.debug("removing html: "+body)
            body = Decoder.removeHTML(body)
            logger.debug("html has removed from body!")
            if '|' in body:
                body = body[body.find('|')+1:]
            try:
                lowerCaseIndex = int(re.search("[a-z]", body).start())
                body = body[:lowerCaseIndex-1]+"\n"+body[lowerCaseIndex-1:]
            except:
                logger.error("No break for city was done. Something goes wrong")
                pass
            element = {}
            element["link"] = page
            element["title"] = body
            element["thumbnail"] = ''
            x.append(element)
        return x

