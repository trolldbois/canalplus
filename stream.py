#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging,os,urlparse
from core import Base,Element,Fetcher,Wtf

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint

import lxml.etree

log=logging.getLogger('stream')



