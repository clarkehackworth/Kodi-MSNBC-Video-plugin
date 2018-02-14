import urllib,urllib2,re,xbmcplugin,xbmcgui,simplejson as json
from bs4 import BeautifulSoup
from random import randint
import logging
logging.basicConfig(level=logging.DEBUG)
import datetime

__plugin__ = "MSNBC Videos"
__author__ = 'Clarke Hackworth <clarke.hackworth@gmail.com>'
__url__ = ''
__date__ = ''
__version__ = '0.1.9'
UTF8 = 'utf-8'

autoPlay = True


def getURL(url):
    	req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        resp=response.read()
	response.close()
	return resp

def populateShows():
  shows = [] 
  showsData = json.loads(getURL("http://www.msnbc.com/api/1.0/shows.json"))
  
  for show in showsData['shows']:
    #print(json.dumps(show['show'], sort_keys=True, indent=4 * ' '))
    title = 'Unknown'
    logoPathURL = ''
    backgroundURL = ''
    if show['show'] and show['show']['slug']:
      if show['show']['title']:
        title = show['show']['title'];
      if show['show']['assets']:
        if show['show']['assets']['logo_small'] and show['show']['assets']['logo_small']['path']:
          logoPathURL = show['show']['assets']['logo_small']['path'];
        elif show['show']['assets']['headshot_large'] and show['show']['assets']['headshot_large']['path']:
          logoPathURL = show['show']['assets']['headshot_large']['path'];
        if show['show']['assets']['background_image'] and show['show']['assets']['background_image']['path']:
          backgroundURL = show['show']['assets']['background_image']['path'];
        shows.append({ 
              	'title':  title,
                'backgroundImageURL': backgroundURL,
                'logoPathURL': logoPathURL,
                'slug': show['show']['slug']
                })
  return shows

def showsArrayKey(item):
    return item['title'].lower()

def addShows():
  shows = populateShows()
  shows = sorted(shows, key=showsArrayKey)
  for show in shows:	
    addDir(show['title'],show['slug'],1,'',show['logoPathURL'])

def playAll(slug,dataParam):   
  dataObj = json.loads(dataParam)
  playlist = dataObj['playlist']
  pubdate = dataObj['data']
  
  episodes = populateEpisodes(slug,playlist)
  episodes = sorted(episodes, key=episodesArrayKey,reverse=True)
  pl=xbmc.PlayList(1)
  pl.clear()
  for ep in episodes:
    if ep['pubDate'] == pubdate:
      sources = populateSources(slug,json.dumps(ep['sources']))
      sources = sorted(sources, key=sourcesArrayKey,reverse=True)
      #print sources[0]
     
      ##listitem = xbmcgui.ListItem(ep['title'],iconImage=ep['thumbnailURL'])
      url = sources[0]['url']
      icon = "DefaultVideoPlaylists.png"
      liz=xbmcgui.ListItem(ep['title'], iconImage=icon, thumbnailImage=ep['thumbnailURL'])
      liz.setProperty("IsPlayable", "true")
      liz.setInfo( type="Video", infoLabels={ "Title": ep['title'] } )
      liz.setSubtitles([sources[0]['subtitle']])
    
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url,listitem=liz, isFolder=False)
      xbmc.PlayList(1).add(url, liz)

  xbmc.Player().play(pl)
  

def episodesArrayKey(item):
    try:
       outarray = item['pubDate'].split(' ')[0].split('/')
       return outarray[2]+outarray[0]+outarray[1]
    except :
       return '700101'
    
def addEpisodes(slug,dataParam):       
  episodes = populateEpisodes(slug,dataParam)
  episodes = sorted(episodes, key=episodesArrayKey,reverse=True)
  dateList = []
  for ep in episodes:
    if ep['pubDate'] not in dateList:
      addDir("Play "+ep['pubDate'],slug,4,json.dumps({'playlist':dataParam,'data':ep['pubDate']}),'')
      dateList.append(ep['pubDate'])
    #addDir("   "+ep['pubDate']+" - "+ep['title'],ep['title'],2,json.dumps(ep['sources'], sort_keys=False),ep['thumbnailURL']);
    addDir("   "+ep['title']+" ("+ep['duration']+")",ep['title'],3,json.dumps({'playlist':dataParam,'data':json.dumps(ep['sources'], sort_keys=False)}),ep['thumbnailURL']);
                       
       
                       
def populateEpisodes(slug,dataParam):
  print "pop eps: "+slug+" - "+str(dataParam)
  episodeListArray = []
  googleEpisodeList = []
  #if slug == "Latest Videos":
  #  googleEpisodeList = populateGoogleEpisodes(slug,1)
  
  
  videorawdata = getURL("http://www.msnbc.com/api/1.0/getplaylistcarousel/vertical/"+dataParam+".json")
  videojsondata = json.loads(videorawdata)
   
  if videojsondata['carousel']:
    #print videojsondata['carousel'][0]['item']
    playlistdata = BeautifulSoup(videojsondata['carousel'][0]['item'], 'html.parser')
    articles = playlistdata.findAll("article")
    
    for article in articles:
      #print article
      #print "-------------------------------"
      if article.find("div", attrs = {'class' : 'title'}).get_text() is not None:
        
        description = article.find("div", attrs = {'class' : 'description'}).get_text().encode('ascii', 'ignore')
        title = article.find("div", attrs = {'class' : 'title'}).get_text()
        thumbnail = article.find('img')['src']
        pubdate = article.find("div", attrs = {'class' : 'datetime'}).get_text()
        sources = [{'type':1,'source':article.find(lambda tag: tag.name == 'div' and 'data-address' in tag.attrs)['data-address']}]
        guid = article.find(lambda tag: tag.name == 'a' and 'data-ng-attr-guid' in tag.attrs)['data-ng-attr-guid']
        duration = article.find("div", attrs = {'class' : 'duration'})
        if duration is not None:
          duration = duration.get_text().replace("Duration: ","")
        else:
          duration = ""

        #print "found article "+description +" - "+title+" - "+thumbnail+" - "+pubdate+" - "+str(sources)+" - "+guid

        episode = {'description': description,
         'thumbnailURL': thumbnail,
         'pubDate': pubdate,
         'sources': sources,
         'title': title ,
         'guid' : guid,
         'duration': duration,
			   #'rawdate': 
                  };
        for gepisode in googleEpisodeList:
          if episode['guid'] == gepisode['guid']:
            googleEpisodeList.remove(gepisode)
            episode['thumbnailURL'] = gepisode['thumbnailURL']
            #episode['sources'].append({'type':2,'source':gepisode['source']})
            #print "added source "+gepisode['source']+" on "+episode['guid'] 
        episodeListArray.append(episode)	
        
  else:
    raise Exception('pub_news_show first_playlist_html not found')
    
  for gepisode in googleEpisodeList:
    gepisode['sources'] = [{'type':2,'source':gepisode['source']}]
    episodeListArray.append(gepisode)
    #print "added episode "+gepisode['guid']
  return episodeListArray;

def populateGoogleEpisodes(slug,page):
  episodeListArray = []
  if page is None:
    page=1
  url = "http://www.msnbc.com/msnbc_googlevideos.xml?page="+str(page)
  data = getURL(url)
  showssoup = BeautifulSoup(data, "html.parser")
  urlList = showssoup.findAll("url")
  for urlItem in urlList:
    if urlItem.find("loc").get_text().startswith("http://www.msnbc.com/"+slug):
      #print "google found "+urlItem.find("video:publication_date").get_text().split('T')[0]+" "+urlItem.find("loc").get_text() 
      source = urlItem.find("video:player_loc").get_text().replace("player","feed").replace("/p/","/f/").replace("MSNBCEmbeddedOffSite","msnbc_video-p-test").replace("guid","byGuid")+"&form=json"
      datearr = urlItem.find("video:publication_date").get_text().split('T')[0].split("-")
      guid = urlItem.find("video:player_loc").get_text().split("=")[1]
      episodeListArray.append({
                    'description': urlItem.find("video:description").get_text(),
					'thumbnailURL': urlItem.find("video:thumbnail_loc").get_text(),
					'pubDate': datearr[1]+"/"+datearr[2]+"/"+str(int(datearr[0])-2000),
					'source':source,
					'title': urlItem.find("video:title").get_text(),
					'guid': guid,
					#'rawdate': 
				})	
        
  return episodeListArray;

def addPlaylists(slug,dataParam):       
  playlists = populatePlaylists(slug,dataParam)
  
  for pl in playlists:
    addDir(pl['name'],pl['name'],2,pl['guid'],"DefaultFolder.png");
                       

def populatePlaylists(slug,dataParam):    
  print "pop playlists: "+slug+" - "+str(dataParam)   
  playlists = []
  
  url = "http://www.msnbc.com/"+slug
  data = getURL(url)
  data = re.sub(r"document\.write(.*);", "", data)
  
  showssoup = BeautifulSoup(data, 'html.parser')
  scripts = showssoup.findAll("script")
  jsontext = ""
  for script in scripts:
    text = script.get_text().strip()
    if text.startswith("jQuery.extend(Drupal.settings,"):
      jsontext = text.replace("jQuery.extend(Drupal.settings,","").replace(");","")
  pageData = json.loads(jsontext)
  
  
  if pageData['pub_news_show'] and pageData['pub_news_show']['playlists']:
    for plist in pageData['pub_news_show']['playlists']:
      playlists.append({'name':plist['name'],'guid':plist['guid']})
  return playlists

def sourcesArrayKey(item):
    return int(item['res'])
    
def addSources(slug,dataParam):
  print "addSources sources: "+slug+" - "+str(dataParam)
  dataObj = json.loads(dataParam)
  playlist = dataObj['playlist']
  data = dataObj['data']
  
  sources = populateSources(slug,data)
  sources = sorted(sources, key=sourcesArrayKey,reverse=True)
  for src in sources:	
    sourceTitle = src['title']
    li = xbmcgui.ListItem(sourceTitle, iconImage='DefaultVideo.png')
    li.setInfo( type="Video", infoLabels={ "Title": src['slug'] })
    li.setSubtitles([src['subtitle']])
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=src['url'], listitem=li)
  
def populateSources(slug,dataParam):
  logging.debug("pop sources: "+slug+" - ")
  sourceListArray = []
  sources = json.loads(dataParam)  
  
  
  sources = json.loads(dataParam)  
  for source in sources:
    sourceURL = source['source']
    if source['type'] == 1:
      data = getURL(sourceURL)
      data = re.sub(r"document\.write(.*);", "", data)
  
      showssoup = BeautifulSoup(data, "html.parser")
      scripts = showssoup.findAll("script")
      jsontext = ""
      for script in scripts:
        text = script.get_text().strip()
        if text.startswith("window.__data="):
          jsontext = text.replace("window.__data=","").replace("};","}")
      if jsontext == '':
        print data
        raise Exception('someone moved the drupal settings json')
      pageData = json.loads(jsontext)
      sourceURL = ''

      if pageData['video']:
        if pageData['video']['current']['videoAssets']:
          pageUrl = pageData['video']['current']['videoAssets'][0]['publicUrl']
          titleBase = pageData['video']['current']['headline']['primary']
          #logging.debug(title+' '+pageUrl)
          data = getURL(pageUrl)
          #logging.debug(data)
          
          videoSoup = BeautifulSoup(data, 'html.parser')
          videos = videoSoup.findAll("video")
          subTags = videoSoup.findAll("textstream")[0]['src']
          logging.debug(subTags)

          logging.debug("subs: " + subTags)
          for video in videos:
            height = "0"
            src=''
            if video.has_attr('height'):
              height = video['height']
              title = titleBase + ' ' + str(height)
            if video.has_attr('src'):
              src=video['src']
              logging.debug(src)
              sourceListArray.append({
                'slug': slug,
                'title': title,
                'url' : src,
                'res': height,
                'subtitle': subTags
                })
      else:
        raise Exception('cant find video location data')
  return sourceListArray
       
def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param



def addLink(name,url,mode,data,iconimage):
	#logging.debug("addLink url:"+url+" ,name:"+name+" ,mode:"+str(mode))
	addItem(name,url,mode,data,iconimage,"DefaultVideo.png")

def addDir(name,url,mode,data,iconimage):
	#logging.debug("addDir: url"+url+" ,name:"+name+" ,mode:"+str(mode))
	addItem(name,url,mode,data,iconimage,"DefaultFolder.png")

def addItem(name,url,mode,data,iconimage,texticon):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url.encode(UTF8))+"&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode(UTF8))+"&data="+urllib.quote_plus(data)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=texticon, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
        
              
params=get_params()
url=None
name=None
mode=None
data=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass

try:
        mode=int(params["mode"])
except:
        pass
try:
        data=urllib.unquote_plus(params["data"])
except:
        pass

logging.debug("Mode: "+str(mode))
logging.debug("URL: "+str(url))
logging.debug("Data: "+str(data))
logging.debug("Name: "+str(name))

if mode==None or url==None or len(url)<1:
        addShows()
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
        

elif mode==1:
  #logging.debug("url:"+url+",mode:"+str(mode))
  addPlaylists(url,data)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==2:
  #logging.debug("url:"+url+",mode:"+str(mode))
  addEpisodes(url,data)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


elif mode==3:
  #logging.debug("url:"+url+",mode:"+str(mode))
  if data is not None:
    #logging.debug("data:"+data)
    addSources(url,data)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==4:
  #logging.debug("url:"+url+",mode:"+str(mode))
  playAll(url,data)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
