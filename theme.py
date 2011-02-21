#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging, re
import lxml.html

from core import Database,Element,Fetcher
from categorie import Categorie,CategorieBuilder
from emission import Emission

log=logging.getLogger('theme')



class MainFetcher(Fetcher):
  ROOTURL='/'
  def __init__(self):
    Fetcher.__init__(self)
    return
  
  def fetch(self):
    # make the request
    log.debug('requesting %s'%(self.ROOTURL))
    Fetcher.request(self,self.ROOTURL)
    data=self.handleResponse()
    return data    


class Theme(Element):
  '''
    Emission are grouped into categories, which are part off one of the 6 main Themes.
  '''
  categories=None
  aPath='./h2[1]/a[1]'
  tidRE='.+pid(\d+).+'
  data=None
  root=None
  text=None
  tid=None
  #
  def __init__(self,el,categories=None):
    Element.__init__(self,el)
    self.categories=dict()
    if categories is not None and len(categories) >0:
      self.addCategories(categories)
    return
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
    else:
      # find it in DB ?
      db=ThemeDatabase()
      value=db[self.text]
      if value is None:
        self.tid=None
      else:
        self.tid=value.tid
    return self.tid
    
  def save(self):
    db=ThemeDatabase()
    self.getId()
    if self.tid is None:
      raise Wtf()
    db[self.tid]=self
    return
  #
  def __repr__(self):
    return '<Theme %d: %s>'%(self.getId(), repr(self.text))  

class Main:
  '''
    Emission are grouped into categories, which are part off one of the 6 main Themes.
  '''
  categories=None
  aPath='./h2[1]/a[1]'
  data=None
  themes=None
  root=None
  #
  def parseContent(self,fetcher=MainFetcher()):
    self.data=fetcher.fetch(self)
    self.makeAll()
    return
  #
  def makeAll(self):
    self.makeThemes()
    for t in self.themes.values():
      log.debug('BEFORE %s has %d categories'%(t,len(t.categories)))
      cats=self.makeCategories(t)
      log.debug('AFTER %s has %d categories'%(t,len(t.categories)))
      for cat in cats:
        emms=self.makeEmissions(cat)
        log.debug(' %s has %d emission'%(cat,len(emms)))
    return self.data

  def makeThemes(self):
    if self.themes !=None:
      return self.themes
    # else
    self.root=lxml.html.fromstring(self.data)
    #themes = '/html/body/div[2]/div[9]/div[3-7]/h2'
    themesId='/html/body/div[2]/div[9]/div[position()>2 and position()<8]'
    themes=[Theme(theme) for theme in self.root.xpath(themesId)]
    self.themes=dict()
    for t in themes:
      self.themes[t.text]=t
    return self.themes

  def makeCategories(self,theme):
    catPath='./div/h3'
    categories=[Categorie(cat) for cat in theme.element.xpath(catPath)]
    theme.addCategories(categories)
    return categories

  def makeEmissions(self,category):
    emPath='..//a'
    emissions=[Emission(em) for em in category.element.xpath(emPath)]
    category.addEmissions(emissions)
    return emissions

class ThemeDatabase(Database):
  '''
    Database access layer for Theme.
  '''
  table="themes"
  schema="(tid INT UNIQUE, url VARCHAR(1000) UNIQUE, desc VARCHAR(1000) UNIQUE)"
  __SELECT_ALL="SELECT tid, url, desc from %s"
  __SELECT_ID="SELECT tid, url, desc from %s WHERE tid=?"
  __SELECT_DESC="SELECT tid, url, desc from %s WHERE desc LIKE ?"
  __INSERT_ALL="INSERT INTO %s (tid, url, desc) VALUES (?,?,?)"
  __UPDATE_ALL="UPDATE %s SET url=?, desc=? WHERE tid = ?"
  def __init__(self):
    Database.__init__(self,self.table)
    self.checkOrCreateTable()
    return
            
  def __getitem__(self,key):
    try:
      tid=int(key)
      c=self.selectByID(tid)
      ret=c.fetchone()
      if ret is None:
        return None
      theme=ThemePOPO()
      theme.tid,theme.url,theme.text=ret
      return theme
    except ValueError,e:
      pass
    # not an int, let's try by name
    try:
      c=self.selectByName(key)
      ret=c.fetchone()
      if ret is None:
        return None
      theme=ThemePOPO()
      theme.tid,theme.url,theme.text=ret
      return theme
    except ValueError,e:
      pass
    return None

  def values(self):
    cursor=self.conn.cursor()
    cursor.execute(self.__SELECT_ALL%(self.table))
    values=[ThemePOPO(tid,url,text) for tid,url,text in cursor.fetchall()]
    log.debug('%d themes loaded'%(len(values)) )
    return values
    

  def insertmany(self, themes):
    args=[(theme.tid,theme.url,theme.text,) for theme in themes]
    Database.insertmany(args)
    return
    
  def updatemany(self,themes):
    args=[(theme.url,theme.text,theme.tid,) for theme in themes]
    Database.updatemany(args)
    return


class ThemePOPO(Theme):
  def __init__(self,tid=None,url=None,text=None):
    self.tid=tid
    self.url=url
    self.text=text
    self.categories=dict()

class ThemeBuilder:
  def loadDb(self):
    tdb=ThemeDatabase()
    themes=tdb.values()
    for theme in themes:
      cb=CategorieBuilder()
      theme.addCategories(cb.loadForTheme(theme))
      
    return themes


