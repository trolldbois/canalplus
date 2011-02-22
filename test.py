#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import codecs,logging,os,random

from core import Stats
from emission import Emission
from video import Video
from theme import Main

log=logging.getLogger('test')


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
  video=Video(419796,1784,'LES GUIGNOLS')
  filefetcher=FileFetcher('test/419796')
  video.parseContent(cache,filefetcher)

  for vfk,vf in cache.items():
    print vfk,vf
  #
  for s in cache[video.vid].streams.values():
    print s
  


#testVideoXml()
#testEmission('test/EmissionPOPO-3442')
#testGuignols()



