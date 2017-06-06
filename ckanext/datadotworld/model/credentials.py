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

    def __repr__(self):
        return '<DataDotWorld Credentials: org={0}, ownerID={1}>'.format(
            self.organization, self.owner
        )
