import argparse
from dateutil import parser
import json
import os

from progressbar import progressbar
from zope.component.hooks import setSite, getSite
from tendo import singleton
from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from tendo import singleton
from zope.component.hooks import setSite
import transaction
from plone.api import portal
from plone.api.exc import UserNotFoundError
import logging

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
    profiles_path = '{}/profiles'.format(args.dump_folder)
    profiles = os.listdir(profiles_path)
    no_errors = True
    
    for filename in progressbar(profiles, 
                                prefix='Profiles Progress: ', 
                                redirect_stdout=True):
        profile = json.load(open(os.path.join(profiles_path, filename), 'r'))
        fullname = '{} {}'.format(profile['properties']['firstname'], profile['properties']['lastname'])
        try:
            api.user.create(email=profile['email'], 
                            username=profile['username'], 
                            password=None, roles=('Member',), 
                            properties=profile['properties'])
        except Exception as e:
            no_errors = False
            logging.error('error while importing profile for {}, {}'.format(fullname, e))
    print('commit transaction')
    transaction.commit()
    return no_errors

def import_groups(args):
    # make main groups
    api.group.create(groupname='KarlAdmin', 
                     title='Admin', 
                     description='admins', 
                     roles=['Site-Manager'], 
                     groups=[])
    api.group.create(groupname='KarlModerator', 
                     title='Moderators', 
                     description='group moderators', 
                     roles=['Editor', 'Contributor'], 
                     groups=['KarlAdmin'])
    api.group.create(groupname='KarlStaff', 
                     title='Staff', 
                     description='karl staff', 
                     roles=['Reader'], 
                     groups=['KarlAdmin', 'KarlModerator'])
    api.group.create(groupname='KarlCommunications', 
                     title='Communications', 
                     description='', 
                     roles=[], 
                     groups=[])
    group_list = ['KarlAdmin', 'KarlModerator', 'KarlStaff', 'KarlCommunications']
    print('commit transaction')
    transaction.commit()
    
    groups_path = '{}/groups'.format(args.dump_folder)
    groups = os.listdir(groups_path)
    print('creating groups')
    for group in groups:
        if os.path.isdir(os.path.join(groups_path, group)):
            if group == 'communities':  # the only folder in groups should be communities
                community_path = os.path.join(groups_path, 'communities')  # community_path = {}/groups/communities
                site = api.content.get(path='/')
                api.content.create(container=site, type='Folder', title='blogs')

                print('creating communities')
                communities_list = import_communities(community_path)
                api.group.create(groupname='Communities', 
                                 title='Communities', 
                                 description='', 
                                 roles=[], 
                                 groups=[communities_list])
                print('commit transaction')
                transaction.commit()
            else:
                logging.error('unexpected directory {}'.format(group))

        else:
            try:
                for groupname in group_list:  # for each of the core groups
                    if groupname in group:
                        fi = json.load(open(os.path.join(groups_path, group), 'r'))
                        for member in fi['members']:
                            try:
                                api.group.add_user(groupname=groupname, username=member)
                                print('added {} to group {}'.format(member, groupname))
                            except UserNotFoundError:  # not all users in db were migrated
                                pass
                            except Exception as e:
                                logging.error('unexpected error: {}'.format(e))
                        group_list.remove(groupname)  # remove the group from the list to shorten the next for loop search
                        break
                print('commit transaction')
                transaction.commit()
            except Exception as e:
                logging.error('error while importing group {}, {}'.format(group, e))

    # add all moderator groups to group KarlModerators
    all_groups = api.group.get_groups()
    moderators = []
    for group in all_groups:
        if 'moderator' in group.id:
            moderators.append(group.id)
    group_tool = api.portal.get_tool(name='portal_groups')
    group_tool.editGroup('KarlModerator', groups=moderators)
    
    print('commit transaction')
    transaction.commit()
    

def import_communities(path):  # path = {}/groups/communities
    communities_list = []
    for community_name in os.listdir(path):
        # progressbar(os.listdir(path), 
        #                                 prefix='Communities Progress: ', 
        #                                 redirect_stdout=False):
        communities_list.append(community_name)
        community_folder_path = os.path.join(path, community_name)  # {}/groups/communities/<community_name>
        
        for obj in os.listdir(community_folder_path):
            # if community has a blog 
            blog_folder_path = os.path.join(community_folder_path, obj)
            if os.path.isdir(os.path.join(community_folder_path, obj)) and obj == 'blog':  # {}/groups/communities/<community_name>/blog
                blog_folder = api.content.get(path='/blogs')
                print('creating community {} blog'.format(community_name))
                community_blog_folder = api.content.create(container=blog_folder, 
                                                           type='Folder',
                                                           title=community_name)
                for blog in os.listdir(blog_folder_path):
                    select_blog_path = os.path.join(blog_folder_path, blog)  # {}/groups/communities/<community_name>/blog/<blog_name>
                    if not os.path.isdir(select_blog_path):  # blog info should be located in its own folder
                        logging.error('unexpected file {}, was expecting a folder'.format(blog))
                    else:
                        blog_count = len(os.listdir(select_blog_path))
                        # select specific blog post folder
                        for item in os.listdir(select_blog_path):  # {}/groups/communities/<community_name>/blog/<blog_post_name>/<blog_post>.json
                            print('community: {}, {}/{} creating {} blog folder'.format(community_name, os.listdir(select_blog_path).index(item)+1, blog_count, blog))
                            select_community_blog_folder = api.content.create(container=community_blog_folder, 
                                                                              type='Folder', 
                                                                              title=item)
                            if os.path.isdir(os.path.join(select_blog_path, item)):  # if there is a folder inside, it should be the attachments folder
                                if item == 'attachments':  # {}/groups/communities/<community_name>/blog/<blog_name>/attachments
                                # go into attachments folder
                                    print('creating {} blog post attachment folder'.format(blog))
                                    attachments_folder = api.content.create(container=select_community_blog_folder, 
                                                                            type='Folder', 
                                                                            title='attachments')
                                    attachments_path = os.path.join(select_blog_path, item)
                                    for attachment in os.listdir(attachments_path):
                                        if attachment.startswith('_data'):  # this is just file data, is here just incase we need it
                                            continue
                                        else:  # add attachments in blog
                                            api.content.copy(source=attachment, 
                                                             target=attachments_folder)
                                else:  # woops! that shouldn't have happened!
                                    logging.error('unexpected folder {}, was expecting attachments folder'.format(item))
                            else:  # {}/groups/communities/<community_name>/blog/<blog_name>/<blog_item>.json
                            # create blog post
                            
                                fi = open(os.path.join(select_blog_path, item), 'r')
                                dump_fi = json.load(fi)
                                fi.close()

                                attachments = dump_fi['attachments']
                                try:
                                    attach = dump_fi['data']['attachments']
                                    for _fi in attach:
                                        attachments.append(_fi)
                                except:
                                    pass

                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(dump_fi['text'])
                                api.content.create(type='News Item', 
                                                   title=dump_fi['title'].encode('ascii', 'ignore'),
                                                   container=select_community_blog_folder,
                                                   subject=dump_fi['title'].encode('ascii', 'ignore'),
                                                   description=dump_fi['description'].encode('ascii', 'ignore'),
                                                   contributors=[dump_fi['creator'].encode('ascii', 'ignore'), dump_fi['modified_by'].encode('ascii', 'ignore')],
                                                   effective_date=parser.parse(dump_fi['created']).date(),
                                                   attachments=attachments,
                                                   comments=dump_fi['data']['comments'],
                                                   text=soup.get_text().replace('\n', '  ').encode('ascii', 'ignore'),
                                )
                    print('commit transaction')
                    transaction.commit()                             

            elif obj == '{}.json'.format(community_name):
                # create community
                try:
                    
                    fi = open(os.path.join(community_folder_path, obj), 'r') # {}/groups/communities/<community_name>/<community_name>.json
                    dump_fi = json.load(fi)  # load community .json file
                    fi.close()
                    print('creating community group {}'.format(community_name))
                    api.group.create(groupname='{}:moderators'.format(dump_fi['groupname']), 
                                    title='{}:moderators'.format(dump_fi['title']), 
                                    description=None, 
                                    roles=['Editor', 'Contributor'], 
                                    groups=[])
                    api.group.create(groupname='{}:members'.format(dump_fi['groupname']), 
                                    title='{}:members'.format(dump_fi['title']), 
                                    description=None, 
                                    roles=[], 
                                    groups=['{}:moderators'.format(dump_fi['groupname'])])
                    for member in dump_fi['members']:  # add community members to group
                        try:
                            api.group.add_user(groupname='{}:members'.format(dump_fi['groupname']), 
                                            username=member)
                        except UserNotFoundError:
                            continue
                    for moderator in dump_fi['moderators']:  # add community moderators to group
                        try:
                            api.group.add_user(groupname='{}:moderators'.format(dump_fi['groupname']), 
                                            username=moderator)
                        except UserNotFoundError:
                            continue
                    print('commit transaction')
                    transaction.commit()
                except Exception as e:
                    logging.error('error while importing community {}, {}'.format(path, e))
            else:
                logging.error('unexpected folder or filefile {}'.format(obj))
    return communities_list

def migrate(args):
    # no_profile_errors = import_profiles(args)
    # if no_profile_errors:
    #     print('Successfully imported all profiles')
    # else:
    #     raise Exception('error importing profiles')
    import_groups(args)

def run(app):
    singleton.SingleInstance('migrate-karl')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    parser = argparse.ArgumentParser(
        description='Get a report of permissions by role and user')
    parser.add_argument('--site-id', dest='site_id', default='Castle')
    parser.add_argument('--dump_folder', dest='dump_folder')
    args, _ = parser.parse_known_args()
    
    site = app[args.site_id]
    setSite(site)
    migrate(args)
    print('sucessfully ran script!!!')

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