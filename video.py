#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging
from core import Base,Database,Element,Fetcher,Wtf,parseElement
from stream import Stream

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
  # Xpath values
  videosPath='/VIDEOS/VIDEO'
  streamPath='./MEDIA/VIDEOS/*'
  idPath='./ID'
  infoTitrePath='./INFOS/TITRAGE/TITRE'
  infoSousTitrePath='./INFOS/TITRAGE/SOUS_TITRE'

  def __init__(self,session):
    Fetcher.__init__(self,session)
    return

  def fetch(self,video):
    '''  On recupere le contenu par le reseau
    '''
    # make the request
    log.debug('requesting %s'%(video.getUrl()))
    Fetcher.request(self,video.getUrl())
    data=self.handleResponse()
    return data
  #
  def parseContent(self,video,videosCache):
    ''' 
    We return a dictionnary of several Videos referenced in the XML file
    '''
    if video.getId() not in videosCache:
      log.debug('fetching')
      # first time, we nee to get the XML and parse IT
      data=self.fetch(video)
      log.debug('parsing')
      self.parseXml(data,video,videosCache)
    else:
      # we are already parsed
      log.debug('saved one HTTP query for %s'%(video) )
      fetcher.stats.SAVEDQUERIES+=1
      pass
    return
  #
  def parseXml(self,data,video,videosCache):
    videos=[]
    # on recupere plusieurs videos en realite ...
    root=lxml.etree.fromstring(data)
    elements=root.xpath(self.videosPath)
    # we parse each child to get a new Video with the 3 Streams
    log.info('parsing Video XML chunk for %d Videos'%( len(elements)) )
    for desc in elements:
      vid=int(desc.xpath(self.idPath)[0].text)
      # check for error, vide videoId == -1
      if vid == -1:
        self.writeToFile(data,video)
        ## and save a DEADLINK Stream to keep it out from future round
        video.url='DEADLINK'
        raise VideoNotFetchable(video)
      log.debug('parsing XML chunk for  %s'%(vid) )
      # if video is already known, continue
      if (vid in videosCache ) and (videosCache[vid].isParsed()) :
        continue
      elif vid not in videosCache:
        # Create Video before updating it in cache
        text='%s - %s'%(clean(desc,self.infoTitrePath), clean(desc,self.infoSousTitrePath))
        videosCache[vid]=Video(vid,video.pid,text)
        log.debug('%s added to cache'%(vid) )
        streamsEl=desc.xpath(self.streamPath)
        streams=[self.session.merge(Stream(vid,s.tag,s.text)) for s in streamsEl if s.text is not None]
        self.session.merge(videosCache[vid])
        log.debug('%d streams created '%( len(streams)) )
      # Videos is NOT parsed , update each video with new infos
      videosCache[vid].update( clean(desc,self.infoTitrePath), clean(desc,self.infoSousTitrePath))
    return


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

  def __init__(self,vid,pid,text):
    self.pid=int(pid)
    self.vid=int(vid)
    self.text=text
    self.url=self.srcUrl%(self.vid)
    self.parsed=False
    return

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
  def __repr__(self):
    return "<Video %d-%d: %s>"%(self.pid, self.vid,repr(self.text))



