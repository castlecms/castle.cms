from castle.cms import archival
from zope.component.hooks import setSite

import argparse
import json
import transaction


parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--file', dest='file', default=False)
parser.add_argument('--site-id', dest='site_id', default='Plone')
parser.add_argument('--site-url', dest='site_url', default='')
args, _ = parser.parse_known_args()

user = app.acl_users.getUser('admin')  # noqa
newSecurityManager(None, user.__of__(app.acl_users))  # noqa
site = app[args.site_id]  # noqa
setSite(site)


fi = open(args.file)
items = json.loads(fi.read())
fi.close()


storage = archival.Storage(site, UrlOpener=archival.RequestsUrlOpener)
count = 0
for item in items:
    count += 1
    content_path = '/' + '/'.join(item['path'].split('/')[2:])
    url = args.site_url.rstrip('/') + content_path
    # need to export UID also
    new_url = storage.add_url(url, content_path, item['uid'])
    if new_url:
        print('imported %s -> %s' % (url, new_url))
    else:
        print('error importing %s' % (url,))
    if count % 100 == 0:
        print('done with %i' % count)
        transaction.commit()

transaction.commit()
