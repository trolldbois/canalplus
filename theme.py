#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging
import lxml.html

from core import Database,Element,Fetcher
from categorie import Category
from emission import Emission

log=logging.getLogger('theme')



class ThemesFetcher(Fetcher):
  ROOTURL='/'
  data=None
  themes=None
  root=None
  def __init__(self):
    Fetcher.__init__(self)

  def fromFile(self,filename):
    self.data=file(filename).read()
    self.makeAll()

  def fetch(self):
    # make the request
    log.debug('requesting %s'%(self.ROOTURL))
    Fetcher.request(self,self.ROOTURL)
    self.data=self.handleResponse()
    self.makeAll()
    
  def makeAll(self):
    self.makeThemes()
    for t in self.themes.values():
      log.debug('BEFORE %s has %d categories'%(t,len(t.categories)))
      cats=self.makeCategories(t)
      log.debug('AFTER %s has %d categories'%(t,len(t.categories)))
      for cat in cats:
        emms=self.makeEmissions(cat)
        log.debug(' %s has %d emission'%(cat,len(emms)))
      #
    #
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
    #
    catPath='./div/h3'
    categories=[Category(cat) for cat in theme.element.xpath(catPath)]
    theme.addCategories(categories)
    return categories

  def makeEmissions(self,category):
    #
    emPath='..//a'
    emissions=[Emission(em) for em in category.element.xpath(emPath)]
    category.addEmissions(emissions)
    return emissions

class Theme(Element):
  '''
    Emission are grouped into categories, which are part off one of the 6 main Themes.
  '''
  categories=None
  aPath='./h2[1]/a[1]'
  def __init__(self,el,categories=None):
    Element.__init__(self,el)
    self.categories=dict()
    if categories is not None and len(categories) >0:
      self.addCategories(categories)
  #
  def addCategories(self,cats):
    adds=[cat for cat in cats if cat.text not in self.categories]
    for cat in adds:
      self.categories[cat.text]=cat
  #
  def __repr__(self):
    return '<Theme %s>'%(self.text.encode('utf8'))  

class ThemeDatabase(Database):
  '''
    Database access layer for Theme.
  '''
  pass



