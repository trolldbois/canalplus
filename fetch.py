#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging,os

from core import *
from categorie import *
from emission import *
from video import *
from theme import *

log=logging.getLogger('fetcher')

SERVER='www.canalplus.fr'
PORT=80
METHOD='GET'



def dumpAll():
  logging.basicConfig(filename='log',level=logging.DEBUG)
  main=ThemesFetcher()
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

def test():
  #e=main.themes.values()[1].categories.values()[2].emissions.values()[2]
  #print e
  #print e.url

  ef=EmissionFetcher()
  #videos=ef.fetch(e)
  videos=ef.fromFile('test/guignols.html')
  print videos


  vf=VideoFetcher()
  vf.fromFile('test/419796')

  for vfk,vf in vf.cache.items():
    print vfk,vf

    

  logging.basicConfig(level=logging.DEBUG)
  main=ThemesFetcher()
  #data=main.run()

  data=main.fromFile('test/index.html')

  if True:
    for t in main.themes.values():
      print t
      for c in t.categories.values():
        print '\t',c
        for e in c.emissions.values():
          print '\t\t',e

  #e=main.themes.values()[1].categories.values()[2].emissions.values()[2]
  #print e
  #print e.url

  ef=EmissionFetcher()
  #videos=ef.fetch(e)
  videos=ef.fromFile('test/guignols.html')
  print videos


  vf=VideoFetcher()
  vf.fromFile('test/419796')

  for vfk,vf in vf.cache.items():
    print vfk,vf



#
#dumpAll()
test()

