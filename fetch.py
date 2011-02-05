#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+taleo@gmail.com
#



import httplib, logging, urllib,time
import lxml,lxml.html,re,os
from lxml import etree
from lxml.etree import tostring
from operator import itemgetter, attrgetter

log=logging.getLogger('fetcher')

SERVER='www.canalplus.fr'
PORT=80
METHOD='GET'


def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

class Wtf(Exception):
  pass

class Fetcher():
  headers={'Accept-Language': 'fr,en-us;q=0.7,en;q=0.3', 
          'Accept-Encoding': 'gzip,deflate', 
          'Connection': 'keep-alive', 
          'Keep-Alive': '115', 
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
          'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13', 
          'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7', 
      }
  params=dict()
  def __init__(self,method=METHOD,server=SERVER,port=PORT):
    # open connection
    self.METHOD=method
    self.SERVER=server
    self.PORT=port
    self.conn = httplib.HTTPConnection(self.SERVER, self.PORT)
  
  def getParams(self):
    return self.params

  def getHeaders(self):
    return self.headers

  def printParams(self,params,sep='='):
    for k,v in params.items():
      log.debug('%s%s%s'%(k,sep,v))

  def uncompress(self,cdata):
    import StringIO, gzip
    compressedstream = StringIO.StringIO(cdata) 
    gzipper = gzip.GzipFile(fileobj=compressedstream)
    data = gzipper.read() 
    return data

  def request(self,url):
    params=self.getParams()
    headers=self.getHeaders()
    # make the request
    self.conn.request(self.METHOD,url,params,headers)
    log.info('requested : %s'%(url))
    return self.conn

  def handleResponse(self):
    resp=self.conn.getresponse()
    respC=resp.getheader('connection')
    if respC == 'close':
      log.debug('BAD: connection is closed.')
      log.debug(resp.reason)
      log.debug(resp.getheaders())
      return None
    else:
      data=resp.read()
      if resp.getheader('content-encoding') == 'gzip':
        data=self.uncompress(data)
      return data


class MainFetcher(Fetcher):
  ROOTURL='/'
  data=None
  themes=None
  root=None
  def __init__(self):
    Fetcher.__init__(self)

  def run(self):
    # make the request
    log.debug('requesting %s'%(self.ROOTURL))
    Fetcher.request(self,self.ROOTURL)
    self.data=main.handleResponse()
    self.makeThemes()
    for t in self.themes:
      log.debug('BEFORE %s has %d categories'%(t,len(t.categories)))
      self.makeCategories(t)
      log.debug('AFTER %s has %d categories'%(t,len(t.categories)))
    return self.data

  def makeThemes(self):
    if self.themes !=None:
      return self.themes
    # else
    self.root=lxml.html.fromstring(self.data)
    #themes = '/html/body/div[2]/div[9]/div[3-7]/h2'
    themesId='/html/body/div[2]/div[9]/div[position()>2 and position()<8]'
    self.themes=[Theme(theme) for theme in self.root.xpath(themesId)]
    return self.themes

  def makeCategories(self,theme):
    #
    catPath='./div/h3'
    categories=[Category(cat) for cat in theme.element.xpath(catPath)]
    theme.addCategories(categories)
    return categories

  def makeEmissions(self,category):
    #
    emissions=dict()
    catId='./div/h3'
    catElements=themeEl.xpath(catId)
    for catEl in catElements:
      categories[catEl.text]=themeEl
    self.themes=themes
    return self.themes

    
  def parse(self):
    root=lxml.html.fromstring(self.data)
    menu=root.xpath('/html/body/div[2]/div[9]')[0]
    #menu=root.get_element_by_id('nav')
    #menutxt=tostring(menu, pretty_print=True, method="html")
    #themes = '/html/body/div[2]/div[9]/div[3-7]/h2'
    themesId='/html/body/div[2]/div[9]/div[position()>2 and position()<8]/h2/a'
    themes=root.xpath(themesId)
    categoriesId='/html/body/div[2]/div[9]/div[3]/div/h3'


class Element():
  element=None
  a=None
  text=None
  url=None
  def __init__(self,el):
    self.element=el
    log.debug('Creating a %s'%self.__class__.__name__)
    res=self.element.xpath(self.aPath)
    if len(res) != 1:
      log.debug('DOM error, falling back to xpath string(), no url ')
      print ''
    if len(res)==0:
      self.text=self.element.xpath('string()')
    else:
      self.a=res[0]
      log.debug('A %s'%(tostring(self.a)))
      self.text=self.a.text
      log.debug('TEXT %s '%(self.text))
      self.url=self.a.get('href')
      log.debug('url %s '%(self.url))

class Theme(Element):
  categories=None
  aPath='./h2[1]/a[1]'
  def __init__(self,el,categories=None):
    Element.__init__(self,el)
    self.categories=dict()
    if categories is not None and len(categories) >0:
      self.addCategories(categories)
  #
  def addCategories(self,cats):
    adds=[cat for cat in cats if cat.text not in self.categories]
    for cat in adds:
      self.categories[cat.text]=cat
  #
  def __repr__(self):
    return '<Theme %s>'%(self.text.encode('utf8'))  

class Category(Element):
  emissions=None
  #catPath='/html/body/div[2]/div[9]/div[3]/div/h3'
  aPath='./a[1]'
  def __init__(self,el,emissions=None):
    Element.__init__(self,el)
    self.emissions=dict()
    if emissions is not None and len(emissions) >0:
      self.addEmissions(emissions)
  def addEmissions(self,emms):
    adds=[em for em in emms if em.text not in self.emmissions]
    for emm in adds:
      self.emissions[emm.text]=emm
  #
  def __repr__(self):
    return '<Category %s>'%(self.text.encode('utf8'))  
  


class Emission(Element):
  prefix='/pid(\d)+.*'
  url=None
  def __init__(self,hrefEl):
    Emissions(self,hrefel)
    self.url=self.element.get('href')
    self.parse()
    
  def writeToFile(self,dirname='./'):
    fout=file(os.path.sep.join([dirname,self.prefix+'%s'%self.id]),'w')
    fout.write(self.data)

  def parse(self):
    #f='jobOffer.1'
    #tree= lxml.html.parse(f)
    #root=tree.getroot()
    root=lxml.html.fromstring(self.data)

  def __repr__(self):
    return '<Job page %s : %s/%s>'%(self.url,self.id,self.title)  



logging.basicConfig(level=logging.DEBUG)
main=MainFetcher()
data=main.run()

for t in main.themes:
  print t
  for c in t.categories.values():
    print '\t',c


