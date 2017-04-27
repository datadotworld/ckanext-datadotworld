from ckan.model import Package
from sqlalchemy.orm import relationship, backref
from sqlalchemy import (
    UnicodeText,
    ForeignKey,
    Column

)
from ckanext.datadotworld.model import Base, States


class Extras(Base):
    __tablename__ = 'datadotworld_extras'

    package_id = Column(
        UnicodeText, ForeignKey(Package.id), primary_key=True)

    owner = Column(UnicodeText)
    id = Column(UnicodeText)
    state = Column(UnicodeText, default=States.uptodate)
    message = Column(UnicodeText)

    package = relationship(
        Package, backref=backref(
            'datadotworld_extras', uselist=False, cascade='all'))

    def __repr__(self):
        return '<DataDotWorldExtras:pkg={0},ownerID={1},remoteID={2}>'.format(
            self.package, self.owner, self.id
        )
