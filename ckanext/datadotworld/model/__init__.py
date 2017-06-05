# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
metadata = Base.metadata


class States:
    uptodate = u'up-to-date'
    failed = u'failed'
    pending = u'pending'
    deleted = u'deleted'
