#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

import httplib, logging, os, re, sqlite3
import StringIO, gzip
#mechanize
from lxml.etree import tostring

from model import Theme,Categorie,Emission,Video,Stream


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

  def writeToFile(self,data,obj,dirname='./test'):
    '''
    save content to file <dirname>/<self.id>
    '''
    filename=os.path.sep.join([dirname,'%s-%d'%(obj.__class__.__name__,obj.getId()) ])
    fout=file(filename,'w')
    fout.write(data)
    log.info('Written to file %s'%(filename))
    return


class Parser:
  def __init__(self,cls,subPath):
    self.cls=cls
    self.subPath=subPath
    self.log=logging.getLogger(self.__class__.__name__)
    return
  
  def parse(self,el):
    if el is None:
      self.log.debug('Element is None')
      return None
    self.log.debug('Parsing a %s'%self.cls)
    text=''
    url=''
    a=''
    res=el.xpath(self.subPath)
    if len(res)==0:
      self.log.debug('DOM error, falling back to xpath string(), no url ')
      self.log.debug('tree element : %s'%(repr(tostring(el))))
      text=el.xpath('string()')
    else:
      a=res[0]
      self.log.debug('A %s'%(repr(tostring(a))))
      text=a.text
      self.log.debug('TEXT %s '%(repr(text) ))
      url=a.get('href')
      self.log.debug('url %s '%(repr(url) ))
    #if text is not None:
    #  #print text
    #  #text=obj.text.decode(obj.encoding)
    obj=self.makeInstance(a,text,url)
    obj.element=el
    self.log.debug(obj)
    self.log.debug('')
    return obj
  #
  def makeInstance(self,a,text,url):
    raise NotImplementedError()

class ThemeParser(Parser):
  tidRE='.+pid(\d+).+'
  xPath='/html/body/div[2]/div[9]/div[position()>2 and position()<8]'
  subPath='./h2[1]/a[1]'
  def __init__(self):
    cls=Theme
    Parser.__init__(self,cls,self.subPath)
    return
  #
  def getId(self,url):
    '''      Get theme's unique identifier.    '''
    tid=None
    # if there is url, we can parse it to get the TID
    if url is not None :
      # TID is in the URL
      tids=re.findall(self.tidRE,url)
      if len(tids) !=1:
        log.warning('Erreur while parsing TID')
        return None
      tid=int(tids[0])
    else:
      return None
    return tid
  #
  def makeInstance(self,a,text,url):
    obj=self.cls(tid=self.getId(url),url=url,text=text)
    return obj
  
class CategorieParser(Parser):
  xPath='./div/h3'
  subPath='./a'
  def __init__(self,theme):
    cls=Categorie
    self.theme=theme
    Parser.__init__(self,cls,self.subPath)
    return
  #
  def makeInstance(self,a,text,url):
    obj=self.cls(text=text,tid=self.theme.tid)
    return obj

class EmissionParser(Parser):
  xPath='..//a'
  subPath='.'
  pidRE='.+[c,p]id(\d+).+'
  # the regexp to get an Video Id from a url
  vidRE='.vid=(\d+)'
  def __init__(self,cat):
    cls=Emission
    self.cat=cat
    Parser.__init__(self,cls,self.subPath)
    return
  def getId(self,url):
    '''      Get emission's unique identifier.
      Programme Id.
    '''
    # if there is not url, we can't parse it to get the PID
    # PID is in the URL
    pids=re.findall(self.pidRE,url)
    if len(pids) !=1:
      log.warning('Erreur while parsing PID')
      return None
    pid=int(pids[0])
    return pid
  #
  def makeInstance(self,a,text,url):
    obj=self.cls(pid=self.getId(url),url=url,text=text,cid=self.cat.cid)
    return obj

class VideoParser(Parser):
  def __init__(self):
    aPath='.'
    cls=Video
    Parser.__init__(self,cls,aPath)
    return

class StreamParser(Parser):
  def __init__(self):
    aPath='.'
    cls=Stream
    Parser.__init__(self,cls,aPath)
    return


