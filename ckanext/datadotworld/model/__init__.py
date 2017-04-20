from sqlalchemy.ext.declarative import declarative_base
import ckan.model as model
Base = declarative_base()
metadata = Base.metadata

import ckanext.datadotworld.model.credentials
import ckanext.datadotworld.model.extras


def drop_tables():
    metadata.drop_all(model.meta.engine)


def create_tables():
    metadata.create_all(model.meta.engine)
