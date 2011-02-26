#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging, re
import lxml.html

from core import Fetcher
from core import Stats,ThemeParser,CategorieParser,EmissionParser,VideoParser,StreamParser

from model import Theme,Categorie,Emission,Video,Stream


log=logging.getLogger('theme')



class Wtf(Exception):
  def __init__(self,obj=None):
    self.obj=obj
  def __str__(self):
    if self.obj is not None:
      return '%s'%(self.obj.__dict__)
    return '' 


class MainFetcher(Fetcher):
  ROOTURL='/'
  def __init__(self,session):
    Fetcher.__init__(self,session)
    return
  
  def fetch(self):
    # make the request
    log.debug('requesting %s'%(self.ROOTURL))
    Fetcher.request(self,self.ROOTURL)
    data=self.handleResponse()
    return data    


class NullSession:
  def merge(self,obj):
    return obj

class Main:
  '''
    Emission are grouped into categories, which are part off one of the 6 main Themes.
  '''
  log=log
  categories=None
  aPath='./h2[1]/a[1]'
  data=None
  themes=None
  root=None
  #
  def __init__(self,session=None):
    self.session=session
    if self.session is None:
      self.session = NullSession()
    return
  #
  def parseContent(self,fetcher):
    self.data=fetcher.fetch()
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
    parser=ThemeParser()
    # else
    self.root=lxml.html.fromstring(self.data)
    #themes = '/html/body/div[2]/div[9]/div[3-7]/h2'
    #themesId='/html/body/div[2]/div[9]/div[position()>2 and position()<8]'
    themes=[self.session.merge(parser.parse(theme)) for theme in self.root.xpath(parser.xPath)]
    self.themes=dict()
    for t in themes:
      self.themes[t.text]=t
    return self.themes

  def makeCategories(self,theme):
    #catPath='./div/h3'
    parser=CategorieParser(theme)
    categories=[self.session.merge(parser.parse(cat)) for cat in theme.element.xpath(parser.xPath)]
    log.debug('categories: %s'%(categories))
    #theme.addCategories(categories)
    return categories

  def makeEmissions(self,categorie):
    #emPath='..//a'
    parser=EmissionParser(categorie)
    emissions=[self.session.merge(parser.parse(em)) for em in categorie.element.xpath(parser.xPath)]
    #category.addEmissions(emissions)
    return emissions

  def save(self):
    pass
    
