#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging,os,urlparse,re


from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship

log=logging.getLogger('model')

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()




class Wtf(Exception):
  def __init__(self,obj=None):
    self.obj=obj
  def __str__(self):
    if self.obj is not None:
      return '%s'%(self.obj.__dict__)
    return '' 





class Theme(Base):
  '''
    Emission are grouped into categories, which are part off one of the 6 main Themes.
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
  
  log=log
  data=None
  root=None

  #
  def __repr__(self):
    return '<Theme %s: %s>'%(self.tid, repr(self.text))  


class Categorie(Base):
  __tablename__="categories"
  
  cid=Column('rowid',Integer, primary_key=True)
  tid=Column(Integer, ForeignKey('themes.tid'))
  text=Column('desc',String(1000),primary_key=True)
  emissions=relationship("Emission",backref='categorie')
  
  __table_args__= (UniqueConstraint(text, 'desc') ,{}) 

  log=log
  #catPath='/html/body/div[2]/div[9]/div[3]/div/h3'
  aPath='./a[1]'

  def __init__(self,cid=None,text=None,tid=None):
    self.cid=cid
    self.text=text
    self.tid=tid
    return

  #
  def __repr__(self):
    return '<Categorie %s-%s: %s>'%(self.tid,self.cid,repr(self.text))  
  

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
    
  #
  def __repr__(self):
    return '<Emission %s pid="%s">'%(repr(self.text),self.pid)  


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


class Stream(Base):
  __tablename__="streams"

  #id=Column(Integer,primary_key=True)
  vid=Column(Integer,ForeignKey('videos.vid'),primary_key=True)
  quality=Column(String(50),primary_key=True)
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
    
  
  def __repr__(self):
    low=min(len(self.url),20)
    up=max(0,len(self.url)-20)    
    return "<Stream %s %s[..]%s >"%(self.quality,self.url[:low],self.url[up:])


