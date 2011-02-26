#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import codecs,logging,os,random,sys

from exception import Wtf,VideoNotFetchable,EmissionNotFetchable
from main import Main
from core import MainFetcher,EmissionFetcher,VideoFetcher
from parser import EmissionParser,VideoParser,StreamParser
from model import Base,Theme,Categorie,Emission,Video,Stream

import lxml,lxml.html, lxml.etree

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker
from sqlalchemy.sql.expression import desc

engine = create_engine('sqlite:///canalplus.db',echo=False)
Session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))
Base.metadata.create_all(engine)

log=logging.getLogger('update')

class Update:
  def __init__(self):
    self.session=Session()
    self.session.commit()
    return
  
  def updateNew(self):
    logging.basicConfig(filename='update.log',level=logging.DEBUG)
    #logging.getLogger('core').setLevel(logging.INFO)
    main=Main(self.session)
    main.parseContent(MainFetcher())
    self.session.flush()
    # themes, categories and emissions are loaded
    # let's update the database with new emissions
    # load all new videos XML files from  
    self.updateEmissions()
    self.session.commit()
    
  def resyncAll(self):
    logging.basicConfig(filename='resync.log',level=logging.DEBUG)
    main=Main()
    main.parseContent()
    # load all new videos XML files from  
    self.updateVideos(True)

  def updateEmissions(self):
    ''' update out of sync videos'''
    ems=self.session.query(Emission).order_by(desc(Emission.ts))
    done=0
    #random.shuffle(ems)
    for em in ems:
      try:
        videos=self.updateEmission(em)
        self.session.commit()
        streams=self.updateVideos(em)
        self.session.commit()
      except EmissionNotFetchable,e:
        log.warning(e)
        continue
      done+=1
      log.info("[%3d/%3d] %d new videos \t %s"%(done,ems.count()-done, len(videos),em))
    return
  

  def updateEmission(self,emission,force=False):
    if emission is None:
      log.error("Pas d'emission")
      raise EmissionNotFetchable(emission)
    newVideos=set()
    # Refresh content
    fetcher=EmissionFetcher()
    data=fetcher.fetch(emission)

    root=lxml.html.fromstring(data)
    videoParser=VideoParser(emission)
    videos=set([videoParser.parse(element) for element in root.xpath(videoParser.xPath)])
    log.warning('%s'%(videos))
    for vid in videos:
      #add/check if video is in DB.
      self.session.merge(vid)
    self.session.flush()
    # all videos are in db. Streams are next
    return videos
    
  def updateVideos(self,emission):
    #reload only videos with no streams for emission em
    videos=self.session.query(Video).with_parent(emission).filter(~Video.streams.any())
    parsed=set()
    fetcher=VideoFetcher()
    streamParser=StreamParser(emission,parsed)
    cntStream=0
    for video in videos:
      try:
        # step 1
        log.debug('************* XML-todo %s'%(video))
        if videos in parsed:
          log.debug('Video stream XML already parsed %s'%(video))
          continue
        # fetch XML file
        data=fetcher.fetch(video)
        # parse Xml for video
        root=lxml.etree.fromstring(data)
        newvideos,newstreams=streamParser.findAll(root)
        # put model in session
        #self.session.add_all(newvideos)
        #self.session.add_all(newstreams)
        newvideos=set([self.session.merge(myVid) for myVid in newvideos])
        newstreams=set([self.session.merge(myStream) for myStream in newstreams])
        log.warning('%s'%(newstreams))
        cntStream+=len(newstreams)
        # cache parsed videos for step 1
        parsed.update(newvideos)
        log.debug('************* XML-parsed %s'%(parsed))
      except VideoNotFetchable,v:
        streamParser.writeToFile(data,video,video.vid)
        continue
      self.session.commit()
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
      print '%s %s %10s\t%s'%(em.text, vid.text, vid.bestStream().quality, vid.bestStream().url)
    return vids


def main():

      
  u=Update()
  if len(sys.argv) == 2:
    arg=sys.argv[1]
    if arg == 'refresh':
      # update all emission
      u.updateNew()
      return
  ## or just the one we want
  pids=[1830,1784]
  for pid in pids:
    em=u.session.query(Emission).get(pid)
    videos=u.updateEmission(em)
    streams=u.updateVideos(em)
    for vid in videos:
      print 'Emission ',pid,'video ',vid.vid,vid.text
    u.session.commit()
  #
  p=Printer()
  p.lastVideos(1830)
  p.lastVideos(1784)
  

if __name__ == '__main__':
  main()


