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
