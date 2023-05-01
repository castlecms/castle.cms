import argparse
import json
import os
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
    parser.add_argument('--dump_folder', dest='dump_folder')
    args, _ = parser.parse_known_args()
    return args

# [
    #Site-Manager ('Allow', group.KarlAdmin', 
        # ('view', 
        # 'comment', 
        # 'edit', 
        # 'create', 
        # 'delete', 
        # 'moderate', 
        # 'administer', 
        # 'delete community', 
        # 'email', 
        # 'view', 
        # 'comment', 
        # 'edit', 
        # 'create', 
        # 'delete', 
        # 'moderate')),
    #Editor, Contributor ('Allow', 'group.KarlModerator', 
        # ('view', 
        # 'comment', 
        # 'edit', 
        # 'create', 
        # 'delete', 
        # 'moderate')), 
    #Reader ('Allow', 'group.KarlStaff', 
        # ('view', 
        # 'comment')
    # )
# ]
basePath = '/Users/katieschramm/dev/git/FBI/fbigov-dev'

def import_profiles(args):
    errors = dict()
    profiles_path = '{}/profiles'.format(args.dump_folder)
    profiles = os.listdir(profiles_path)
    for filename in profiles:
        fi = open(os.path.join(profiles_path, filename))
        profile = json.load(filename)
        fullname = '{} {}'.format(profile['properties']['firstname'], profile['properties']['lastname'])
        try:
            api.user.create(email=profile['email'], username=profile['username'], password=None, roles=('Member',), properties=profile['properties'])
        except Exception:
            errors.update(fullname)
        fi.close()
        transaction.commit()

def import_groups(args):
    api.group.create(groupname='KarlAdmin', title='Admin', description='admins', roles=['Site-Manager'], groups=[])
    api.group.create(groupname='KarlModerator', title='Moderators', description='group moderators', roles=['Editor', 'Contributor'], groups=['KarlAdmin'])
    api.group.create(groupname='KarlStaff', title='Staff', description='karl staff', roles=['Reader'], groups=['KarlAdmin', 'KarlModerator'])
    api.group.create(groupname='KarlCommunications', title='Communications', description='', roles=[], groups=[])
    group_list = ['KarlAdmin', 'KarlModerator', 'KarlStaff', 'KarlCommunications']
    transaction.commit()
    
    groups_path = '{}/groups'.format(args.dump_folder)
    groups = os.listdir(groups_path)
    for group in groups:
        if os.isdir(group):
            if group == 'communities':
                community_path = os.path.join(groups_path)
                import_communities(community_path, group)
            else:
                print('unexpected directory {}'.format(group))
        else:
            for groupname in group_list:
                if groupname in group:
                    fi = open(os.path.join(groups_path, group))
                    dump_file = json.load(fi)
                    for member in dump_file['members']:
                        api.group.add_user(groupname=groupname, username=member)
                    group_list.remove(groupname)
                    break        
    
def import_communities(path):
    community_fi = open(path.community)
    community = json.load(community_fi)
    try:
        api.group.create(groupname='{}:moderators'.format(community['groupname']), title='{}:moderators'.format(community['title']), description=None, roles=['Editor', 'Contributor'], groups=[])
        api.group.create(groupname='{}:members'.format(community['groupname']), title='{}:members'.format(community['title']), description=None, roles=[], groups=['{}:moderators'.format(community['groupname'])])
    except:
        print('Could not add %s to groups' % (path))
    community_fi.close()
    transaction.commit()

def migrate(args):
    profile_errors = import_profiles(args)
    if profile_errors > 0:
        print('Profile errors: {}'.format(profile_errors))
        raise Exception('error importing profiles, check log at {}/errors/profile_errors'.format(basePath))
    else:
        print('Successfully imported all profiles')
    import_groups(args)

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

def setup_and_run():
    conf_path = os.getenv("ZOPE_CONF_PATH", "parts/instance/etc/zope.conf")
    if conf_path is None or not os.path.exists(conf_path):
        raise Exception('Could not find zope.conf at {}'.format(conf_path))

    from Zope2 import configure
    configure(conf_path)
    import Zope2
    app = Zope2.app()
    from Testing.ZopeTestCase.utils import makerequest
    app = makerequest(app)
    app.REQUEST['PARENTS'] = [app]
    from zope.globalrequest import setRequest
    setRequest(app.REQUEST)
    from AccessControl.SpecialUsers import system as user
    from AccessControl.SecurityManagement import newSecurityManager
    newSecurityManager(None, user)

    run(app)


if __name__ == '__main__':
    run(app)  # noqa