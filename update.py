#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import codecs,logging,os,random

from emission import EmissionNotFetchable,EmissionBuilder,EmissionDatabase
from video import VideoNotFetchable,VideoBuilder
from theme import Main

log=logging.getLogger('update')

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


def main():
  u=Update()
  u.updateNew()

  p=Printer()
  p.lastVideos(1830)
  p.lastVideos(1784)

if __name__ == '__main__':
  main()


