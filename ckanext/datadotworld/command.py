from ckan.lib.cli import CkanCommand
from pylons import config
import paste.script
import logging
from migrate.versioning.shell import main
from migrate.exceptions import DatabaseAlreadyControlledError
import os.path as path

log = logging.getLogger('ckanext.datadotworld')
repository = path.realpath(path.join(
    path.dirname(__file__), '../../datadotworld_repository'))


class DataDotWorldCommand(CkanCommand):
    """
    ckanext-datadotworld management commands.

    Usage::
        paster datadotworld [command]
    Commands::
        init - prepare migrations
        downgrade - delete tables provided by datadotworld
        upgrade - create/update required tables
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__

    parser = paste.script.command.Command.standard_parser(verbose=True)
    parser.add_option('-c', '--config', dest='config',
                      default='development.ini',
                      help='Config file to use.')

    def command(self):
        self._load_config()

        if not len(self.args):
            print(self.usage)
        elif self.args[0] == 'init':
            self._init()
        elif self.args[0] == 'current_version':
            self._current_version()
        elif self.args[0] == 'available_version':
            self._available_version()
        elif self.args[0] == 'upgrade':
            self._upgrade()
        elif self.args[0] == 'downgrade':
            self._downgrade()
        else:
            print(self.usage)

    def _init(self):
        try:
            argv = [
                'version_control',
                config.get('sqlalchemy.url')
            ]
            main(argv, debug=False, repository=repository)
        except DatabaseAlreadyControlledError:
            print("Migration table already exist")
        else:
            print("Migration table prepared")

    def _current_version(self):
        argv = [
            'db_version',
            config.get('sqlalchemy.url')
        ]
        main(argv, debug=False, repository=repository)

    def _available_version(self):
        argv = [
            'version'
        ]
        main(argv, debug=False, repository=repository)

    def _upgrade(self):
        argv = [
            'upgrade',
            config.get('sqlalchemy.url'),

        ]
        main(argv, debug=False, repository=repository)

    def _downgrade(self):

        argv = [
            'downgrade',
            config.get('sqlalchemy.url'),
        ]
        main(argv, debug=False, repository=repository, version=0)
