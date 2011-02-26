#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging,lxml,re 

from core import Base,Element,Fetcher,Wtf


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
  aPath='.'
  pidRE='.+pid(\d+).+'
  # the regexp to get an Video Id from a url
  vidRE='.vid=(\d+)'
  def __init__(self,session):
    Fetcher.__init__(self,session)
    return

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

  def parseContent(self,emission):
    ''' Read the data to get the videos VID
    '''
    data=self.fetch(emission)
    self.getVideos(data)
    return
    
  def getVideos(self,data,emission):
    '''
      An Emission's videos are identified bt their VID in the url
    '''
    videos=dict()
    try:
      root=lxml.html.fromstring(data)
      contenu=root.xpath('id("contenuOnglet")')[0]
      vidz=contenu.xpath('.//h4')
      for videoLink in vidz:
        title=videoLink.xpath('string()').strip()
        vid=re.findall(self.vidRE,videoLink.xpath('./a')[0].get('href'))[0]
        videos[vid]=Video(vid,emission.getId(),title)
    except Exception,e:
      log.error("%s %s"%(e, emission) )
      self.writeToFile(data,emission)
      raise EmissionNotFetchable(emission)
    return videos

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

  def __init__(self,pid=None,cid=None,url=None,text=None):
    self.pid=pid
    self.cid=cid
    self.url=url
    self.text=text
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

  #
  def __repr__(self):
    return '<Emission %s pid="%s">'%(repr(self.text),self.pid)  




