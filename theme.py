#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging, re
import lxml.html

from core import Base, Database,Element,Fetcher,Wtf,parseElement
from emission import EmissionNotFetchable

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship


log=logging.getLogger('theme')



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
  
  log=log
  aPath='./h2[1]/a[1]'
  tidRE='.+pid(\d+).+'
  data=None
  root=None
  #
  #
  def addCategories(self,cats):
    adds=[cat for cat in cats if cat.text not in self.categories]
    for cat in adds:
      self.categories[cat.text]=cat
    return
    
  def getId(self):
    '''      Get theme's unique identifier.    '''
    if self.tid != None:
      return self.tid
    # if there is url, we can parse it to get the TID
    if self.url is not None :
      # TID is in the URL
      tids=re.findall(self.tidRE,self.url)
      if len(tids) !=1:
        log.warning('Erreur while parsing TID')
        return None
      self.tid=int(tids[0])
    return self.tid
  #
  def __repr__(self):
    return '<Theme %s: %s>'%(self.getId(), repr(self.text))  

