#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging,os,urlparse,re
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#local exception
from exception import Wtf

log=logging.getLogger('model')
Base = declarative_base()


class Theme(Base):
  '''
    Theme is the top-most classification.
    Themes - > Categories -> Emissions
  '''
  __tablename__="themes"
  
  tid=Column(Integer,primary_key=True)
  url=Column(String(1000))
  text=Column('desc',String(1000))
  categories = relationship("Categorie", backref="theme")

  __table_args__= (UniqueConstraint(url, 'url'), UniqueConstraint(text, 'desc') ,{}) 

  def __init__(self,tid=None,url=None,text=None):
    self.tid=tid
    self.url=url
    self.text=text
    return
  def __repr__(self):
    return '<Theme %s: %s>'%(self.tid, repr(self.text))  


class Categorie(Base):
  '''
    Categorie regroups several emissions.
    Themes - > Categories -> Emissions
  '''
  __tablename__="categories"
  
  cid=Column('rowid',Integer, primary_key=True)
  tid=Column(Integer, ForeignKey('themes.tid'))
  text=Column('desc',String(1000),primary_key=True)
  emissions=relationship("Emission",backref='categorie')
  
  __table_args__= (UniqueConstraint(text, 'desc') ,{}) 
  def __init__(self,cid=None,text=None,tid=None):
    self.cid=cid
    self.text=text
    self.tid=tid
    return
  def __repr__(self):
    return '<Categorie %s-%s: %s>'%(self.tid,self.cid,repr(self.text))  
  

class Emission(Base):
  '''
    An emission is described on the main page.
    An more complete description of it's video contents is accessible by URL link self.url
  '''
  __tablename__="emissions"

  pid=Column(Integer,primary_key=True)
  cid=Column(Integer, ForeignKey('categories.rowid'))
  text=Column('desc',String(1000))
  url=Column(String(1000))
  ts=Column(DateTime)
  videos=relationship("Video",backref='emission')

  __table_args__= (UniqueConstraint(url, 'url'), UniqueConstraint(text, 'desc') ,{}) 

  def __init__(self,pid=None,cid=None,url=None,text=None):
    self.pid=pid
    self.cid=cid
    self.url=url
    self.text=text
    return
  def __repr__(self):
    return '<Emission %s pid="%s">'%(repr(self.text),self.pid)  


class Video(Base):
  '''
    Videos are referenced on a Emission page.
    Several Videos can be found, with quick time expiration ( by day)
    Each video has a more complete XML description which can be found at self.url= self.srcUrl + self.vid
    This XML data often references all Videos & streams on the Emission page.
  '''
  __tablename__="videos"
  vid=Column(Integer,primary_key=True)
  pid=Column(Integer,ForeignKey('emissions.pid'))
  text=Column("desc",String(1000))
  url=Column(String(1000))
  streams=relationship("Stream",backref='video')

  __table_args__= (UniqueConstraint(url, 'url'), UniqueConstraint(text, 'desc') ,{}) 

  parsed=False
  srcUrl='http://service.canal-plus.com/video/rest/getVideosLiees/cplus/%d'

  def __init__(self,vid,pid,text):
    self.pid=int(pid)
    self.vid=int(vid)
    self.text=text
    self.url=self.srcUrl%(self.vid)
    self.parsed=False
    return

  def update(self,title,subtitle):
    self.title=title
    self.subtitle=subtitle
    self.text='%s - %s'%(self.title,self.subtitle)
    self.parsed=True
    log.debug('Updated %s'%self)    
    return

  def bestStream(self):
    if len(self.streams) == 0:
      return None
    else:
      for qual in ['HD','HAUT_DEBIT','BAS_DEBIT']:
        if qual in self.streams:
          return self.streams[qual]
      return self.streams[0]

  def __repr__(self):
    return "<Video %d-%d: %s>"%(self.pid, self.vid,repr(self.text))


class Stream(Base):
  '''
    Streams are the link to video content.
    Several links with different qulity can be found for one video.
  '''

  __tablename__="streams"
  vid=Column(Integer,ForeignKey('videos.vid'),primary_key=True)
  quality=Column(String(50),primary_key=True)
  url=Column(String(1000))

  __table_args__  = (UniqueConstraint(url, 'url'), {}) 

  def __init__(self,vid,quality,url):
    self.vid=vid
    self.quality=quality
    self.url=urlparse.urlparse(url).geturl()
    if self.url is None:
      raise Wtf()
    return  
  
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
 
  def __repr__(self):
    low=min(len(self.url),20)
    up=max(0,len(self.url)-20)    
    return "<Stream %s %s[..]%s >"%(self.quality,self.url[:low],self.url[up:])


