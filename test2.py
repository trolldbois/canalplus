#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import codecs,logging,os,random

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

from core import Stats
from theme import Theme
from categorie import Categorie
from emission import Emission
from video import Video
from stream import Stream

log=logging.getLogger('test')

engine = create_engine('sqlite:///canalplus.db',echo=False)
Session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))

def testModel():
  testStream()
  print ''
  testVideo()
  print ''
  testEmission()
  print ''
  testCategorie()
  print ''
  testTheme()
  print ''
  
def testStream():
  #425846|BAS_DEBIT|rtmp://vod-fms.canalplus.fr/ondemand/videos/1102/LES_GUIGNOLS_QUOTIDIEN_110216_AUTO_10737_169_video_L.flv
  s=Stream(425846,'BAS_DEBIT','rtmp://vod-fms.canalplus.fr/ondemand/videos/1102/LES_GUIGNOLS_QUOTIDIEN_110216_AUTO_10737_169_video_L.flv')
  print s
  #read
  session=Session()
  for stream in session.query(Stream).limit(1):
    print stream

def testVideo():
  session=Session()
  for vid in session.query(Video).limit(1):
    print vid
  print vid.streams

def testEmission():
  session=Session()
  for em in session.query(Emission).limit(1):
    print em
  print em.videos

def testCategorie():
  session=Session()
  for cat in session.query(Categorie).limit(1):
    print cat
  print cat.emissions

def testTheme():
  session=Session()
  for theme in session.query(Theme).limit(1):
    print theme
  print theme.categories

def test():
  testModel()


test()

