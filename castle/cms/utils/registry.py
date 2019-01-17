from castle.cms import cache
from plone import api
from plone.protect.authenticator import createToken
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


def get_backend_url():
    registry = getUtility(IRegistry)
    backend_url = registry.get('plone.backend_url', None)
    if not backend_url or len(backend_url) == 0:
        return api.portal.get().absolute_url()
    else:
        return backend_url[0]


def no_backend_url(value):
    try:
        url = str(value)
        backend = get_backend_url()
        if backend in url:
            return False
        return True
    except Exception:
        return True


def get_public_url():
    public_url = api.portal.get_registry_record('plone.public_url')
    if not public_url:
        public_url = api.portal.get().absolute_url()
    return public_url


def site_has_icon():
    key = '{}.has_site_icon'.format(
        ''.join(api.portal.get().getPhysicalPath()))
    try:
        has_icon = cache.ram.get(key)
    except KeyError:
        registry = getUtility(IRegistry)
        has_icon = False
        try:
            has_icon = bool(registry['plone.site_icon'])
        except Exception:
            pass
        cache.ram.set(key, has_icon)
    return has_icon


def get_upload_fields(registry=None):
    if registry is None:
        registry = getUtility(IRegistry)
    upload_fields = registry.get('castle.file_upload_fields', None)
    if upload_fields is None:
        # not updated yet, b/w compatiable
        required_upload_fields = registry.get(
            'castle.required_file_upload_fields', []) or []
        result = [{
            'name': 'title',
            'label': 'Title',
            'widget': 'text',
            'required': 'title' in required_upload_fields,
            'for-file-types': '*'
        }, {
            'name': 'description',
            'label': 'Summary',
            'widget': 'textarea',
            'required': 'description' in required_upload_fields,
            'for-file-types': '*'
        }, {
            'name': 'tags',
            'label': 'Tags',
            'widget': 'tags',
            'required': 'tags' in required_upload_fields,
            'for-file-types': '*'
        }, {
            'name': 'youtube_url',
            'label': 'Youtube URL',
            'widget': 'text',
            'required': 'youtube_url' in required_upload_fields,
            'for-file-types': 'video'
        }]
    else:
        result = []
        for field in upload_fields:
            if 'name' not in field:
                continue
            # need to make copy of data otherwise we're potentially
            # modifying the record directly
            data = {}
            data.update(field)
            # make sure all required field are in place
            if data.get('required'):
                data['required'] = str(data['required']).lower() in ('true', 't', '1')
            else:
                data['required'] = False
            if 'label' not in data:
                data[u'label'] = data[u'name'].capitalize()
            if 'widget' not in field:
                data[u'widget'] = u'text'
            if 'for-file-types' not in data:
                data[u'for-file-types'] = u'*'
            result.append(data)
    return result


def get_chat_info():

    try:
        frontpage = api.portal.get_registry_record('castle.rocket_chat_front_page')
        salt = api.portal.get_registry_record('castle.rocket_chat_secret')
    except api.exc.InvalidParameterError:
        frontpage = None
        salt = ''

    if frontpage is None or salt == '':
        return

    if frontpage[-1] != '/':
        frontpage = frontpage + '/'

    url = frontpage.replace('http://', 'ws://')
    url = url + 'websocket'

    current = api.user.get_current()
    base_url = api.portal.get().absolute_url()

    return {
        'url': url,
        'base_url': base_url,
        'frontpage': frontpage,
        'token': createToken(salt),
        'user': getattr(current, 'id', ''),
        'email': current.getProperty('email')
    }
