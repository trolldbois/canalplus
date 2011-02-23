#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging,lxml,re 

from core import Base,Database,Element,Fetcher,Wtf,parseElement


from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship

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
    url=emission.getUrl()
    # make the request
    log.debug('requesting %s'%(url))
    Fetcher.request(self,url)
    data=self.handleResponse()
    if(data is None):
      raise EmissionNotFetchable(emission)
    return data


class Emission(Base):
  '''
    An emission is described on a dynamice page.
    It is accessible by URL link self.url
    It an be saved to file.
    It's content is accessible by memory access to self.text
  '''
  __tablename__="emissions"

  pid=Column(Integer,primary_key=True)
  cid=Column(Integer, ForeignKey('categories.rowid'))
  text=Column('desc',String(1000))
  url=Column(String(1000))
  ts=Column(DateTime)
  videos=relationship("Video",backref='emission')

  __table_args__= (UniqueConstraint(url, 'url'), UniqueConstraint(text, 'desc') ,{}) 

  log=log
  aPath='.'
  pidRE='.+pid(\d+).+'
  # the regexp to get an Video Id from a url
  vidRE='.vid=(\d+)'

  def addVideos(self,vids):
    adds=[vid for vid in vids if vid.getId() not in self.videos]
    for vid in adds:
      self.videos[vid.vid]=vid
      vid.setEmission(self)
    return
    
  def getId(self):
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
    self.videos=dict()
    try:
      root=lxml.html.fromstring(self.data)
      contenu=root.xpath('id("contenuOnglet")')[0]
      vidz=contenu.xpath('.//h4')
      for videoLink in vidz:
        title=videoLink.xpath('string()').strip()
        vid=re.findall(self.vidRE,videoLink.xpath('./a')[0].get('href'))[0]
        self.videos[vid]=Video(vid,self.getId(),title)
    except Exception,e:
      log.error("%s %s"%(e, self) )
      self.writeToFile()
      raise EmissionNotFetchable(self)
    return self.videos

  def updateTs(self):
    db=EmissionDatabase()
    db.updateTs(self)
    return
  #
  def __repr__(self):
    return '<Emission %s pid="%s">'%(repr(self.text),self.pid)  




