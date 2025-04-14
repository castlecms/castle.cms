from castle.cms import subscribe
from castle.cms.constants import ALL_SUBSCRIBERS
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import logging
import requests
import string


logger = logging.getLogger('castle.cms')


def plivo_send(message, auth_id, auth_token, src, numbers):
    params = {
        'src': src,
        'dst': '<'.join(numbers),
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
            logger.error(
                'failed to send message through plivo',
                exc_info=True)
            return False
    else:
        return False


def twilio_send(message, account_sid, auth_token, frm, to):
    # Example curl:
    #  curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/Messages.json" \
    #  --data-urlencode "From=+15017122661" \
    #  --data-urlencode "Body=Hi there" \
    #  --data-urlencode "To=+15558675310" \
    #  -u $TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN

    url = 'https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json'.format(account_sid)
    data = {
        # the format used for phone numbers is "E.164" which means the number needs to
        # start with a "+", have a country code, then have a phone number with area code
        # US would be +15555555555 as example
        "From": "+{}".format(frm),
        "Body": message,
    }
    # twilio's api sends message to 1 recipient per call
    sentall = True
    for t in to:
        # the format used for phone numbers is "E.164" which means the number needs to
        # start with a "+", have a country code, then have a phone number with area code
        # US would be +15555555555 as example
        data["To"] = "+{}".format(t)
        try:
            resp = requests.post(url, data=data, auth=(account_sid, auth_token))
            resp.raise_for_status()
        except Exception:
            logger.error(
                'failed to send message through twilio to "{}"'.format(data["To"]),
                exc_info=True)
            sentall = False

    return sentall


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

    plivo_enabled = registry.get('castle.plivo_enabled')
    twilio_enabled = registry.get('castle.twilio_enabled')
    twilio_override = registry.get('castle.twilio_override')

    plivo_auth_id = registry.get('castle.plivo_auth_id')
    plivo_auth_token = registry.get('castle.plivo_auth_token')
    plivo_src = registry.get('castle.plivo_phone_number')
    plivo_src = ''.join(n for n in plivo_src if n in string.digits)

    plivo_configured = True
    if plivo_auth_id is None or len(plivo_auth_id.strip()) <= 0:
        plivo_configured = False
    elif plivo_auth_token is None or len(plivo_auth_token.strip()) <= 0:
        plivo_configured = False
    elif plivo_src is  None or len(plivo_src.strip()) <= 0:
        plivo_configured = False

    twilio_account_sid = registry.get('castle.twilio_account_sid')
    twilio_auth_token = registry.get('castle.twilio_auth_token')
    twilio_from = registry.get('castle.twilio_from')

    twilio_configured = True
    if twilio_account_sid is None or len(twilio_account_sid.strip()) <= 0:
        twilio_configured = False
    elif twilio_auth_token is None or len(twilio_auth_token.strip()) <= 0:
        twilio_configured = False
    elif twilio_from is  None or len(twilio_from.strip()) <= 0:
        plivo_configured = False

    if plivo_enabled and not twilio_override and plivo_configured:
        plivo_send(message, plivo_auth_id, plivo_auth_token, plivo_src, clean_numbers)
    elif twilio_enabled and twilio_configured:
        twilio_send(message, twilio_account_sid, twilio_auth_token, twilio_from, clean_numbers)

