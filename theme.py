#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#


import logging, re
import lxml.html

from core import Base,Element,Fetcher,Wtf
from emission import EmissionNotFetchable

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship


log=logging.getLogger('theme')



