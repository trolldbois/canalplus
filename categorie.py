#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging

from core import Database,Element,Fetcher


log=logging.getLogger('categorie')



class Categorie(Element):
  emissions=None
  #catPath='/html/body/div[2]/div[9]/div[3]/div/h3'
  aPath='./a[1]'
  cid=None
  tid=None
  def __init__(self,el,emissions=None):
    Element.__init__(self,el)
    self.emissions=dict()
    if emissions is not None and len(emissions) >0:
      self.addEmissions(emissions)
    return
  def addEmissions(self,emms):
    adds=[em for em in emms if em.text not in self.emissions]
    for emm in adds:
      self.emissions[emm.text]=emm
      emm.setCategorie(self)
    return
  def setTheme(self,theme):
    self.tid=theme.tid
    return
  def getId(self):
    if self.cid is None:
      db=CategorieDatabase()
      c=db.selectByName(self.text)
      ret=c.fetchone()
      if ret is None:
        # no ref, add it to db.
        db.insertMany([self])
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
  def __repr__(self):
    return '<Categorie %s>'%(repr(self.text))  
  

class CategorieDatabase(Database):
  table='categorie'
  # use ROWID
  schema="(desc VARCHAR(1000) UNIQUE,tid INT)"
  __SELECT_ALL="SELECT rowid as cid, desc, tid from %s "
  __SELECT_ID="SELECT rowid as cid, desc, tid from %s WHERE rowid=?"
  __SELECT_TID="SELECT rowid as cid, desc, tid from %s WHERE tid=?"
  __SELECT_TEXT="SELECT rowid as cid, desc, tid from %s WHERE desc LIKE ?"
  __INSERT_ALL="INSERT IGNORE INTO %s (desc,tid) VALUES (?,?)"
  def __init__(self):
    Database.__init__(self,self.table)
    self.checkOrCreateTable()
    return
            
  def selectByTid(self,elId):
    cursor=self.conn.cursor()
    cursor.execute(self.__SELECT_TID%(self.table),(elId,))
    return cursor

  def insertmany(self, categories):
    args=[(cat.text,cat.tid,) for cat in categories]
    Database.insertmany(args)
    return

  def updatemany(self, categories):
    args=[(cat.text,cat.tid,) for cat in categories]
    Database.updatemany(args)
    return
    
  def __getitem__(self,key):
    try:
      cid=int(key)
      c=self.selectByID(cid)
      ret=c.fetchone()
      if ret is None:
        return None
      cat=CategoryPOPO(ret)
      cat.cid,cat.text,cat.tid=ret
      return cat
    except ValueError,e:
      pass
    # not an int, let's try by name
    try:
      c=self.selectByName(key)
      ret=c.fetchone()
      if ret is None:
        return None
      cat=CategoryPOPO(ret)
      cat.cid,cat.text,cat.tid=ret
      return cat
    except ValueError,e:
      pass
    return None

  def values(self):
    cursor=self.conn.cursor()
    cursor.execute(self.__SELECT_ALL%(self.table))
    values=[CategoriePOPO(cid,text,tid) for cid,text,tid in cursor.fetchall()]
    log.debug('%d themes loaded'%(len(values)) )
    return values

class CategoriePOPO(Categorie):
  def __init__(self,cid=None,text=None,tid=None):
    self.cid=cid
    self.text=text
    self.tid=tid
    self.emissions=dict()

class CategorieBuilder:
  def loadForTheme(self,theme):
    db=CategorieDatabase()
    c=db.selectByTid(theme.getId())
    cats=c.fetchall()
    return cats
  def loadDb(self):
    cdb=CategorieDatabase()
    cats=cdb.values()
    for cat in cats:
      eb=EmissionBuilder()
      cat.addEmissions(eb.loadForCategorie(cat))
    return cats


