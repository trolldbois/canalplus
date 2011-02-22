#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import codecs,logging,os,random

from core import *
from categorie import *
from emission import *
from video import *
from theme import *

log=logging.getLogger('fetcher')

SERVER='www.canalplus.fr'
PORT=80
METHOD='GET'

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
    #t.save()
    for c in t.categories.values():
      print '\t',c
      #c.save()
      for e in c.emissions.values():
        print '\t\t',e
        #e.save()
        for v in e.videos.values():
          v.save()
          print '\t\t\t',v, '%d videos'%( len() )


class Update:
  cache=dict()
  ebuilder=EmissionBuilder()
  vbuilder=VideoBuilder()
  def updateNew(self):
    logging.basicConfig(filename='update.log',level=logging.DEBUG)
    #logging.getLogger('core').setLevel(logging.INFO)
    main=Main()
    main.parseContent()
    # themes, categories and emissions are loaded
    # let's update the database with new emissions
    main.save(update=False)
    # load all new videos XML files from  
    self.updateVideos()
    
  def resyncAll(self):
    logging.basicConfig(filename='resync.log',level=logging.DEBUG)
    main=Main()
    main.parseContent()
    #force update
    main.save(update=True)
    # load all new videos XML files from  
    self.updateVideos(True)

    
  def updateVideos(self):
    ems=self.ebuilder.loadDb()
    # we exclude already parsed Videos XMLs. the stream should be in DB.
    self.cache=self.vbuilder.loadVideosWithStreams()
    done=0
    # histoire de...
    #random.shuffle(ems)
    for em in ems:
      try:
        videos=self.updateEmission(em)
      except EmissionNotFetchable,e:
        log.warning(e)
        continue
      done+=1
      log.info("[%3d/%3d] %d new videos \t %s"%(done,len(ems)-done, len(videos),em))
    return

  def updateEmission(self,em,force=False):
    newVideos=set()
    # Refresh content
    em.parseContent()
    ## we now have a bunch of videos XML we need to fetch
    cache=self.cache
    if force:
      # we go with empty cache
      cache=dict()
    cntStream=0
    for vid in em.videos.values():
      try:
        vid.parseContent(cache)
      except VideoNotFetchable,v:
        v.video.save() ## e1
        v.video.streams[0].save() ## s1
        em.updateTs()
        continue
      vid.save()
      # empty cache means, we need to reload vid from cache
      # if not forced , we do not reload XML from db-stored videos
      # so streams will be empty 
      for s in cache[vid.getId()].streams.values():
        if s.save() > 0:
          cntStream+=1
          newVideos.add(vid)
    cntVideos=len(newVideos)
    if (cntVideos+cntStream >0 ): 
      log.info("\t%3d new Videos - %3d new streams"%(cntVideos,cntStream ))
    # update timestamps
    em.updateTs()
    return newVideos

class Printer:
  def lastVideos(self,emId):
    emDb=EmissionDatabase()
    newVideos=set()
    em=emDb[emId]
    # get videos and streams
    vBuilder=VideoBuilder()
    em.addVideos(vBuilder.loadForEmission(em))
    for vid in em.videos.itervalues():
      for stream in vid.streams.itervalues():
        print '%s %s %10s\t%s'%(em.text, vid.text,stream.quality,stream.url)
    return em.videos

class Fetcher:
  def fetchNew(self,emId):
    p=Printer()
    videos=p.lastVideos(emId)
    for video in videos.itervalues():
      s=video.bestStream()
      if os.access(s.makeFilename(),os.F_OK):
        continue
      s.fetchStream()

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
  

def showDb():
  logging.basicConfig(level=logging.DEBUG)
  #read themes
  tb=ThemeBuilder()
  themes=tb.loadDb()
  printTree(themes)

#
#dumpAll()
#test()
#showDb()
#showTree()

#u=Update()
#u.updateNew()

#p=Printer()
#p.lastVideos(1830)
#p.lastVideos(1784)

f=Fetcher()
f.fetchNew(1830)
f.fetchNew(1784)



#testVideoXml()
#testEmission('test/EmissionPOPO-3442')
#testGuignols()

# guignols 1784
# zapping 1830
#updateEmission(1784)






