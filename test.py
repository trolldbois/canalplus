#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import codecs,logging,os,random

from main import Main
from core import Stats

from theme import Theme
from categorie import Categorie
from emission import Emission
from video import Video,VideoFetcher
from stream import Stream

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

log=logging.getLogger('test')

engine = create_engine('sqlite:///canalplus.db',echo=False)
Session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))



class FileFetcher:
  stats=Stats()
  def __init__(self,filename):
    self.filename=filename
  def fetch(self,obj):
    '''
      Loads a page content from file on disk.
    '''
    data=codecs.open(self.filename,"r").read()
    #try:
    #  data=codecs.open(self.filename,"r","utf-8" ).read()
    #except UnicodeDecodeError,e:
    #  data=codecs.open(self.filename,"r","iso-8859-15" ).read()
    #  #data=unicode(data,'utf-8') 
    return data


def showTree():
  logging.basicConfig(filename='show.log',level=logging.DEBUG)
  main=Main()
  main.parseContent()
  printTree(main.themes.values())


def printTree(themes):
  for t in themes:
    print t
    for c in t.categories.values():
      print '\t',c
      for e in c.emissions.values():
        print '\t\t',e
        for v in e.videos.values():
          print '\t\t\t',v, '%d videos'%( len(v.streams) )


def testGuignols():
  logging.basicConfig(level=logging.DEBUG)
  cache=dict()
  # loading a Emission page
  ## make up an url
  href=lxml.etree.Element("a")
  href.set('href','http://www.canalplus.fr/c-divertissement/pid1784-les-guignols-de-l-info.html?')
  ## build the Emission
  em=Emission(href)
  em.parseContent()
  print em.videos.values()
  ## we now have a bunch of videos we nee to fetch
  cache=dict()
  for vid in em.videos.values():
    vid.parseContent(cache)
    print vid
    for s in vid.streams.values():
      print '\t',s


def testTheme():
  logging.basicConfig(filename='log.debug',level=logging.DEBUG)
  main=Main()
  filefetcher=FileFetcher('test/index.html')
  main.parseContent(filefetcher)
  if True:
    printTree(main.themes.values())    
  return


def testEmission(filename=None):
  logging.basicConfig(level=logging.DEBUG)
  cache=dict()
  # (fake) loading a Emission page
  ## make up an url
  href=lxml.etree.Element("a")
  href.set('href','http://www.canalplus.fr/c-divertissement/pid1784-les-guignols-de-l-info.html?')
  ## build the Emission
  em=Emission(href)
  print em
  ## style faking the load
  filefetcher=FileFetcher('test/guignols.html')
  if filename is not None:
    filefetcher=FileFetcher(filename)
  em.parseContent(filefetcher)
  print em.videos.values()
  ## we now have a bunch of videos we nee to fetch
  cache=dict()
  for vid in em.videos.values():
    vid.parseContent(cache)
    print vid
    for s in vid.streams.values():
      print '\t',s
  
def testVideoXml():
  logging.basicConfig(level=logging.DEBUG)
  cache=dict()
  session=Session()
  
  v=Video(421738,3299,'Album de la semaine')
  print v
  video=Video(419796,1784,'LES GUIGNOLS')
  print video
  
  filefetcher=FileFetcher('test/419796')
  videofetcher=VideoFetcher(session)
  data=videofetcher.fetch=filefetcher.fetch
  videofetcher.parseContent(video,cache)

  for vfk,vf in cache.items():
    print vfk,vf
  #
  for s in cache[video.vid].streams:
    print s
  
  print ''
  session.commit()


#testVideoXml()
testEmission('test/EmissionPOPO-3442')
#testGuignols()



