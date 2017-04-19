import ckan.lib.base as base
import ckan.model as model
import ckan.logic as logic
import ckan.plugins.toolkit as tk
from ckanext.datadotworld.model.credentials import Credentials
from ckan.common import _, request, c
import ckan.lib.helpers as h


class DataDotWorldController(base.BaseController):

    def edit(self, id):
        def validate(data):
            error_dict = {}

            if tk.asbool(data.get('integration', 'False')):
                if not data.get('owner'):
                    error_dict['owner'] = ['Required']
                if not data.get('key'):
                    error_dict['key'] = ['Required']
            if error_dict:
                raise logic.ValidationError(error_dict)


        context = {
            'model': model,
            'session': model.Session,
            'user': c.user or c.author,
            'auth_user_obj': c.userobj}
        data_dict = {
            'id': id
        }
        extra = {
            'errors': {},
            'error_summary': None
        }

        try:
            if not h.check_access('organization_update', data_dict):
                raise logic.NotAuthorized
            c.group_dict = logic.get_action('organization_show')(context, data_dict)
            c.group = context['group']
            c.credentials = c.group.datadotworld_credentials
            if c.credentials is None:
                c.credentials = Credentials(
                    organization=c.group
                )
                model.Session.add(c.credentials)
        except logic.NotFound:
            base.abort(404, _('Organization not found'))
        except logic.NotAuthorized:
            base.abort(401, _('User %r not authorized to edit %s') % (
                c.user, id))
        if request.method == 'POST':
            data = dict(request.POST)
            c.credentials.update(data)
            try:
                validate(data)
            except logic.ValidationError as e:
                extra['errors'] = e.error_dict
                extra['error_summary'] = e.error_summary
            else:
                model.Session.commit()
                return base.redirect_to('organization_dataworld', id=id)

        return base.render('organization/edit_credentials.html', extra_vars=extra)
