#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging,lxml,re 

from core import Database,Element,Fetcher
from video import Video

log=logging.getLogger('emission')



class EmissionNotFetchable(Exception):
  '''
    Exception raised when the emission name is unknown or unfetchable,
  '''
  def __init__(self,emission):
    self.emission=emission
  def __str__(self):
    return 'EmissionNotFetchable %s'%self.emission
  
class EmissionFetcher(Fetcher):
  '''
  Http fetcher for an emission.
  '''
  def __init__(self):
    Fetcher.__init__(self)

  def fetch(self,emission):
    '''
      Loads a Emission Html page content from network.
    '''
    url=self.getUrl(emission)
    # make the request
    log.debug('requesting %s'%(url))
    Fetcher.request(self,url)
    data=self.handleResponse()
    if(data is None):
      raise EmissionNotFetchable(emission)
    return data


class Emission(Element):
  '''
    An emission is described on a dynamice page.
    It is accessible by URL link self.url
    It an be saved to file.
    It's content is accessible by memory access to self.text
  '''
  aPath='.'
  pidRE='.+pid(\d+).+'
  pid=None
  # the regexp to get an Video Id from a url
  vidRE='.vid=(\d+)'
  def __init__(self,hrefEl):
    Element.__init__(self,hrefEl)
    if self.text is None:
      self.text = self.url
    if self.text is None:
      self.text=''
    self.getPid()
    return
    
  def getPid(self):
    '''
      Get emission's unique identifier.
      Programme Id.
    '''
    if self.pid != None:
      return self.pid
    # if there is not url, we can't parse it to get the PID
    if self.url is None :
      return None
    # PID is in the URL
    pids=re.findall(self.pidRE,self.url)
    if len(pids) !=1:
      log.warning('Erreur while parsing PID')
      return None
    self.pid=int(pids[0])
    return self.pid

  def getUrl(self):
    ''' Some logic around an emission's url.  '''
    if self.url is None or len(self.url) == 0:
      raise EmissionNotFetchable(self)
    return self.url

  def writeToFile(self,dirname='./'):
    '''
    save content to file <dirname>/<self.id>
    '''
    fout=file(os.path.sep.join([dirname,'%s'%self.id]),'w')
    fout.write(self.data)
    return

  def parseContent(self,fetcherEngine=EmissionFetcher()):
    ''' Read the data to get the videos VID
    '''
    fetcher=fetcherEngine
    self.data=fetcher.fetch(self)
    self.getVideos()
    return
    
  def getVideos(self):
    '''
      An Emission's videos are identified bt their VID in the url
    '''
    self.videos=[]
    try:
      root=lxml.html.fromstring(self.data)
      contenu=root.xpath('id("contenuOnglet")')[0]
      vidz=contenu.xpath('.//h4')
      for videoLink in vidz:
        title=videoLink.xpath('string()').strip()
        vid=re.findall(self.vidRE,videoLink.xpath('./a')[0].get('href'))[0]
        myvid=Video(title,self.getPid(),vid)
        self.videos.append(myvid)
    except IndexError,e:
      raise EmissionNotFetchable('')
    return self.videos
  #
  def __repr__(self):
    return '<Emission %s pid="%s">'%(self.text.encode('utf8'),self.pid)  





class EmissionDatabase(Database):
  table='emission'
  def __init__(self):
    Database.__init__(self,table)
  def update(self,emission):
    pass
  # getter , setter





