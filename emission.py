#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging,re

import lxml 

#from lxml import etree
#from lxml.etree import tostring
#from operator import itemgetter, attrgetter

from core import Database,Element,Fetcher
from video import Video

log=logging.getLogger('emission')

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
  def __init__(self,hrefEl):
    Element.__init__(self,hrefEl)
    if self.text is None:
      self.text = self.url
    if self.text is None:
      self.text=''
    self.getPid()
    return
    
  def writeToFile(self,dirname='./'):
    '''
    save content to file <dirname>/<self.id>
    '''
    fout=file(os.path.sep.join([dirname,'%s'%self.id]),'w')
    fout.write(self.data)
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
  #
  def __repr__(self):
    return '<Emission %s pid="%s">'%(self.text.encode('utf8'),self.pid)  


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
  # the regexp to get an Video Id from a url
  vidRE='.vid=(\d+)'
  def __init__(self):
    Fetcher.__init__(self)

  def getUrl(self,emission):
    '''
      Some logic around an emission's url.
    '''
    url=emission.url
    if url is None or len(url) == 0:
      raise EmissionNotFetchable(emission)
    return url

  def fromFile(self,filename):
    '''
      Loads a Emission Html page content from file on disk.
    '''
    self.data=file(filename).read()
    return self.makeAll()

  def fetch(self,emission):
    '''
      Loads a Emission Html page content from network.
    '''
    url=self.getUrl(emission)
    # make the request
    log.debug('requesting %s'%(url))
    Fetcher.request(self,url)
    self.data=self.handleResponse()
    if(self.data is None):
      raise EmissionNotFetchable(emission)
    return self.makeAll()
    
  def makeAll(self):
    '''
      Build a list of Videos from the emissions page.
    '''
    try:
      videos=self.makeVideoIds()
    except IndexError,e:
      raise EmissionNotFetchable('')
    return videos
    
  def makeVideoIds(self):
    '''
      An Emission's videos are identified bt their VID in the url
    '''
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



class EmissionDatabase(Database):
  table='emission'
  def __init__(self):
    Database.__init__(self,table)
  def update(self,emission):
    pass
  # getter , setter





