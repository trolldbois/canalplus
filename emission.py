#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging,lxml,re 

from core import Database,Element,Fetcher,Wtf
from video import Video,VideoBuilder
import sqlite3 

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
  def __init__(self):
    Fetcher.__init__(self)

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


class Emission(Element):
  '''
    An emission is described on a dynamice page.
    It is accessible by URL link self.url
    It an be saved to file.
    It's content is accessible by memory access to self.text
  '''
  log=log
  aPath='.'
  pidRE='.+pid(\d+).+'
  pid=None
  # the regexp to get an Video Id from a url
  vidRE='.vid=(\d+)'
  #categorie
  cat=None
  def __init__(self,hrefEl):
    Element.__init__(self,hrefEl)
    if self.text is None:
      self.text = self.url
    if self.text is None:
      self.text=''
    self.getId()
    self.videos=dict()
    return

  def setCategorie(self,cat):
    self.cat=cat
    return

  def addVideos(self,vids):
    adds=[vid for vid in vids if vid.getId() not in self.videos]
    for vid in adds:
      self.videos[vid.vid]=vid
      vid.setEmission(self)
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

  def getUrl(self):
    ''' Some logic around an emission's url.  '''
    if self.url is None or len(self.url) == 0:
      self.writeToFile()
      raise EmissionNotFetchable(self)
    return self.url

  def parseContent(self,fetcherEngine=EmissionFetcher()):
    ''' Read the data to get the videos VID
    '''
    fetcher=fetcherEngine
    self.data=fetcher.fetch(self)
    self.getVideos()
    return
    
  def getVideos(self):
    '''
      An Emission's videos are identified bt their VID in the url
    '''
    self.videos=dict()
    try:
      root=lxml.html.fromstring(self.data)
      contenu=root.xpath('id("contenuOnglet")')[0]
      vidz=contenu.xpath('.//h4')
      for videoLink in vidz:
        title=videoLink.xpath('string()').strip()
        vid=re.findall(self.vidRE,videoLink.xpath('./a')[0].get('href'))[0]
        self.videos[vid]=Video(vid,self.getId(),title)
    except Exception,e:
      log.error("%s %s"%(e, self) )
      self.writeToFile()
      raise EmissionNotFetchable(self)
    return self.videos
  #
  def save(self,update=False):
    db=EmissionDatabase()
    self.getId()
    if self.pid is None:
      #raise Wtf(self)
      log.warning("Unparseable PID for %s"%self)
    else:
      try:
        # conditional saving
        if update or self.getId() not in db:
          log.info('Saving new Emission %s'%self)
          db[self.getId()]=self
      except sqlite3.IntegrityError,e:
        log.error('Integrity error on %s'%(self))
        log.error(self.__dict__)
        pass
    return
  def updateTs(self):
    db=EmissionDatabase()
    db.updateTs(self)
    return
  #
  def __repr__(self):
    return '<Emission %s pid="%s">'%(repr(self.text),self.pid)  



class EmissionDatabase(Database):
  table='emissions'
  schema="(pid INT UNIQUE, cid INT, url VARCHAR(1000) UNIQUE, desc VARCHAR(1000) UNIQUE, ts DATETIME)"
  _SELECT_ALL="SELECT pid, cid, url, desc from %s ORDER by ts asc"
  _SELECT_ID="SELECT pid, cid, url, desc from %s WHERE pid=?"
  _SELECT_DESC="SELECT pid, cid, url, desc from %s WHERE desc LIKE ?"
  _SELECT_PARENT_ID="SELECT pid, cid, url, desc from %s WHERE cid=?"
  _INSERT_ALL="INSERT INTO %s (pid, cid, url, desc, ts) VALUES (?,?,?,?,DATETIME('now'))"
  _UPDATE_ALL="UPDATE %s SET cid=?,url=?,desc=?,ts=DATETIME('now') WHERE pid=?"
  _UPDATE_TS="UPDATE %s SET ts=DATETIME('now') WHERE pid=?"
  def __init__(self):
    Database.__init__(self,self.table)
    self.checkOrCreateTable()
    return
            
  def updateTs(self, emission):
    args=(emission.getId(),)
    self.conn.execute('BEGIN TRANSACTION')
    try:
      log.debug( "%s - %s " % (self._UPDATE_TS%self.table,args) )   
      self.conn.execute(self._UPDATE_TS%self.table,args)
      self.conn.commit()
    except Exception, e:
      self.conn.rollback()
      log.error('%s -> %s'%(self._UPDATE_TS%self.table,args))
      raise e
    return

  def insertmany(self, emissions):
    args=[(em.pid,em.cat.getId(),em.url,em.text,) for em in emissions]
    Database.insertmany(self,args)
    return

  def updatemany(self, emissions):
    args=[(em.cat.getId(),em.url,em.text,em.getId(),) for em in emissions]
    Database.updatemany(self,args)
    return

  def __getitem__(self,key):
    try:
      pid=int(key)
      c=self.selectByID(pid)
      ret=c.fetchone()
      if ret is None:
        raise KeyError()
      em=EmissionPOPO(ret)
      em.pid,em.cid,em.url,em.text=ret
      return em
    except ValueError,e:
      pass
    # not an int, let's try by name
    try:
      c=self.selectByName(key)
      ret=c.fetchone()
      if ret is None:
        raise KeyError()
      em=EmissionPOPO(ret)
      em.pid,em.cid,em.url,em.text=ret
      return em
    except ValueError,e:
      pass
    raise KeyError()

  def values(self):
    cursor=self.conn.cursor()
    cursor.execute(self._SELECT_ALL%(self.table))
    values=[EmissionPOPO(pid,cid,url,text) for pid,cid,url,text in cursor.fetchall()]
    log.debug('%d emissions loaded'%(len(values)) )
    return values

class EmissionPOPO(Emission):
  def __init__(self,pid=None,cid=None,url=None,text=None):
    self.pid=pid
    self.cid=cid
    self.url=url
    self.text=text
    self.videos=dict()

class EmissionBuilder:
  def loadForCategorie(self,cat):
    db=EmissionDatabase()
    c=db.selectByParent(cat.getId())
    rows=c.fetchall()
    ems=[EmissionPOPO(pid,cid,url,text) for (pid,cid,url,text) in rows]
    # go down the tree
    vb=VideoBuilder()
    for em in ems:
      em.addVideos(vb.loadForEmission(em))
    return ems
  def loadDb(self):
    edb=EmissionDatabase()
    ems=edb.values()
    # go down the tree
    vb=VideoBuilder()
    for em in ems:
      em.addVideos(vb.loadForEmission(em))
    return ems



