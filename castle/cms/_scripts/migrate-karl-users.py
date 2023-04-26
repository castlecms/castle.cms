import argparse
import json
from zope.component.hooks import setSite
from tendo import singleton
from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from tendo import singleton
from zope.component.hooks import setSite
import transaction


def get_args():
    parser = argparse.ArgumentParser(
        description='Get a report of permissions by role and user')
    parser.add_argument('--site-id', dest='site_id', default='Castle')
    args, _ = parser.parse_known_args()
    return args

def migrate(args):
    fi = open(args.filename)
  
    dump_file = json.load(fi)

    for profile in dump_file:
        fullname = '{} {}'.format(profile.firstname, profile.lastname)
        try:
            api.user.create(email=profile.email, username=profile.username, password=None, roles=('Member',), properties=profile.properties)
        except Exception:
            print('Could not add %s, id %s' % (fullname, profile.username), exc_info=True)
    fi.close()

    transaction.commit()


def run(app):
    singleton.SingleInstance('migrate-karl')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    parser = argparse.ArgumentParser(
    description='...')
    parser.add_argument('--site-id', dest='site_id', default='Castle')
    parser.add_argument('filename', help='json dump file')
    args, _ = parser.parse_known_args()
    
    site = app[args.site_id]
    setSite(site)
    migrate(args)


if __name__ == '__main__':
    run(app)  # noqa