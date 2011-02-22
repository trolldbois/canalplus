#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging

from core import Database,Element,Fetcher
from emission import EmissionBuilder

log=logging.getLogger('categorie')



class Categorie(Element):
  log=log
  emissions=None
  #catPath='/html/body/div[2]/div[9]/div[3]/div/h3'
  aPath='./a[1]'
  cid=None
  tid=None
  def __init__(self,el,tid,emissions=None):
    Element.__init__(self,el)
    self.emissions=dict()
    self.tid=tid
    if emissions is not None and len(emissions) >0:
      self.addEmissions(emissions)
    return
  def addEmissions(self,emms):
    adds=[em for em in emms if em.text not in self.emissions]
    for emm in adds:
      self.emissions[emm.text]=emm
      emm.setCategorie(self)
    return

  def getId(self):
    if self.cid is None:
      db=CategorieDatabase()
      c=db.selectByName(self.text)
      ret=c.fetchone()
      if ret is None:
        # no ref, add it to db.
        db.insertmany([self])
        c=db.selectByName(self.text)
        ret=c.fetchone()
        if ret is None:
          raise IOError('Database is not saving %s'%(self))
      # with ret
      self.cid,desc,tid=ret
      c.close()
    #else
    return self.cid
  #
  def save(self,update=False):
    db=CategorieDatabase()
    self.getId()
    if self.cid is None:
      raise Wtf()
    # conditional saving
    if update or self.getId() not in db:
      log.info('Saving new Categorie %s'%self)
      db[self.getId()]=self
    return
  #
  def __repr__(self):
    return '<Categorie %s-%d: %s>'%(self.tid,self.getId(),repr(self.text))  
  

class CategorieDatabase(Database):
  table='categories'
  # use ROWID
  schema="(desc VARCHAR(1000) UNIQUE,tid INT)"
  _SELECT_ALL="SELECT rowid as cid, desc, tid from %s "
  _SELECT_ID="SELECT rowid as cid, desc, tid from %s WHERE rowid=?"
  _SELECT_PARENT_ID="SELECT rowid as cid, desc, tid from %s WHERE tid=?"
  _SELECT_DESC="SELECT rowid as cid, desc, tid from %s WHERE desc LIKE ?"
  _INSERT_ALL="INSERT INTO %s (desc,tid) VALUES (?,?)"
  _UPDATE_ALL="UPDATE %s SET desc=?,tid=? where rowid=?"
  def __init__(self):
    Database.__init__(self,self.table)
    self.checkOrCreateTable()
    return
  
  def insertmany(self, categories):
    args=[(cat.text,cat.tid,) for cat in categories]
    Database.insertmany(self,args)
    return

  def updatemany(self, categories):
    args=[(cat.text,cat.tid,cat.getId(),) for cat in categories]
    Database.updatemany(self,args)
    return
    
  def __getitem__(self,key):
    try:
      cid=int(key)
      c=self.selectByID(cid)
      ret=c.fetchone()
      if ret is None:
        raise KeyError()
      cat=CategoriePOPO(ret)
      cat.cid,cat.text,cat.tid=ret
      return cat
    except ValueError,e:
      pass
    # not an int, let's try by name
    try:
      c=self.selectByName(key)
      ret=c.fetchone()
      if ret is None:
        raise KeyError()
      cat=CategoriePOPO(ret)
      cat.cid,cat.text,cat.tid=ret
      return cat
    except ValueError,e:
      pass
    raise KeyError()

  def values(self):
    cursor=self.conn.cursor()
    cursor.execute(self._SELECT_ALL%(self.table))
    values=[CategoriePOPO(cid,text,tid) for cid,text,tid in cursor.fetchall()]
    log.debug('%d categories loaded'%(len(values)) )
    return values

class CategoriePOPO(Categorie):
  def __init__(self,cid=None,text=None,tid=None):
    self.cid=cid
    self.text=text
    self.tid=tid
    self.emissions=dict()

class CategorieBuilder:
  cache=None
  def __init__(self):
    self.cache=dict()
  def loadForTheme(self,theme):
    db=CategorieDatabase()
    c=db.selectByParent(theme.getId())
    rows=c.fetchall()
    cats=[CategoriePOPO(cid,text,tid) for (cid,text,tid) in rows]
    # go down the tree
    eb=EmissionBuilder()
    for cat in cats:
      cat.addEmissions(eb.loadForCategorie(cat))
    return cats
  def loadDb(self):
    cdb=CategorieDatabase()
    cats=cdb.values()
    # go down the tree
    eb=EmissionBuilder()
    for cat in cats:
      cat.addEmissions(eb.loadForCategorie(cat))
    return cats


