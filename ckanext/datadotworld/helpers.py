import ckan.model as model


def admin_in_orgs(name):
    user = model.User.get(name)
    if not user:
        return []
    return user.get_groups('organization', 'admin')
