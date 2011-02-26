#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

#mechanize

import httplib, logging, os, re, sqlite3
import StringIO, gzip

from model import Emission,Video


log=logging.getLogger('core')

SERVER='www.canalplus.fr'
PORT=80
METHOD='GET'

class Stats:
  NUMREQUEST=0
  SAVEDQUERIES=0  

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def clean(tree,el):
  value=tree.xpath(el)
  if value is None or len(value) <1:
    value=None
  else:
    value = value[0].text
  return value

class Fetcher():
  headers={'Accept-Language': 'fr,en-us;q=0.7,en;q=0.3', 
          'Accept-Encoding': 'gzip,deflate', 
          'Connection': 'keep-alive', 
          'Keep-Alive': '115', 
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
          'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13', 
          'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7', 
      }
  stats=Stats()
  params=dict()
  def __init__(self,session,method=METHOD,server=SERVER,port=PORT):
    #save SQL ORM
    self.session=session
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
    compressedstream = StringIO.StringIO(cdata) 
    gzipper = gzip.GzipFile(fileobj=compressedstream)
    data = gzipper.read() 
    return data

  def request(self,url):
    params=self.getParams()
    headers=self.getHeaders()
    # make the request
    self.conn.request(self.METHOD,url,params,headers)
    self.stats.NUMREQUEST+=1
    log.info('REQUEST %d/%d : requested : %s'%(self.stats.NUMREQUEST,self.stats.NUMREQUEST+self.stats.SAVEDQUERIES,url))
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
  def __init__(self,session):
    Fetcher.__init__(self,session)
    return
  
  def fetch(self):
    # make the request
    log.debug('requesting %s'%(self.ROOTURL))
    Fetcher.request(self,self.ROOTURL)
    data=self.handleResponse()
    return data    

class EmissionFetcher(Fetcher):
  '''
  Http fetcher for an emission.
  '''
  def fetch(self,emission):
    '''
      Loads a Emission Html page content from network.
    '''
    # make the request
    log.debug('requesting %s'%(emission.url))
    Fetcher.request(self,emission.url)
    data=self.handleResponse()
    if(data is None):
      raise EmissionNotFetchable(emission)
    return data


class VideoFetcher(Fetcher):
  def fetch(self,video):
    '''  On recupere le contenu par le reseau
    '''
    # make the request
    log.debug('requesting %s'%(video.url))
    Fetcher.request(self,video.url)
    data=self.handleResponse()
    if(data is None):
      raise VideoNotFetchable(video)
    return data


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

