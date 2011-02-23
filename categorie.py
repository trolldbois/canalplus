#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging

from core import Base,Database,Element,Fetcher,parseElement

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship


log=logging.getLogger('categorie')



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
  def __repr__(self):
    return '<Categorie %s-%d: %s>'%(self.tid,self.getId(),repr(self.text))  
  

