#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


class Wtf(Exception):
  def __init__(self,obj=None):
    self.obj=obj
  def __str__(self):
    if self.obj is not None:
      return '%s'%(self.obj.__dict__)
    return '' 

class VideoNotFetchable(Exception):
  '''    Exception raised when the video is unfetchable,
  '''
  def __init__(self,video):
    self.video=video
  def __str__(self):
    return 'VideoNotFetchable %s'%self.video


class EmissionNotFetchable(Exception):
  '''
    Exception raised when the emission name is unknown or unfetchable,
  '''
  def __init__(self,emission):
    self.emission=emission
  def __str__(self):
    return 'EmissionNotFetchable %s'%self.emission
  
  
