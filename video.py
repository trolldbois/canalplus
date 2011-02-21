#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging
from core import Database,Element,Fetcher
from stream import Stream
import lxml.etree

log=logging.getLogger('video')


def clean(tree,el):
  value=tree.xpath(el)
  if value is None or len(value) <1:
    value=None
  else:
    value = value[0].text
  return value



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
    log.debug('requesting %s'%(video.url))
    Fetcher.request(self,video.url)
    data=self.handleResponse()
    return data


class Video():
  '''
    Une video est determinee par une url REST self.srcUrl + self.vid
  '''
  srcUrl='http://service.canal-plus.com/video/rest/getVideosLiees/cplus/%d'
  #programme ID
  pid=None
  vid=None
  bd=None
  hi=None
  hd=None
  # Xpath values
  videosPath='/VIDEOS/VIDEO'
  idPath='./ID'
  infoTitrePath='./INFOS/TITRAGE/TITRE'
  infoSousTitrePath='./INFOS/TITRAGE/SOUS_TITRE'
  # ./TITRE + ./SOUS_TITRE
  linkBDPath='./MEDIA/VIDEOS/BAS_DEBIT'
  linkHIPath='./MEDIA/VIDEOS/HAUT_DEBIT'
  linkHDPath='./MEDIA/VIDEOS/HD'
  def __init__(self,name,pid,vid):
    self.name=name
    self.pid=int(pid)
    self.vid=int(vid)
    self.url=self.srcUrl%(self.vid)
    self.parsed=False
    return
  #
  def update(self,title,subtitle,bd,hi,hd):
    self.title=title
    self.subtitle=subtitle
    self.name='%s - %s'%(self.title,self.subtitle)
    self.bd=Stream(bd)
    self.hi=Stream(hi)
    self.hd=Stream(hd)
    self.parsed=True
    return
  #
  def isParsed(self):
    return self.parsed
  
  def getStreams(self):
    streams=[s for s in [self.hd,self.hi,self.bd] if (s.stream is not None ) or (len(s.stream)!=0 )]
    return streams
  #  
  def bestStream(self):
    streams=self.getStreams()
    if len(streams) == 0:
      return None
    else:
      return streams[0]
  #
  def parseContent(self,fetcher=VideoFetcher(),videoCache=dict()):
    ''' 
    We return a dictionnary of several Videos referenced in the XML file
    '''
    self.data=fetcher.fetch(self)
    videos=self.parseXml(videoCache)
    return videos
    
  def parseXml(self,videoCache):
    videos=videoCache
    # on recupere plusieurs videos en realite ...
    root=lxml.etree.fromstring(self.data)
    elements=root.xpath(self.videosPath)
    # we parse each child to get a new Video with the 3 Streams
    for desc in elements:
      vid=int(desc.xpath(self.idPath)[0].text)
      # if video is already known, continue
      if (vid in videos ) and (videos[vid].isParsed()) :
        continue
      elif vid not in videos:
        # Create Video
        name='%s - %s'%(clean(desc,self.infoTitrePath), clean(desc,self.infoSousTitrePath))
        videos[vid]=Video(name,self.pid,vid)
      # else, parse it and update it
      # update each video with new infos
      videos[vid].update( clean(desc,self.infoTitrePath), clean(desc,self.infoSousTitrePath), 
          clean(desc,self.linkBDPath), clean(desc,self.linkHIPath), clean(desc,self.linkHDPath))
    return videos
  #
  def save(self):
    db=VideoDatabase()
    db.insertMany(self.cache.values())
    return

  #
  def __repr__(self):
    return "<Video %d-%d: %s>"%(self.pid, self.vid,self.name)





    

class VideoDatabase(Database):
  table="videos"
  schema="(vid INT, pid INT, url VARCHAR(1000), desc VARCHAR(1000))"
  __SELECT_VID="SELECT vid, pid, url, desc from ? WHERE vid=?"
  __SELECT_PID="SELECT vid, pid, url, desc from ? WHERE pid=?"
  __INSERT_ALL="INSERT IGNORE INTO ? (vid, pid, url, desc) VALUES (?,?,?,?)"
  def __init__(self):
    Database.__init__(self,self.table)
    self.checkOrCreateTable()
    return
            
  def select(self,elId):
    cursor=self.conn.cursor()
    cursor.execute(__SELECT_VID,(self.table,elId,))
    return cursor

  def insertMany(self, videos):
    ''' elList = [ <Video>,..]
    '''
    l=[(self.table,video.vid,video.pid,video.bd,video.hi,video.hd,video.subtitle) for video in videos]
    self.conn.execute('BEGIN TRANSACTION')
    try:
      self.conn.executemany(__INSERT_ALL,l)
      self.conn.commit()
    except Exception, e:
      self.conn.rollback()
      raise e
    return
    
  def update(self,el):
    raise NotImplementedError()



