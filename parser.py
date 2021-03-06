#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging, re
import lxml
from lxml.etree import tostring

from model import Theme,Categorie,Emission,Video,Stream



log=logging.getLogger('parser')

def clean(tree,el):
  value=tree.xpath(el)
  if value is None or len(value) <1:
    value=None
  else:
    value = value[0].text
  return value


class Parser:
  '''
    Abstract class to parse A DOM structure into an object
  '''
  def __init__(self,cls,xPath,subPath):
    self.cls=cls
    self.xPath=xPath
    self.subPath=subPath
    self.log=logging.getLogger(self.__class__.__name__)
    return
  
  def findAll(self,root):
    return iter( [ obj for obj in [self.parse(myCls) for myCls in root.xpath(self.xPath)] if obj is not None] )
  
  def parse(self,el):
    if el is None:
      self.log.debug('Element is None')
      return None
    self.log.debug('Parsing a %s'%self.cls)
    text=''
    url=''
    a=''
    res=el.xpath(self.subPath)
    if len(res)==0:
      self.log.debug('DOM error, falling back to xpath string(), no url ')
      self.log.debug('tree element : %s'%(repr(tostring(el))))
      text=el.xpath('string()')
    else:
      a=res[0]
      self.log.debug('A %s'%(repr(tostring(a))))
      text=a.text
      self.log.debug('TEXT %s '%(repr(text) ))
      url=a.get('href')
      self.log.debug('url %s '%(repr(url) ))
    #if text is not None:
    #  #print text
    #  #text=obj.text.decode(obj.encoding)
    try:
      obj=self.makeInstance(a,text,url)
      obj.element=el
    except Exception,e:
      return None
    self.log.debug(obj)
    self.log.debug('')
    return obj
  #
  def writeToFile(self,data,obj,id,dirname='./test'):
    '''
    save content to file <dirname>/<self.id>
    '''
    filename=os.path.sep.join([dirname,'%s-%d'%(obj.__class__.__name__,obj.id) ])
    fout=file(filename,'w')
    fout.write(data)
    log.info('Written to file %s'%(filename))
    return  
  #
  def makeInstance(self,a,text,url):
    raise NotImplementedError()

class ThemeParser(Parser):
  '''
    Builds Theme from Main page root DOM
  '''
  tidRE='.+pid(\d+).+'
  xPath='/html/body/div[2]/div[9]/div[position()>2 and position()<8]'
  subPath='./h2[1]/a[1]'
  def __init__(self):
    cls=Theme
    Parser.__init__(self,cls,self.xPath,self.subPath)
    return
  #
  def getId(self,url):
    '''      Get theme's unique identifier.    '''
    tid=None
    # if there is url, we can parse it to get the TID
    if url is not None :
      # TID is in the URL
      tids=re.findall(self.tidRE,url)
      if len(tids) !=1:
        log.warning('Erreur while parsing TID')
        return None
      tid=int(tids[0])
    else:
      return None
    return tid
  #
  def makeInstance(self,a,text,url):
    obj=self.cls(tid=self.getId(url),url=url,text=text)
    return obj
  
class CategorieParser(Parser):
  '''
    Builds Categorie from Main page theme root DOM
  '''
  xPath='./div/h3'
  subPath='./a'
  def __init__(self,theme):
    cls=Categorie
    self.theme=theme
    Parser.__init__(self,cls,self.xPath,self.subPath)
    return
  #
  def makeInstance(self,a,text,url):
    obj=self.cls(text=text,tid=self.theme.tid)
    return obj

class EmissionParser(Parser):
  '''
    Builds Emission from Main page categorie root DOM
  '''
  xPath='..//a'
  subPath='.'
  pidRE='.+[c,p]id(\d+).+'
  def __init__(self,cat):
    cls=Emission
    self.cat=cat
    Parser.__init__(self,cls,self.xPath,self.subPath)
    return
  #
  def getId(self,url):
    '''      Get emission's unique identifier.
      Programme Id.
    '''
    # if there is not url, we can't parse it to get the PID
    # PID is in the URL
    pids=re.findall(self.pidRE,url)
    if len(pids) !=1:
      log.warning('Erreur while parsing PID for %s'%(url))
      return None
    pid=int(pids[0])
    return pid
  #
  def makeInstance(self,a,text,url):
    pid=self.getId(url)
    if pid is None:
      return None
    obj=self.cls(pid=pid,url=url,text=text,cid=self.cat.text)
    return obj

class VideoParser(Parser):
  '''
    Builds Video from Emission page root DOM
  '''
  xPath='id("contenuOnglet")//h4'
  subPath='./a'
  # the regexp to get an Video Id from a url
  vidRE='.vid=(\d+)'
  def __init__(self,emission):
    self.emission=emission
    cls=Video
    #Parser.__init__(self,cls,self.xPath,self.subPath)
    return

  def parse(self,el):
    ''' An Emission's videos are identified bt their VID in the url
    '''
    text=el.xpath('string()').strip()
    vid=re.findall(self.vidRE,el.xpath(self.subPath)[0].get('href'))[0]
    video=Video(vid=vid,pid=self.emission.pid,text=text)
    return video

class StreamParser(Parser):
  '''
    Builds Stream from Video XML page root DOM
  '''
  # Xpath values
  videosPath='/VIDEOS/VIDEO'
  streamPath='./MEDIA/VIDEOS/*'
  idPath='./ID'
  infoTitrePath='./INFOS/TITRAGE/TITRE'
  infoSousTitrePath='./INFOS/TITRAGE/SOUS_TITRE'
  def __init__(self,emission,cache):
    cls=Stream
    self.emission=emission
    self.cache=cache
    return
  #
  def findAll(self,root):
    ''' 
    We return a dictionary of several Videos referenced in the XML file
    '''
    videos=set()
    streams=set()
    # on recupere plusieurs videos en realite ...
    elements=root.xpath(self.videosPath)
    # we parse each child to get a new Video with the 3 Streams
    log.info('parsing Video XML chunk for %d Videos'%( len(elements)) )
    for desc in elements:
      # videos compares on vid and pid
      vid=int(desc.xpath(self.idPath)[0].text)
      # check for error, vide videoId == -1
      if vid == -1:
        raise VideoNotFetchable()
      #test for presence in cache
      # Create Video before creating it's streams
      text='%s - %s'%(clean(desc,self.infoTitrePath), clean(desc,self.infoSousTitrePath))
      myVideo=Video(vid,self.emission.pid,text)
      if myVideo in self.cache:
        log.info('already parsed in previous XML %s'%(myVideo))
        continue
      log.debug('parsing XML chunk for  %s'%(vid) )
      videos.add(myVideo)
      log.debug('%s added to cache'%(vid) )
      # creating streams
      streamsEl=desc.xpath(self.streamPath)
      streams.update([Stream(vid,s.tag,s.text) for s in streamsEl if s.text is not None])
      log.debug('%d streams created '%( len(streams)) )
    return videos,streams
  #
  def parse(self,el):
    raise NotImplementedError()
    


