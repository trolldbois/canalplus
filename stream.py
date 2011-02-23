#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging,os,urlparse
from core import Base,Database,Element,Fetcher,Wtf

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint

import lxml.etree

log=logging.getLogger('stream')


class Stream(Base):
  __tablename__="streams"

  id=Column(Integer,primary_key=True)
  vid=Column(Integer,ForeignKey('videos.vid'))
  quality=Column(String(50))
  #url=Column(String(1000), UniqueConstraint('urlu'))
  url=Column(String(1000))

  __table_args__  = (UniqueConstraint(url, 'url'), {}) 

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


