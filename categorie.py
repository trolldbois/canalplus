#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+python@gmail.com
#

import logging

from core import Base,Element,Fetcher

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship


log=logging.getLogger('categorie')



