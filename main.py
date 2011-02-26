#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging, re
import lxml.html

from parser import ThemeParser,CategorieParser,EmissionParser,VideoParser,StreamParser
from model import Theme,Categorie,Emission,Video,Stream

log=logging.getLogger('theme')


class NullSession:
  ''' Fake a session merge'''
  def merge(self,obj):
    return obj

class Main:
  '''
    Fetch, load and parse content from canalplus main index page.
    Builds Theme, categories and emissions.
  '''
  log=log
  categories=None
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
    self.root=lxml.html.fromstring(self.data)
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
    self.themes=dict()
    parser=ThemeParser()
    themes=[self.session.merge(theme) for theme in parser.findAll(self.root)]
    for t in themes:
      self.themes[t.text]=t
    return self.themes

  def makeCategories(self,theme):
    parser=CategorieParser(theme)
    categories=[self.session.merge(cat) for cat in parser.findAll(theme.element)]
    log.debug('categories: %s'%(categories))
    return categories

  def makeEmissions(self,categorie):
    parser=EmissionParser(categorie)
    emissions=[self.session.merge(em) for em in parser.findAll(categorie.element)]
    return emissions


