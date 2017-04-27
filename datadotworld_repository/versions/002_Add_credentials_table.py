from sqlalchemy import (
    Table, Column, UnicodeText,
    ForeignKey, MetaData, Boolean
)
import ckan.model as model
metadata = MetaData()


extras = Table(
    'datadotworld_credentials', metadata,
    Column(
        'organization_id', UnicodeText(), ForeignKey(model.Group.id),
        primary_key=True, nullable=False),
    Column('integration', Boolean()),
    Column('show_links', Boolean()),
    Column('key', UnicodeText()),
    Column('owner', UnicodeText())
)


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    extras.create()


def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    extras.drop()
