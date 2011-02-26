#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

class VideoNotFetchable(Exception):
  '''    Exception raised when the video is unfetchable,
  '''
  def __init__(self,video):
    self.video=video
  def __str__(self):
    return 'VideoNotFetchable %s'%self.video

