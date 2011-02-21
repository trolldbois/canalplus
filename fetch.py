#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import codecs,logging,os

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



def dumpAll():
  logging.basicConfig(filename='log',level=logging.DEBUG)
  main=ThemeFetcher()
  ef=EmissionFetcher()
  vf=VideoFetcher()
  # my cache is in VideoFetcher
  # other cache in filesytem
  vidCache=os.listdir('cache/')
  # dump all here
  fout=file('urls','w')
  oldcache=vf.cache.copy()
  # run....
  data=main.fetch()
  # unravel all
  for t in main.themes.values():
    print t
    for c in t.categories.values():
      print '\t',c
      for e in c.emissions.values():
        print '\t\t',e
        # fetch each Emission page
        try:
          videos=ef.fetch(e)
        except EmissionNotFetchable,e:
          log.warning(e)
          videos=[]
        # we've got a bunch of video Ids...
        # normally, we shoud it the XML Desc only once by emission 
        # because it contains multiple videos desc
        for vid in videos:
          print '\t\t\t',vid
          # but we are lazy, so we hammer canalplus server.
          if str(vid.vid) in vidCache:
            # except if we already have it
            print 'saved'
            continue
          vf.fetch(vid)
          # we write new infos in file....
          newcache=set(vf.cache) - set(oldcache)
          newitems=[vf.cache[item] for item in newcache] 
          for v in newitems:
            fout.write( ('%s ; %s\n'%(v.hd,v.name)).encode('utf8'))
            mycache=file('cache/%d'%v.vid,'w')
            mycache.write('')
            mycache.close()
          fout.flush()
          oldcache=vf.cache.copy()
  # tafn
  fout.close()


def printTree(themes):
  for t in themes:
    print t
    for c in t.categories.values():
      print '\t',c
      for e in c.emissions.values():
        print '\t\t',e


def test():
  #logging.basicConfig(level=logging.DEBUG)
  main=Main()
  filefetcher=FileFetcher('test/index.html')
  main.parseContent(filefetcher)

  if True:
    printTree(main.themes.values())
    
  return

  # (fake) loading a Emission page
  ## make up an url
  href=lxml.etree.Element("a")
  href.set('href','http://www.canalplus.fr/c-divertissement/pid1784-les-guignols-de-l-info.html?')
  ## build the Emission
  em=Emission(href)
  print em
  ## style faking the load
  filefetcher=FileFetcher('test/guignols.html')
  em.parseContent(filefetcher)
  print em.videos

  # fake a Video Load
  ## we now have a bunch of videos
  video=[vid for vid in em.videos if vid.vid==419796][0]
  cache=dict()
  cache[video.vid]=video
  #href=lxml.etree.Element("a")
  #href.set('href','http://service.canal-plus.com/video/rest/getVideosLiees/cplus/419796')
  #video=Video()
  ## style faking the load
  filefetcher=FileFetcher('test/419796')
  newVideos=video.parseContent(filefetcher,cache)

  for vfk,vf in newVideos.items():
    print vfk,vf
  #
  for s in video.getStreams():
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
showDb()

