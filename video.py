#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging
from core import Base,Database,Element,Fetcher,Wtf,parseElement

import lxml.etree

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship


log=logging.getLogger('video')


def clean(tree,el):
  value=tree.xpath(el)
  if value is None or len(value) <1:
    value=None
  else:
    value = value[0].text
  return value

class VideoNotFetchable(Exception):
  '''    Exception raised when the video is unfetchable,
  '''
  def __init__(self,video):
    self.video=video
  def __str__(self):
    return 'VideoNotFetchable %s'%self.video


class VideoFetcher(Fetcher):
  '''
    Agent de recuperation de l'url REST contenant les infos pour cette videos ( ou plusieurs)
  '''
  def __init__(self):
    Fetcher.__init__(self)
    return

  def fetch(self,video):
    '''  On recupere le contenu par le reseau
    '''
    # make the request
    log.debug('requesting %s'%(video.getUrl()))
    Fetcher.request(self,video.getUrl())
    data=self.handleResponse()
    return data


class Video(Base):
  '''
    Une video est determinee par une url REST self.srcUrl + self.vid
  '''
  __tablename__="videos"
  vid=Column(Integer,primary_key=True)
  pid=Column(Integer,ForeignKey('emissions.pid'))
  text=Column("desc",String(1000))
  url=Column(String(1000))
  #self.srcUrl%(self.vid)
  streams=relationship("Stream",backref='video')

  __table_args__= (UniqueConstraint(url, 'url'), UniqueConstraint(text, 'desc') ,{}) 

  parsed=False
  srcUrl='http://service.canal-plus.com/video/rest/getVideosLiees/cplus/%d'

  # Xpath values
  videosPath='/VIDEOS/VIDEO'
  streamPath='./MEDIA/VIDEOS/*'
  idPath='./ID'
  infoTitrePath='./INFOS/TITRAGE/TITRE'
  infoSousTitrePath='./INFOS/TITRAGE/SOUS_TITRE'

  def getUrl(self):
    return self.url
  #
  def update(self,title,subtitle):
    self.title=title
    self.subtitle=subtitle
    self.text='%s - %s'%(self.title,self.subtitle)
    self.parsed=True
    log.debug('Updated %s'%self)    
    return
  #
  def isParsed(self):
    return self.parsed
  #
  def getId(self):
    ''' gets a video ID    '''
    return self.vid
    
  def setEmission(self,em):
    self.pid=em.getId()
    self.emission=em
    return

  def addStreams(self,streams):
    log.debug('Adding streams for %s'%self)    
    for s in streams:
      self.streams[s.quality]=s
    return
  #  
  def bestStream(self):
    if len(self.streams) == 0:
      return None
    else:
      for qual in ['HD','HAUT_DEBIT','BAS_DEBIT']:
        if qual in self.streams:
          return self.streams[qual]
      return self.streams[0]
  #
  def parseContent(self,videosCache,fetcher=VideoFetcher()):
    ''' 
    We return a dictionnary of several Videos referenced in the XML file
    '''
    if self.getId() not in videosCache:
      log.debug('fetching')
      # first time, we nee to get the XML and parse IT
      self.data=fetcher.fetch(self)
      log.debug('parsing')
      self.parseXml(videosCache)
    else:
      # we are already parsed
      log.debug('saved one HTTP query for %s'%(self) )
      fetcher.stats.SAVEDQUERIES+=1
      pass
    return
    
  def parseXml(self,videosCache):
    videos=[]
    # on recupere plusieurs videos en realite ...
    root=lxml.etree.fromstring(self.data)
    elements=root.xpath(self.videosPath)
    # we parse each child to get a new Video with the 3 Streams
    log.info('parsing Video XML chunk for %d Videos'%( len(elements)) )
    for desc in elements:
      vid=int(desc.xpath(self.idPath)[0].text)
      # check for error, vide videoId == -1
      if vid == -1:
        self.writeToFile()
        ## and save a DEADLINK Stream to keep it out from future round
        v=Video(self.vid,self.pid,'DEADLINK')
        s=Stream(self.vid,'DEADLINK','')
        v.addStreams([s])
        raise VideoNotFetchable(v)
      log.debug('parsing XML chunk for  %s'%(vid) )
      # if video is already known, continue
      if (vid in videosCache ) and (videosCache[vid].isParsed()) :
        continue
      elif vid not in videosCache:
        # Create Video before updating it in cache
        text='%s - %s'%(clean(desc,self.infoTitrePath), clean(desc,self.infoSousTitrePath))
        videosCache[vid]=Video(vid,self.pid,text)
        log.debug('%s added to cache'%(vid) )
        streamsEl=desc.xpath(self.streamPath)
        streams=[Stream(vid,s.tag,s.text) for s in streamsEl if s.text is not None]
        log.debug('%d streams created '%( len(streams)) )
        videosCache[vid].addStreams(streams)
      # Videos is NOT parsed , update each video with new infos
      videosCache[vid].update( clean(desc,self.infoTitrePath), clean(desc,self.infoSousTitrePath))
    return
  #
  def __repr__(self):
    return "<Video %d-%d: %s>"%(self.pid, self.vid,repr(self.text))



