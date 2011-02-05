#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+taleo@gmail.com
#



import httplib, logging, urllib,time
import lxml,lxml.html,re,os
from lxml import etree
from lxml.etree import tostring
from operator import itemgetter, attrgetter

log=logging.getLogger('fetcher')

SERVER='www.canalplus.fr'
PORT=80
METHOD='GET'


def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

class Wtf(Exception):
  pass

class Fetcher():
  headers={'Accept-Language': 'fr,en-us;q=0.7,en;q=0.3', 
          'Accept-Encoding': 'gzip,deflate', 
          'Connection': 'keep-alive', 
          'Keep-Alive': '115', 
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
          'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13', 
          'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7', 
      }
  params=dict()
  def __init__(self,method=METHOD,server=SERVER,port=PORT):
    # open connection
    self.METHOD=method
    self.SERVER=server
    self.PORT=port
    self.conn = httplib.HTTPConnection(self.SERVER, self.PORT)
  
  def getParams(self):
    return self.params

  def getHeaders(self):
    return self.headers

  def printParams(self,params,sep='='):
    for k,v in params.items():
      log.debug('%s%s%s'%(k,sep,v))

  def uncompress(self,cdata):
    import StringIO, gzip
    compressedstream = StringIO.StringIO(cdata) 
    gzipper = gzip.GzipFile(fileobj=compressedstream)
    data = gzipper.read() 
    return data

  def request(self,url):
    params=self.getParams()
    headers=self.getHeaders()
    # make the request
    self.conn.request(self.METHOD,url,params,headers)
    log.info('requested : %s'%(url))
    return self.conn

  def handleResponse(self):
    resp=self.conn.getresponse()
    respC=resp.getheader('connection')
    if respC == 'close':
      log.debug('BAD: connection is closed.')
      log.debug(resp.reason)
      log.debug(resp.getheaders())
      return None
    else:
      data=resp.read()
      if resp.getheader('content-encoding') == 'gzip':
        data=self.uncompress(data)
      return data


class MainFetcher(Fetcher):
  ROOTURL='/'
  data=None
  themes=None
  root=None
  def __init__(self):
    Fetcher.__init__(self)

  def fromFile(self,filename):
    self.data=file(filename).read()
    self.makeAll()

  def fetch(self):
    # make the request
    log.debug('requesting %s'%(self.ROOTURL))
    Fetcher.request(self,self.ROOTURL)
    self.data=self.handleResponse()
    self.makeAll()
    
  def makeAll(self):
    self.makeThemes()
    for t in self.themes.values():
      log.debug('BEFORE %s has %d categories'%(t,len(t.categories)))
      cats=self.makeCategories(t)
      log.debug('AFTER %s has %d categories'%(t,len(t.categories)))
      for cat in cats:
        emms=self.makeEmissions(cat)
        log.debug(' %s has %d emission'%(cat,len(emms)))
      #
    #
    return self.data

  def makeThemes(self):
    if self.themes !=None:
      return self.themes
    # else
    self.root=lxml.html.fromstring(self.data)
    #themes = '/html/body/div[2]/div[9]/div[3-7]/h2'
    themesId='/html/body/div[2]/div[9]/div[position()>2 and position()<8]'
    themes=[Theme(theme) for theme in self.root.xpath(themesId)]
    self.themes=dict()
    for t in themes:
      self.themes[t.text]=t
    return self.themes

  def makeCategories(self,theme):
    #
    catPath='./div/h3'
    categories=[Category(cat) for cat in theme.element.xpath(catPath)]
    theme.addCategories(categories)
    return categories

  def makeEmissions(self,category):
    #
    emPath='..//a'
    emissions=[Emission(em) for em in category.element.xpath(emPath)]
    category.addEmissions(emissions)
    return emissions


class Element():
  element=None
  a=None
  text=None
  url=None
  def __init__(self,el):
    self.element=el
    log.debug('Creating a %s'%self.__class__.__name__)
    res=self.element.xpath(self.aPath)
    if len(res) != 1:
      log.debug('DOM error, falling back to xpath string(), no url ')
      print ''
    if len(res)==0:
      self.text=self.element.xpath('string()')
    else:
      self.a=res[0]
      log.debug('A %s'%(tostring(self.a)))
      self.text=self.a.text
      log.debug('TEXT %s '%(self.text))
      self.url=self.a.get('href')
      log.debug('url %s '%(self.url))

class Theme(Element):
  categories=None
  aPath='./h2[1]/a[1]'
  def __init__(self,el,categories=None):
    Element.__init__(self,el)
    self.categories=dict()
    if categories is not None and len(categories) >0:
      self.addCategories(categories)
  #
  def addCategories(self,cats):
    adds=[cat for cat in cats if cat.text not in self.categories]
    for cat in adds:
      self.categories[cat.text]=cat
  #
  def __repr__(self):
    return '<Theme %s>'%(self.text.encode('utf8'))  

class Category(Element):
  emissions=None
  #catPath='/html/body/div[2]/div[9]/div[3]/div/h3'
  aPath='./a[1]'
  def __init__(self,el,emissions=None):
    Element.__init__(self,el)
    self.emissions=dict()
    if emissions is not None and len(emissions) >0:
      self.addEmissions(emissions)
  def addEmissions(self,emms):
    adds=[em for em in emms if em.text not in self.emissions]
    for emm in adds:
      self.emissions[emm.text]=emm
  #
  def __repr__(self):
    return '<Category %s>'%(self.text.encode('utf8'))  
  


class Emission(Element):
  aPath='.'
  pidRE='.+pid(\d+).+'
  pid=None
  def __init__(self,hrefEl):
    Element.__init__(self,hrefEl)
    if self.text is None:
      self.text = self.url
    if self.text is None:
      self.text=''
    self.getPid()
    
  def writeToFile(self,dirname='./'):
    fout=file(os.path.sep.join([dirname,self.prefix+'%s'%self.id]),'w')
    fout.write(self.data)

  def getPid(self):
    if self.pid != None:
      return self.pid
    if self.url is None :
      return None
    pids=re.findall(self.pidRE,self.url)
    if len(pids) !=1:
      log.warning('Erreur while parsing PID')
      return None
    self.pid=int(pids[0])
    return self.pid
  #
  def __repr__(self):
    return '<Emission %s pid="%s">'%(self.text.encode('utf8'),self.pid)  


class EmissionNotFetchable(Exception):
  def __init__(self,emission):
    self.emission=emission
  def __str__(self):
    return repr(self,value)
  
class EmissionFetcher(Fetcher):
  vidRE='.vid=(\d+)'
  def __init__(self):
    Fetcher.__init__(self)

  def getUrl(self,emission):
    url=emission.url
    if url is None or len(url) == 0:
      raise EmissionNotFetchable(emission)
    return url

  def fromFile(self,filename):
    self.data=file(filename).read()
    return self.makeAll()

  def fetch(self,emission):
    url=self.getUrl(emission)
    # make the request
    log.debug('requesting %s'%(url))
    Fetcher.request(self,url)
    self.data=self.handleResponse()
    return self.makeAll()
    
  def makeAll(self):
    videos=self.makeVideoIds()
    return videos
    
  def makeVideoIds(self):
    root=lxml.html.fromstring(self.data)
    contenu=root.xpath('id("contenuOnglet")')[0]
    vidz=contenu.xpath('.//h4')
    videos=[]
    for videoLink in vidz:
      title=videoLink.xpath('string()').strip()
      vid=re.findall(self.vidRE,videoLink.xpath('./a')[0].get('href'))[0]
      myvid=Video(title,vid)
      videos.append(myvid)
    return videos

class Video():
  srcUrl='http://service.canal-plus.com/video/rest/getVideosLiees/cplus/%d'
  bd=None
  hi=None
  hd=None
  def __init__(self,name,vid):
    self.name=name
    self.vid=int(vid)
    self.url=self.srcUrl%(self.vid)
  #
  def update(self,title,subtitle,bd,hi,hd):
    self.title=title
    self.subtitle=subtitle
    self.name='%s - %s'%(self.title,self.subtitle)
    self.bd=bd
    self.hi=hi
    self.hd=hd
  #
  def fetchStream(self):
    url=self.hd
    log.debug(self.mplayer %(url))
  #
  def __repr__(self):
    if self.hd is not None:
      return "<Video %d: %s %s>"%(self.vid,self.name, self.hd)
    else:
      return "<Video %d: %s>"%(self.vid,self.url)

class VideoFetcher(Fetcher):
  cache=None
  videosPath='/VIDEOS/VIDEO'
  idPath='./ID'
  infoTitrePath='./INFOS/TITRAGE/TITRE'
  infoSousTitrePath='./INFOS/TITRAGE/SOUS_TITRE'
  # ./TITRE + ./SOUS_TITRE
  linkBDPath='./MEDIA/VIDEOS/BAS_DEBIT'
  linkHIPath='./MEDIA/VIDEOS/HAUT_DEBIT'
  linkHDPath='./MEDIA/VIDEOS/HD'
  def __init__(self):
    Fetcher.__init__(self)
    self.cache=dict()
    #check for mplayer
    self.mplayer="mplayer %s"
    pass

  def fromFile(self,filename):
    self.data=file(filename).read()
    self.makeAll()

  def fetch(self,video):
    # make the request
    log.debug('requesting %s'%(video.url))
    Fetcher.request(self,video.url)
    self.data=self.handleResponse()
    self.makeAll()
    
  def makeAll(self):
    self.parse()
    pass

  def parse(self):
    # on recupere plusieurs vieos en realite ...
    root=lxml.etree.fromstring(self.data)
    vidz=root.xpath(self.videosPath)
    for desc in vidz:
      mid=int(desc.xpath(self.idPath)[0].text)
      if mid not in self.cache:
        name='%s - %s'%(desc.xpath(self.infoTitrePath)[0].text,desc.xpath(self.infoSousTitrePath)[0].text)
        self.cache[mid]=Video(name,mid)
      # all      
      self.cache[mid].update( desc.xpath(self.infoTitrePath)[0].text,
                desc.xpath(self.infoSousTitrePath)[0].text,
                desc.xpath(self.linkBDPath)[0].text,
                desc.xpath(self.linkHIPath)[0].text,
                desc.xpath(self.linkHDPath)[0].text)
    pass
    
def dumpAll():
  logging.basicConfig(level=logging.DEBUG)
  main=MainFetcher()
  ef=EmissionFetcher()
  vf=VideoFetcher()
  # my cache is in VideoFetcher
  # dump all here
  fout=file('urls','w')
  oldcache=vf.cache.copy()
  # run....
  data=main.fetch()
  # unravel all
  for t in main.themes.values():
    print t
    for c in t.categories.values():
      print '\t',c
      for e in c.emissions.values():
        print '\t\t',e
        # fetch each Emission page   
        videos=ef.fetch(e)
        # we've got a bunch of video Ids...
        # normally, we shoud it the XML Desc only once by emission 
        # because it contains multiple videos desc
        for vid in videos:
          print '\t\t\t',vid
          # but we are lazy, so we hammer canalplus server.
          vf.fetch(vid)
          # we write new infos in file....
          newcache=set(vf.cache) - set(oldcache)
          newitems=[vf.cache[item] for item in newcache] 
          for v in newitems:
            fout.write( ('%s ; %s\n'%(v.hd,v.name)).encode('utf8'))
          fout.flush()
          oldcache=vf.cache.copy()
  # tafn
  fout.close()

def test():
  #e=main.themes.values()[1].categories.values()[2].emissions.values()[2]
  #print e
  #print e.url

  ef=EmissionFetcher()
  #videos=ef.fetch(e)
  videos=ef.fromFile('guignols.html')
  print videos


  vf=VideoFetcher()
  vf.fromFile('419796')

  for vfk,vf in vf.cache.items():
    print vfk,vf

    

  logging.basicConfig(level=logging.DEBUG)
  main=MainFetcher()
  #data=main.run()

  #data=main.fromFile('index.html')

  if False:
    for t in main.themes.values():
      print t
      for c in t.categories.values():
        print '\t',c
        for e in c.emissions.values():
          print '\t\t',e

  #e=main.themes.values()[1].categories.values()[2].emissions.values()[2]
  #print e
  #print e.url

  ef=EmissionFetcher()
  #videos=ef.fetch(e)
  videos=ef.fromFile('guignols.html')
  print videos


  vf=VideoFetcher()
  vf.fromFile('419796')

  for vfk,vf in vf.cache.items():
    print vfk,vf



#
dumpAll()


