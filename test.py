#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import codecs,logging,os,random

from main import Main
from core import Stats
from core import ThemeParser,CategorieParser,EmissionParser,VideoParser,StreamParser

import lxml,lxml.html

from model import Theme,Categorie,Emission,Video,Stream

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

log=logging.getLogger('test')

engine = create_engine('sqlite:///canalplus.db',echo=True)
Session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))



class FileFetcher:
  stats=Stats()
  def __init__(self,filename):
    self.filename=filename
  def fetch(self):
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
    print t.text
    for c in t.categories:
      print '\t',c.text
      for e in c.emissions:
        print '\t\t',e.text
        for v in e.videos:
          print '\t\t\t',v.text, '%d videos'%( len(v.streams) )




def testTheme(filename='test/index.html'):
  #logging.basicConfig(filename='log.debug',level=logging.DEBUG)
  logging.basicConfig(level=logging.DEBUG)
  main=Main()
  filefetcher=FileFetcher(filename)
  main.parseContent(filefetcher)
  print main.themes
  if True:
    printTree(main.themes.values())    
  return


def testVideoParser(filename=None):
  logging.basicConfig(level=logging.DEBUG)
  f=file('test/guignols.html')
  emission=Emission(pid=1784,text='LES GUIGNOLS')
  root=lxml.html.parse(f)
  videoParser=VideoParser(emission)
  videos=[videoParser.parse(element) for element in root.xpath(videoParser.xPath)]
  print videos
  


#testVideoXml()
testVideoParser()
#testGuignols()
#testTheme()
