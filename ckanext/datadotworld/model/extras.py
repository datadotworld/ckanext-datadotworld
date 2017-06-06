# Copyright 2017 data.world, inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
