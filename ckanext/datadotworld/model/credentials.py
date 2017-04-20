from ckan.model import Group
from sqlalchemy.orm import relationship, backref
from sqlalchemy import (
    UnicodeText,
    ForeignKey,
    Column,
    Boolean
)
from ckanext.datadotworld.model import Base


class Credentials(Base):
    __tablename__ = 'datadotworld_credentials'

    organization_id = Column(
        UnicodeText, ForeignKey(Group.id), primary_key=True)
    integration = Column(Boolean)
    show_links = Column(Boolean)
    key = Column(UnicodeText)
    owner = Column(UnicodeText)

    organization = relationship(
        Group, backref=backref(
            'datadotworld_credentials', uselist=False, cascade='all'))

    def update(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __str__(self):
        return '<DataDotWorld Credentials: org={0}, ownerID={1}>'.format(
            self.organization, self.owner
        )
