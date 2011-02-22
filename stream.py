#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging,os,urlparse
from core import Database,Element,Fetcher,Wtf

import lxml.etree

log=logging.getLogger('stream')


class Stream:
  def __init__(self,vid,quality,url):
    self.vid=vid
    self.quality=quality
    self.url=urlparse.urlparse(url).geturl()
    if self.url is None:
      raise Wtf()
  #
  def fetchStream(self):
    ''' on recupere le stream avec un outils externe ( rtmpdump )
    '''
    #rtmpdump
    self.makeFilename()
    log.debug("rtmpdump -r %s -o %s"%(self.url,self.filename))
    os.system("rtmpdump -r %s -o %s"%(self.url,self.filename))
    return self.filename
  def makeFilename(self):
    self.filename=os.path.sep.join(['./output',os.path.basename(self.url)])
    return self.filename
  def save(self,update=False):
    db=StreamDatabase()
    # conditional saving
    if self.vid not in db: # 1
      # no stream for this video
      log.debug('saving %s'%self)
      db.insertmany([self])
      return 1
    for s in db[self.vid]:
      if s.quality.lower() == self.quality.lower():
        if update:
          log.debug('updating %s'%self)
          db.updatemany([self])
          return 1
        return 0
    #else, nth stream for video
    log.debug('saving %s'%self)
    db.insertmany([self])
    return 1
    
  
  def __repr__(self):
    low=min(len(self.url),20)
    up=max(0,len(self.url)-20)    
    return "<Stream %s %s[..]%s >"%(self.quality,self.url[:low],self.url[up:])


class StreamDatabase(Database):
  table="streams"
  schema="(vid INT, quality VARCHAR(50), url VARCHAR(1000) UNIQUE)"
  _SELECT_ALL="SELECT vid, quality, url FROM %s "
  _SELECT_PARENT_ID="SELECT vid, quality, url FROM %s WHERE vid=?"
  _SELECT_UNIQUE_PARENT_ID="SELECT DISTINCT vid FROM %s"
  _INSERT_ALL="INSERT INTO %s (vid, quality, url) VALUES (?,?,?)"
  _UPDATE_ALL="UPDATE %s SET url=? WHERE vid=? AND quality=?"
  def __init__(self):
    Database.__init__(self,self.table)
    self.checkOrCreateTable()
    return

  def __getitem__(self,key):
    try:
      vid=int(key)
    except ValueError,e:
      raise KeyError()
    c=self.selectByParent(vid)
    ret=c.fetchall()
    if len(ret) ==0 :
      raise KeyError()
    streams=[Stream(vid,quality,url) for (vid,quality,url) in ret]
    return streams
            
  def insertmany(self, streams):
    args=[(s.vid,s.quality,s.url) for s in streams]
    Database.insertmany(self,args)
    return
        
  def updatemany(self, videos):
    args=[(s.url,s.vid,s.quality) for s in streams]
    Database.updatemany(self,args)
    return

  def values(self):
    cursor=self.conn.cursor()
    cursor.execute(self._SELECT_ALL%(self.table))
    values=[Stream(vid,quality,url) for vid,quality,url in cursor.fetchall()]
    log.debug('%d streams loaded'%(len(values)) )
    return values

  def getUniqueParentId(self):
    cursor=self.conn.cursor()
    cursor.execute(self._SELECT_UNIQUE_PARENT_ID%(self.table))
    values=[vid for vid, in cursor.fetchall()]
    return values

class StreamBuilder:
  def loadForVideo(self,vid):
    db=StreamDatabase()
    try:
      streams=db[vid.getId()]
      return streams
    except KeyError,e:
      return []
  def loadDb(self):
    db=VideoDatabase()
    streams=db.values()
    return streams

