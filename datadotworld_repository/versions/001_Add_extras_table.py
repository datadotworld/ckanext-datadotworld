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

from sqlalchemy import Table, Column, UnicodeText, ForeignKey, MetaData
import ckan.model as model
from ckanext.datadotworld.model import States
metadata = MetaData()


extras = Table(
    'datadotworld_extras', metadata,
    Column(
        'package_id', UnicodeText(), ForeignKey(model.Package.id),
        primary_key=True, nullable=False),
    Column('owner', UnicodeText()),
    Column('id', UnicodeText()),
    Column('state', UnicodeText(), default=States.uptodate),
    Column('message', UnicodeText())
)


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    extras.create()


def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    extras.drop()
