from zope.component import queryUtility
from zope.security.interfaces import IPermission
from plone import api


def get_managers():
    managers = []
    for admin_user in api.user.get_users():
        user_roles = api.user.get_roles(user=admin_user)
        admin_email = admin_user.getProperty('email')
        if (('Manager' not in user_roles and
                'Site Administrator' not in user_roles) or
                not admin_email):
            continue
        managers.append(admin_user)
    return managers


def get_permission_title(permission):
    add_perm_ob = queryUtility(IPermission, name=permission)
    if add_perm_ob:
        permission = add_perm_ob.title
    return permission


def publish_content(obj):
    try:
        api.content.transition(obj=obj, transition='publish')
    except api.exc.InvalidParameterError:
        try:
            api.content.transition(obj=obj, transition='publish_internally')
        except api.exc.InvalidParameterError:
            # not a valid transition, move on I guess...
            pass


def is_backend(request):
    backend_urls = api.portal.get_registry_record('plone.backend_url', default=[]) or []
    for backend_url in backend_urls:
        if backend_url.startswith(request.SERVER_URL):
            return True
    return False
