#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import codecs,logging,os,random,sys

from core import Stats
from main import Main
from update import Printer

log=logging.getLogger('fetcher')

import signal
signal.signal(signal.SIGINT, sys.exit)

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
          print '\t\t\t',v, '%d streams'%( len(v.streams) )



class Fetcher:
  def fetchNew(self,emId):
    p=Printer()
    videos=p.lastVideos(emId)
    for video in videos:
      s=video.bestStream()
      print s
      if os.access(s.makeFilename(),os.F_OK):
        continue
      s.fetchStream()
  

def showDb():
  logging.basicConfig(level=logging.DEBUG)
  #read themes
  tb=ThemeBuilder()
  themes=tb.loadDb()
  printTree(themes)

def main():
  print 'Fetching Guignols and Zapping'
  f=Fetcher()
  f.fetchNew(1830)
  f.fetchNew(1784)
  print 'Fetching done'

if __name__ == '__main__':
  main()




