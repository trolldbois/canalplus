#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#



import httplib, logging, os, re, sqlite3
import StringIO, gzip
#mechanize
from lxml.etree import tostring

log=logging.getLogger('core')

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



class Element():
  encoding='utf-8'
  element=None
  a=None
  text=None
  url=None
  def __init__(self,el):
    if el is None:
      return
    self.element=el
    log.debug('Creating a %s'%self.__class__.__name__)
    res=self.element.xpath(self.aPath)
    if len(res) != 1:
      log.debug('DOM error, falling back to xpath string(), no url ')
    if len(res)==0:
      self.text=self.element.xpath('string()')
    else:
      self.a=res[0]
      log.debug('A %s'%(tostring(self.a)))
      self.text=self.a.text
      log.debug('TEXT %s '%(self.text))
      self.url=self.a.get('href')
      log.debug('url %s '%(self.url))
    #if self.text is not None:
    #  #print self.text
    #  #self.text=self.text.decode(self.encoding)
    return    

class Database:
  filename=None
  table=None
  conn=None
  def __init__(self,table,filename='canalplus.db'):
    self.filename=filename
    self.table=table
    self.conn=sqlite3.connect(self.filename)
    return
    
  def check(self):
    ''' check problems with database
    '''
    if (not os.access(self.filename,os.W_OK)):
      raise IOError('File is not writeable')
    elif (not os.access(self.filename,os.R_OK)):
      raise IOError('File is not readable')
    elif (self.table is None):
      raise NotImplementedError("self.table")
    elif (self.schema is None):
      raise NotImplementedError("self.schema")
    return

  def checkOrCreate(self):
    self.check()
    # check database ?
    return

  def checkOrCreateTable(self):
    '''
    Check Table or creates it.
    '''
    self.checkOrCreate()
    try:
      self.conn.execute("CREATE TABLE IF NOT EXISTS %s %s"%(self.table,self.schema) )
      self.conn.commit()
    except Exception, e:
      self.conn.rollback()
      raise e
    pass
    
  def selectByID(self,elId):
    cursor=self.conn.cursor()
    cursor.execute(self.__SELECT_ID%(self.table),(elId,))
    return cursor
  
  def selectByName(self,desc):
    cursor=self.conn.cursor()
    cursor.execute(self.__SELECT_DESC%(self.table),(desc,))
    return cursor
 
  def insertmany(self, args):
    self.conn.execute('BEGIN TRANSACTION')
    try:
      self.conn.executemany(self.__INSERT_ALL%self.table,args)
      self.conn.commit()
    except Exception, e:
      self.conn.rollback()
      raise e
    return

  def updatemany(self, args):
    self.conn.execute('BEGIN TRANSACTION')
    try:
      self.conn.executemany(self.__INSERT_ALL%self.table,args)
      self.conn.commit()
    except Exception, e:
      self.conn.rollback()
      raise e
    return
  
  def __setitem__(self,key,item):
    myID=int(key)
    #except ValueError,e:
    if self[myID] is None:
      self.insertMany([item])
    else:
      self.updateMany([item])
    return
    
  
  
