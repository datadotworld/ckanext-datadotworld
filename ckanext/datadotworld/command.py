from ckan.lib.cli import CkanCommand
import paste.script
import logging
import ckanext.datadotworld.model as d_model

log = logging.getLogger('ckanext.datadotworld')


class DataDotWorldCommand(CkanCommand):
    """
    ckanext-datadotworld management commands.

    Usage::
        paster datadotworld [command]
    Commands::
        init - recreate datadotworld's tables
        drop - delete tables provided by datadotworld
        create - create required tables
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
        elif self.args[0] == 'drop':
            self._drop()
        elif self.args[0] == 'create':
            self._create()
        else:
            print(self.usage)

    def _init(self):
        self._drop()
        self._create()
        log.info("DB tables are reinitialized")

    def _drop(self):
        d_model.drop_tables()
        log.info("DB tables are removed")

    def _create(self):
        d_model.create_tables()
        log.info("DB tables are setup")
