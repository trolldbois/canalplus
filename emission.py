#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging,lxml,re 

from core import Fetcher


from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship

log=logging.getLogger('emission')



class EmissionNotFetchable(Exception):
  '''
    Exception raised when the emission name is unknown or unfetchable,
  '''
  def __init__(self,emission):
    self.emission=emission
  def __str__(self):
    return 'EmissionNotFetchable %s'%self.emission
  
class EmissionFetcher(Fetcher):
  '''
  Http fetcher for an emission.
  '''
  aPath='.'
  pidRE='.+pid(\d+).+'
  # the regexp to get an Video Id from a url
  vidRE='.vid=(\d+)'
  def __init__(self,session):
    Fetcher.__init__(self,session)
    return

  def fetch(self,emission):
    '''
      Loads a Emission Html page content from network.
    '''
    url=emission.url
    # make the request
    log.debug('requesting %s'%(url))
    Fetcher.request(self,url)
    data=self.handleResponse()
    if(data is None):
      raise EmissionNotFetchable(emission)
    return data



