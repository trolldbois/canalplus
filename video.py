#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging
from core import Database,Element,Fetcher,Wtf
from stream import Stream,StreamBuilder,StreamDatabase
import lxml.etree

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


class Video(Element):
  '''
    Une video est determinee par une url REST self.srcUrl + self.vid
  '''
  log=log
  srcUrl='http://service.canal-plus.com/video/rest/getVideosLiees/cplus/%d'
  #programme ID
  pid=None
  vid=None
  bd=None
  hi=None
  hd=None
  # Xpath values
  videosPath='/VIDEOS/VIDEO'
  streamPath='./MEDIA/VIDEOS/*'
  idPath='./ID'
  infoTitrePath='./INFOS/TITRAGE/TITRE'
  infoSousTitrePath='./INFOS/TITRAGE/SOUS_TITRE'
  # ./TITRE + ./SOUS_TITRE
  def __init__(self,vid,pid,text):
    self.pid=int(pid)
    self.vid=int(vid)
    self.text=text
    self.url=self.srcUrl%(self.vid)
    self.parsed=False
    self.streams=dict()
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
  def save(self,update=False):
    db=VideoDatabase()
    # conditional saving
    if update or self.getId() not in db:
      log.debug('saving %s'%(self))
      db[self.getId()]=self
      return 1
    return 0

  #
  def __repr__(self):
    return "<Video %d-%d: %s>"%(self.pid, self.vid,repr(self.text))





    

class VideoDatabase(Database):
  table="videos"
  schema="(vid INT, pid INT, desc VARCHAR(1000))"
  _SELECT_ALL="SELECT vid, pid, desc FROM %s "
  _SELECT_ID="SELECT vid, pid, desc FROM %s WHERE vid=?"
  _SELECT_PARENT_ID="SELECT vid, pid, desc FROM %s WHERE pid=?"
  _INSERT_ALL="INSERT INTO %s (vid, pid, desc) VALUES (?,?,?)"
  _UPDATE_ALL="UPDATE %s SET pid=?,desc=? WHERE vid=?"
  def __init__(self):
    Database.__init__(self,self.table)
    self.checkOrCreateTable()
    return

  def __getitem__(self,key):
    try:
      pid=int(key)
      c=self.selectByID(pid)
      ret=c.fetchone()
      if ret is None:
        raise KeyError()
      vid,pid,text=ret
      v=Video(vid,pid,text)
      return v
    except ValueError,e:
      pass
    # not an int, let's try by name
    try:
      c=self.selectByName(key)
      ret=c.fetchone()
      if ret is None:
        raise KeyError()
      vid,pid,text=ret
      v=Video(vid,pid,text)
      return v
    except ValueError,e:
      pass
    raise KeyError()
            
  def insertmany(self, videos):
    args=[(video.getId(),video.pid,video.text) for video in videos]
    Database.insertmany(self,args)
    return
        
  def updatemany(self, videos):
    args=[(video.pid,video.text, video.getId(),) for video in videos]
    Database.updatemany(self,args)
    return

  def values(self):
    cursor=self.conn.cursor()
    cursor.execute(self._SELECT_ALL%(self.table))
    values=[Video(vid,pid,text) for vid,pid,text in cursor.fetchall()]
    log.debug('%d videos loaded'%(len(values)) )
    return values

class VideoBuilder:
  def loadForEmission(self,em):
    db=VideoDatabase()
    c=db.selectByParent(em.getId())
    rows=c.fetchall()
    vids=[Video(vid,pid,text) for (vid,pid,text) in rows]
    # go down the tree
    sb=StreamBuilder()
    for vid in vids:
      vid.addStreams(sb.loadForVideo(vid))
    return vids
  def loadDb(self):
    db=VideoDatabase()
    vids=db.values()
    # go down the tree
    sb=StreamBuilder()
    for vid in vids:
      vid.addStreams(sb.loadForVideo(vid))
    return vids
  # load Videos with Streams
  def loadVideosWithStreams(self):
    log.error('*** YOU DATABASE TRASH BASTARD ***')
    db=StreamDatabase()
    streams=db.values()
    keys=set(db.getUniqueParentId())
    # go UP the tree
    vdb=VideoDatabase()
    videos=dict()
    # let's be nice
    for key in keys:
      try:
        videos[key]=vdb[key]
      except KeyError,e:
        pass
    sbuilder=StreamBuilder()
    for video in videos.values():
      video.addStreams(sbuilder.loadForVideo(video))
    return videos


