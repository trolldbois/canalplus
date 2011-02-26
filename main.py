#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging, re
import lxml.html

from parser import ThemeParser,CategorieParser,EmissionParser,VideoParser,StreamParser
from model import Theme,Categorie,Emission,Video,Stream
from exception import Wtf 

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
    self.themes=self.makeThemes()
    for t in self.themes:
      log.debug('BEFORE %s has %d categories'%(t,len(t.categories)))
      cats=self.makeCategories(t)
      log.debug('AFTER %s has %d categories'%(t,len(t.categories)))
      for cat in cats:
        self.session.flush()
        emms=self.makeEmissions(cat)
        log.debug(' %s has %d emission'%(cat,len(emms)))
    return self.data

  def makeThemes(self):
    parser=ThemeParser()
    # do not merge, it looses .element
    themes=parser.findAll(self.root)
    out=set()
    for t in themes:
      merged=self.session.merge(t)
      merged.element=t.element
      out.add(merged)
    return out

  def makeCategories(self,theme):
    parser=CategorieParser(theme)
    # do not merge, it looses .element
    categories=parser.findAll(theme.element)
    out=set()
    for cat in categories:
      merged=self.session.merge(cat)
      merged.element=cat.element
      out.add(merged)
    log.debug('categories: %s'%(out))
    return out

  def makeEmissions(self,categorie):
    parser=EmissionParser(categorie)
    # do not merge, it looses .element
    emissions=parser.findAll(categorie.element)
    unication=set()
    out=set()
    for em in emissions:
      if em in out:
        log.warning('Ignoring duplicate PID for %s'%(em))
        continue
      merged=self.session.merge(em)
      merged.element=em.element
      out.add(merged)
    return out


