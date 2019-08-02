import argparse
import json
import os

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from castle.cms.cron.utils import setup_site


try:
    from castle.cms.browser.site.addsite import AddCastleSite
except ImportError:
    # required! This could be getting called from upgrade
    # integration tests
    from castle.cms.browser.addsite import AddCastleSite


app = app  # noqa

parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Castle')
parser.add_argument('--delete', dest='delete', default=False)
args, _ = parser.parse_known_args()

user = app.acl_users.getUser('admin')
newSecurityManager(None, user.__of__(app.acl_users))

if args.delete and args.site_id in app.objectIds():
    print('Deleting site {}'.format(args.site_id))
    app.manage_delObjects([args.site_id])

if args.site_id not in app.objectIds():
    req = app.REQUEST
    req.form = {
        'submitted': 'true',
        'site_id': args.site_id,
        'title': args.site_id
    }
    view = AddCastleSite(app, req)
    view()

    site = app[args.site_id]
    setup_site(site)

    # set registry data
    data = json.loads(os.environ.get('REGISTRY_DATA', '{}'))
    registry = site.portal_registry
    for key, value in data.items():
        registry[key] = value

    transaction.commit()
