#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import codecs,logging,os,random

from main import Main
from emission import EmissionFetcher
from core import EmissionParser,VideoParser,StreamParser
from model import Theme,Categorie,Emission,Video,Stream

import lxml,lxml.html, lxml.etree

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker
from sqlalchemy.sql.expression import desc

engine = create_engine('sqlite:///canalplus.db',echo=False)
Session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))

log=logging.getLogger('update')

class Update:
  def __init__(self):
    self.session=Session()
    return
  def updateNew(self):
    logging.basicConfig(filename='update.log',level=logging.DEBUG)
    #logging.getLogger('core').setLevel(logging.INFO)
    main=Main(self.session)
    main.parseContent()
    # themes, categories and emissions are loaded
    # let's update the database with new emissions
    # load all new videos XML files from  
    self.updateVideos()
    self.session.commit()
    
  def resyncAll(self):
    logging.basicConfig(filename='resync.log',level=logging.DEBUG)
    main=Main()
    main.parseContent()
    # load all new videos XML files from  
    self.updateVideos(True)

  def updateEmissions(self):
    ''' update out of sync videos'''
    ems=session.query(Emission).order_by(Emission.ts).desc()
    #random.shuffle(ems)
    for em in ems:
      try:
        videos=self.updateEmission(em)
        streams=self.updateVideos(em)
      except EmissionNotFetchable,e:
        log.warning(e)
        continue
      done+=1
      log.info("[%3d/%3d] %d new videos \t %s"%(done,len(ems)-done, len(videos),em))
    return
  

  def updateEmission(self,emission,force=False):
    newVideos=set()
    # Refresh content
    fetcher=EmissionFetcher(self.session)
    data=fetcher.fetch(emission)

    root=lxml.html.fromstring(data)
    videoParser=VideoParser(emission)
    videos=[videoParser.parse(element) for element in root.xpath(videoParser.xPath)]
    
    for vid in videos:
      #add/check if video is in DB.
      self.session.merge(vid)
    # all videos are in db. Streams are next
    return videos
    
  def updateVideos(self,emission):
    #reload only videos with no streams for emission em
    videos=self.session.query(Video).with_parent(emission).filter(~Videos.streams.any())
    parsed=set()
    streamParser=VideoParser()
    cntStreams=0
    for video in videos:
      try:
        # step 1
        if videos in parsed:
          log.debug('Video stream XML already parsed %s'%(video))
          continue
        # fetch XML file
        fetcher=VideoFetcher()
        data=fetcher.fetch(video)
        # parse Xml for video
        newvideos,newstreams=streamParser.parseAll(data,video)
        # put model in session
        newvideos=[self.session.merge(myVid) for myVid in newvideos]
        newstreams=[self.session.merge(myStream) for myStream in newstreams]
        cntStream+=len(newstreams)
        # cache parsed videos for step 1
        parsed.update(newvideos)
      except VideoNotFetchable,v:
        continue
    #finished
    cntVideos=len(parsed)
    if (cntVideos+cntStream >0 ): 
      log.info("\t%3d Videos parsee - %3d new streams"%(cntVideos,cntStream ))
    return parsed


class Printer:
  def lastVideos(self,emId):
    session=Session()
    vids=set()
    for em, vid in session.query(Emission,Video).join(Video).filter(Emission.pid==emId).order_by( desc(Video.vid) ).limit(4):
      vids.add(vid)
      log.debug('%s %s %10s\t%s'%(em.text, vid.text, vid.bestStream().quality, vid.bestStream().url))
    return vids


def main():
  u=Update()
  # update all emission
  #u.updateNew()
  ## or just the one we want
  pids=[1830,1784]
  for pid in pids:
    print u.updateEmission(u.session.query(Emission).get(pid))
  #
  p=Printer()
  p.lastVideos(1830)
  p.lastVideos(1784)
  

if __name__ == '__main__':
  main()


