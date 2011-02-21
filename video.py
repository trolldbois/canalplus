#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging
from core import Database,Element,Fetcher

import lxml.etree

log=logging.getLogger('video')


class Video():
  '''
    Une vieo est determinee par une url REST self.srcUrl + self.vid
  '''
  srcUrl='http://service.canal-plus.com/video/rest/getVideosLiees/cplus/%d'
  vid=None
  bd=None
  hi=None
  hd=None
  def __init__(self,name,vid):
    self.name=name
    self.vid=int(vid)
    self.url=self.srcUrl%(self.vid)
    return
  #
  def update(self,title,subtitle,bd,hi,hd):
    self.title=title
    self.subtitle=subtitle
    self.name='%s - %s'%(self.title,self.subtitle)
    self.bd=bd
    self.hi=hi
    self.hd=hd
    return
    
  def getLink(self):
    ret=self.hd
    if ret is None or len(ret)==0:
      ret = self.hi
    if ret is None or len(ret)==0:
      ret = self.bd
    if ret is None or len(ret)==0:
      ret = 'file://about:bad_links/'
    return ret
  #
  def fetchStream(self):
    '''
      on recupere le stream avec un outils externe ( rtmpdump )
    '''
    url=self.hd
    log.debug(self.mplayer %(url))
    return
  #
  def __repr__(self):
    if self.hd is not None:
      return "<Video %d: %s %s>"%(self.vid,self.name, self.getLink())
    else:
      return "<Video %d: %s>"%(self.vid,self.url)

class VideoFetcher(Fetcher):
  '''
    Agent de recuperation de l'url REST contenant les infos pour cette videos ( ou plusieurs)
  '''
  cache=None
  videosPath='/VIDEOS/VIDEO'
  idPath='./ID'
  infoTitrePath='./INFOS/TITRAGE/TITRE'
  infoSousTitrePath='./INFOS/TITRAGE/SOUS_TITRE'
  # ./TITRE + ./SOUS_TITRE
  linkBDPath='./MEDIA/VIDEOS/BAS_DEBIT'
  linkHIPath='./MEDIA/VIDEOS/HAUT_DEBIT'
  linkHDPath='./MEDIA/VIDEOS/HD'
  def __init__(self):
    Fetcher.__init__(self)
    self.cache=dict()
    #check for mplayer
    self.mplayer="mplayer %s"
    pass

  def fromFile(self,filename):
    '''
      On recupere le contenu par lecture d'un fichier sur disque
    '''
    self.data=file(filename).read()
    self.makeAll()

  def fetch(self,video):
    '''
      On recupere le contenu par le reseau
    '''
    # make the request
    log.debug('requesting %s'%(video.url))
    Fetcher.request(self,video.url)
    self.data=self.handleResponse()
    self.makeAll()
    
  def makeAll(self):
    self.parse()
    pass

  def parse(self):
    # on recupere plusieurs vieos en realite ...
    root=lxml.etree.fromstring(self.data)
    vidz=root.xpath(self.videosPath)
    for desc in vidz:
      mid=int(desc.xpath(self.idPath)[0].text)
      if mid not in self.cache:
        name='%s - %s'%(desc.xpath(self.infoTitrePath)[0].text,desc.xpath(self.infoSousTitrePath)[0].text)
        self.cache[mid]=Video(name,mid)
      # all
      hd=desc.xpath(self.linkHDPath)
      if hd is None or len(hd) <1:
        hd=None
      else:
        hd = hd[0].text
      self.cache[mid].update( desc.xpath(self.infoTitrePath)[0].text,
                desc.xpath(self.infoSousTitrePath)[0].text,
                desc.xpath(self.linkBDPath)[0].text,
                desc.xpath(self.linkHIPath)[0].text,
                hd)
    pass

