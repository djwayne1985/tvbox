import CommonFunctions as common
from core import logger
from core.addonUtils import add_dir
from core.downloader import Downloader
from core.xbmcutils import XBMCUtils

def getListsUrls(url,name,page):
    icon = XBMCUtils.getAddonFilePath('icon.png')
    #logger.debug("using url: "+url)
    html = Downloader.getContentFromUrl(url)
    if url.endswith(".xml") or ('<items>' in html or '<item>' in html): #main channels, it's a list to browse
        drawXml(html,icon)
    elif url.endswith(".xspf"):
        drawXspf(html,icon)
    else: #it's the final list channel, split
        drawBruteChannels(html,icon)

def drawBruteChannels(html,icon=''):
	bruteChannels = html.split("#EXTINF")
	for item in bruteChannels:
		item = item[item.find(",") + 1:]
		name = item[:item.find("\n")]
		value = item[item.find("\n") + 1:]
		value = value[:value.find("\n")]
		# print "detected channel: "+name+" with url: "+value
		if name != "" and value != "":  ##check for empty channels, we don't want it in our list
			add_dir(name, value, 2, icon, '', name)
		else:
			logger.debug("Discarted brute: " + name + ", " + value)

def drawXml(html,icon=''):
	logger.debug(html)
	lists = common.parseDOM(html, "stream")
	if len(lists) > 0:
		logger.info("counted: " + str(len(lists)))
		for item in lists:
			name = common.parseDOM(item, "title")[0].encode("utf-8").strip().replace("<![CDATA[", "").replace("]]>", "")
			value = common.parseDOM(item, "link")[0].encode("utf-8").strip().replace("<![CDATA[", "").replace("]]>", "")
			if len(value) > 0:
				logger.info("Added: " + name + ", url: " + value)
				add_dir(name, value, 2, icon, '', 0)
			else:
				logger.debug("Discarted: " + name + ", " + value)
	else:
		lists = common.parseDOM(html, "list")
		if len(lists) > 0:
			logger.info("counted: " + str(len(lists)))
			for item in lists:
				name = common.parseDOM(item, "name")[0].encode("utf-8")
				value = common.parseDOM(item, "url")[0].encode("utf-8")
				logger.info("Added: " + name + ", url: " + value)
				add_dir(name, value, 1, icon, '', 0)
		else:
			lists = common.parseDOM(html, "item")  # sportsdevil private lists
			if len(lists) > 0:
				logger.info("counted (item): " + str(len(lists)))
				for item in lists:
					target = 1
					try:
						name = common.parseDOM(item, "title")[0].encode("utf-8")
						if '<title>' in name:
							name = name[0:name.find('<title>')]
					except:
						pass
					try:
						value = common.parseDOM(item, "sportsdevil")[0].encode("utf-8")
						target = 2
					except:
						value = common.parseDOM(item, "link")[0].encode("utf-8")
						if 'ignorame' in value:
							value = common.parseDOM(item, "externallink")[0].encode("utf-8")
						pass

					#final links capture
					if "rtmp" in value or 'rtsp' in value or value.endswith(".m3u8") or value.endswith(".ts") or 'plugin://plugin.video' in value:
						target = 2

					referer = ""
					try:
						referer = common.parseDOM(item, "referer")[0].encode("utf-8")
					except:
						logger.info("referer not found!")
					img = icon
					try:
						img = common.parseDOM(item, "thumbnail")[0].encode("utf-8")
					except:
						logger.info("thumbnail not found!")
					if name != "" and value != "":
						if referer != "":
							value += ", referer: " + referer
						logger.info("Added: " + name + ", url: " + value)
						add_dir(name, value, target, img, '', 0)
					else:
						logger.debug("Discarted: "+name+", "+value)
			else:  # tries xspf
				drawXspf(html,icon)

def drawXspf(html,icon=''):
	lists = common.parseDOM(html,"track") #rusian acelive format
	if len(lists)>0:
		for item in lists:
			name = common.parseDOM(item,"title")[0].encode("utf-8")
			value = common.parseDOM(item,"location")[0].encode("utf-8")
			logger.info("Added: "+name+", url: "+value)
			add_dir(name, value, 2, icon,'', 0)