from castle.cms import subscribe
from castle.cms.constants import ALL_SUBSCRIBERS
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import requests
import string


def send(message, numbers):
    if numbers == ALL_SUBSCRIBERS:
        numbers = subscribe.get_phone_numbers()

    if isinstance(numbers, basestring):
        numbers = [numbers]

    clean_numbers = []
    for number in numbers:
        number = ''.join(n for n in number if n in string.digits)
        if len(number) == 10:
            # assume at least american..
            number = '1' + number
        clean_numbers.append(number)

    registry = getUtility(IRegistry)
    auth_id = registry.get('castle.plivo_auth_id')
    auth_token = registry.get('castle.plivo_auth_token')
    src = registry.get('castle.plivo_phone_number')
    src = ''.join(n for n in src if n in string.digits)

    params = {
        'src': src,
        'dst': '<'.join(clean_numbers),
        'text': message
    }
    resp = requests.post(
        'https://api.plivo.com/v1/Account/%s/Message/' % auth_id,
        data=json.dumps(params),
        headers={
            'Content-Type': 'application/json'
        },
        auth=(auth_id, auth_token))
    if resp.status_code in (202, 200):
        try:
            return 'error' not in resp.json()
        except Exception:
            return False
    else:
        return False
