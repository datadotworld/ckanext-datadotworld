from ckan.model import Resource
from sqlalchemy.orm import relationship, backref
from sqlalchemy import (
    UnicodeText,
    ForeignKey,
    Column

)
from ckanext.datadotworld.model import Base


class Resource(Base):
    __tablename__ = 'datadotworld_resources'

    resource_id = Column(
        UnicodeText, ForeignKey(Resource.id), primary_key=True)

    url = Column(UnicodeText)
    id = Column(UnicodeText)

    resource = relationship(
        Resource, backref=backref(
            'datadotworld_resource', uselist=False, cascade='all'))

    def __str__(self):
        return '<DataDotWorldResource:res={0},url={1},remoteID={2}>'.format(
            self.resource, self.url, self.id
        )
