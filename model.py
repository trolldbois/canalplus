#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging,os,urlparse
from core import parseElement,Wtf

import lxml.etree

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint

log=logging.getLogger('stream')

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()





