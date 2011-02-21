#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging

from core import Database,Element,Fetcher


log=logging.getLogger('categorie')



class Category(Element):
  emissions=None
  #catPath='/html/body/div[2]/div[9]/div[3]/div/h3'
  aPath='./a[1]'
  def __init__(self,el,emissions=None):
    Element.__init__(self,el)
    self.emissions=dict()
    if emissions is not None and len(emissions) >0:
      self.addEmissions(emissions)
  def addEmissions(self,emms):
    adds=[em for em in emms if em.text not in self.emissions]
    for emm in adds:
      self.emissions[emm.text]=emm
  #
  def __repr__(self):
    return '<Category %s>'%(self.text.encode('utf8'))  
  



