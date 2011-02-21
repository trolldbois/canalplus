#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging
from core import Database,Element,Fetcher

import lxml.etree

log=logging.getLogger('video')


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
  def __init__(self,name,pid,vid):
    self.name=name
    self.pid=int(pid)
    self.vid=int(vid)
    self.url=self.srcUrl%(self.vid)
    return
  #
  def update(self,title,subtitle,bd,hi,hd):
    self.title=title
    self.subtitle=subtitle
    self.name='%s - %s'%(self.title,self.subtitle)
    self.bd=bd
    self.hi=hi
    self.hd=hd
    return
    
  def getLink(self):
    ret=self.hd
    if ret is None or len(ret)==0:
      ret = self.hi
    if ret is None or len(ret)==0:
      ret = self.bd
    if ret is None or len(ret)==0:
      ret = 'file://about:bad_links/'
    return ret
  #
  def fetchStream(self):
    '''
      on recupere le stream avec un outils externe ( rtmpdump )
    '''
    url=self.hd
    log.debug(self.mplayer %(url))
    return
  #
  def __repr__(self):
    if self.hd is not None:
      return "<Video %d: %s %s>"%(self.vid,self.name, self.getLink())
    else:
      return "<Video %d: %s>"%(self.vid,self.url)

class VideoFetcher(Fetcher):
  '''
    Agent de recuperation de l'url REST contenant les infos pour cette videos ( ou plusieurs)
  '''
  cache=None
  videosPath='/VIDEOS/VIDEO'
  idPath='./ID'
  infoTitrePath='./INFOS/TITRAGE/TITRE'
  infoSousTitrePath='./INFOS/TITRAGE/SOUS_TITRE'
  # ./TITRE + ./SOUS_TITRE
  linkBDPath='./MEDIA/VIDEOS/BAS_DEBIT'
  linkHIPath='./MEDIA/VIDEOS/HAUT_DEBIT'
  linkHDPath='./MEDIA/VIDEOS/HD'
  def __init__(self,emission):
    Fetcher.__init__(self)
    self.cache=dict()
    self.emission=emission
    #check for mplayer
    self.mplayer="mplayer %s"
    pass

  def fromFile(self,filename):
    '''
      On recupere le contenu par lecture d'un fichier sur disque
    '''
    self.data=file(filename).read()
    self.makeAll()

  def fetch(self,video):
    '''
      On recupere le contenu par le reseau
    '''
    # make the request
    log.debug('requesting %s'%(video.url))
    Fetcher.request(self,video.url)
    self.data=self.handleResponse()
    self.makeAll()
    
  def makeAll(self):
    self.parse()
    pass

  def parse(self):
    # on recupere plusieurs videos en realite ...
    root=lxml.etree.fromstring(self.data)
    vidz=root.xpath(self.videosPath)
    pid=self.emission.getPid()
    for desc in vidz:
      mid=int(desc.xpath(self.idPath)[0].text)
      if mid not in self.cache:
        name='%s - %s'%(desc.xpath(self.infoTitrePath)[0].text,desc.xpath(self.infoSousTitrePath)[0].text)
        self.cache[mid]=Video(name,pid,mid)
      # all
      hd=desc.xpath(self.linkHDPath)
      if hd is None or len(hd) <1:
        hd=None
      else:
        hd = hd[0].text
      self.cache[mid].update( desc.xpath(self.infoTitrePath)[0].text,
                desc.xpath(self.infoSousTitrePath)[0].text,
                desc.xpath(self.linkBDPath)[0].text,
                desc.xpath(self.linkHIPath)[0].text,
                hd)
    pass
  #
  def save(self):
    db=VideoDatabase()
    db.insertMany(self.cache.values())
    return
    

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



