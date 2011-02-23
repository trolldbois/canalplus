#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging, re
import lxml.html

from core import Database,Element,Fetcher,Wtf,parseElement
from categorie import Categorie
from emission import Emission,EmissionNotFetchable


from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint


log=logging.getLogger('theme')


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
    categories=[Categorie(cat,theme.getId()) for cat in theme.element.xpath(catPath)]
    log.debug('categories: %s'%(categories))
    theme.addCategories(categories)
    return categories

  def makeEmissions(self,category):
    emPath='..//a'
    emissions=[Emission(em) for em in category.element.xpath(emPath)]
    category.addEmissions(emissions)
    return emissions

  def save(self,update=False):
    for t in self.themes.values():
      try:
        t.save(update)
      except Wtf,e:
        log.error(e)
        continue
      for cat in t.categories.values():
        cat.save(update)
        for em in cat.emissions.values():
          em.save(update)
    return


