#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging
from core import Database,Element,Fetcher

import lxml.etree

log=logging.getLogger('stream')


class Stream:
  def __init__(self,stream):
    self.stream=stream
  #
  def fetchStream(self):
    ''' on recupere le stream avec un outils externe ( rtmpdump )
    '''
    url=self.stream
    #rtmpdump
    log.debug(self.mplayer %(url))
    return

  def __repr__(self):
    low=min(len(self.stream),20)
    up=max(0,len(self.stream)-20)    
    return "<Stream %s[..]%s >"%(self.stream[:low],self.stream[up:])

