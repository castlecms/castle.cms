import argparse
import datetime
import json
import os
import tempfile

from zope.component.hooks import setSite
from tendo import singleton
from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from tendo import singleton
from zope.component.hooks import setSite
import transaction
from plone.api.exc import UserNotFoundError
import logging
from plone.namedfile import NamedBlobFile, NamedBlobImage

basePath = '/Users/katieschramm/dev/git/FBI/fbigov-dev/karl_dump'

def import_profiles(args):
    profiles_path = '{}/profiles'.format(args.dump_folder)
    profiles = os.listdir(profiles_path)
    no_errors = True
    
    for filename in profiles:
        json_fi = open(os.path.join(profiles_path, filename), 'r')
        profile = json.load(json_fi)
        json_fi.close()

        fullname = '{} {}'.format(profile['properties']['firstname'], profile['properties']['lastname'])
        try:
            user = api.user.create(email=profile['email'], 
                            username=profile['username'], 
                            password=None, 
                            roles=('Member',),
                            properties=profile['properties'])
            user.setMemberProperties(mapping={ 'phone': profile['properties']['phone'] })
        except Exception as e:
            no_errors = False
            logging.error('error while importing profile for {}, {}'.format(fullname, e))
    return no_errors

def import_groups(args):
    site = api.content.get(path='/')
    api.content.create(container=site, type='Folder', title='blog')
    
    groups_path = '{}/groups'.format(args.dump_folder)
    groups = os.listdir(groups_path)
    for group in groups:
        if os.path.isdir(os.path.join(groups_path, group)):
            if group == 'communities':  # the only folder in groups should be communities
                community_path = os.path.join(groups_path, 'communities')  # community_path = {}/groups/communities

                communities_list = import_communities(community_path)
                api.group.create(groupname='Communities', 
                                 title='Communities', 
                                 description='', 
                                 roles=[], 
                                 groups=[communities_list])
            else:
                logging.error('unexpected directory {}'.format(group))

    api.group.create(groupname='KarlAdmin', 
                     title='Admin', 
                     description='admins', 
                     roles=['Site-Manager'], 
                     groups=[])
    all_groups = api.group.get_groups()
    moderators = []
    for group in all_groups:  # add all moderator groups to group KarlModerators
        if 'moderator' in group.id:
            moderators.append(group.id)
    moderators.append('KarlAdmin')
    api.group.create(groupname='KarlModerator', 
                     title='Moderators', 
                     description='group moderators', 
                     roles=['Editor', 'Contributor'], 
                     groups=moderators)
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

    try:
        for groupname in group_list:  # for each of the core groups
            if groupname in group:
                json_fi = open(os.path.join(groups_path, group), 'r')
                fi = json.load(json_fi)
                json_fi.close

                for member in fi['members']:
                    try:
                        api.group.add_user(groupname=groupname, username=member)
                    except UserNotFoundError:  # not all users in db were migrated
                        pass
                    except Exception as e:
                        logging.error('unexpected error: {}'.format(e))
                group_list.remove(groupname)  # remove the group from the list to shorten the next for loop search
                break
    except Exception as e:
        logging.error('error while importing group {}, {}'.format(group, e))
    

def import_communities(path):  # path = {}/groups/communities
    communities_list = []
    for community_name in os.listdir(path):
        communities_list.append(community_name)
        print('import communites {}/{}'.format(len(communities_list), len(os.listdir(path))))
        community_folder_path = os.path.join(path, community_name)  # {}/groups/communities/<community_name>
        
        for obj in os.listdir(community_folder_path):
            blog_folder_path = os.path.join(community_folder_path, obj)
            if os.path.isdir(os.path.join(community_folder_path, obj)) and obj == 'blog':  # if community has a blog
                blog_folder = api.content.get(path='/blog')  # {}/groups/communities/<community_name>/blog
                community_blog_folder = api.content.create(container=blog_folder, 
                                                           type='Folder',
                                                           title=community_name)
                count = 0
                for blog_post in os.listdir(blog_folder_path):
                    count += 1
                    print('import blog, blog post {}/{}'.format(count, len(os.listdir(blog_folder_path))))
                    
                    attachments = []
                    fake_attachment = 'Copy of _Stress Buster_ Challenge Tracker.pdf'
                    
                    blog_file = open(os.path.join(blog_folder_path, blog_post))
                    blog_dump = json.load(blog_file)
                    blog_file.close()

                    for attachment in blog_dump['data']['attachments']:
                        split = fake_attachment.split('.')
                        # split = attachment.split('.')
                        attachment_name = split[0]
                        
                        fi = open(os.path.join('{}/_blog_attachments/__data__{}.json'.format(basePath, attachment_name)), 'rb')
                        data_attachment_dump = json.load(fi)
                        fi.close()

                        attach_fi = open(os.path.join('{}/_blog_attachments/{}'.format(basePath, fake_attachment)), 'rb')
                        # attach_fi = open(os.path.join('{}/_blog_attachments/{}'.format(basePath, attachment)), 'rb')  # {}/groups/communities/<community_name>/blog/<blog_name>/<blog_item>.json
                        temp_fi = tempfile.TemporaryFile()
                        temp_fi.write(attach_fi.read())
                        attach_fi.close()

                        try:
                            file_obj = api.content.create(                          
                                container=community_blog_folder,
                                type='File', 
                                id=attachment,                             
                                title=attachment, 
                                safe_id=True
                            )
                            if 'image' in data_attachment_dump['mimetype']:
                                file_obj.file = NamedBlobImage(                          
                                    data=temp_fi,                                  
                                    contentType=data_attachment_dump['mimetype'],                   
                                    filename=attachment,            
                                )
                            else:
                                file_obj.file = NamedBlobFile(                          
                                    data=temp_fi,                                  
                                    contentType=data_attachment_dump['mimetype'],                   
                                    filename=attachment,            
                                )
                            attachments.append(file_obj)
                            transaction.commit()
                            fi.close()
                        except:
                            pass
                    blog_obj = api.content.create(type='News Item', 
                                       title=blog_dump['title'],
                                       container=community_blog_folder,
                                       subject=blog_dump['title'],
                                       description=blog_dump['description'],
                                       contributors=[blog_dump['modified_by']],
                                       effective_date=datetime.datetime.strptime(blog_dump['created'], "%Y-%m-%d %H:%M:%S.%f"),
                                       creation_date=datetime.datetime.strptime(blog_dump['created'], "%Y-%m-%d %H:%M:%S.%f"),
                                       attachments=attachments,
                                       comments=blog_dump['data']['comments'],
                                       text=blog_dump['text'],
                                       creators=[blog_dump['creator']],
                    )
                    if 'admin' in blog_obj.contributors:
                        index = blog_obj.contributors.index('admin')
                        contributors = blog_obj.contributors[:(index-1)] + blog_obj.contributors[(index+1):]
                        blog_obj.contributors = contributors
                    mod = api.content.get('/blog/{}/{}'.format(community_name, blog_obj.id))
                    mod.setModificationDate(datetime.datetime.strptime(blog_dump['modified'], "%Y-%m-%d %H:%M:%S.%f"))                  

            elif obj == '{}.json'.format(community_name):
                try:  # create community
                    fi = open(os.path.join(community_folder_path, obj), 'r') # {}/groups/communities/<community_name>/<community_name>.json
                    dump_fi = json.load(fi)  # load community .json file
                    fi.close()

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
                except Exception as e:
                    logging.error('error while importing community {}, {}'.format(path, e))
            else:
                logging.error('unexpected folder or filefile {}'.format(obj))
    return communities_list

def migrate(args):
    # import_profiles(args)
    # transaction.commit()
    # if no_profile_errors:
    #     print('Successfully imported all profiles')
    # else:
    #     raise Exception('error importing profiles')
    import_groups(args)
    transaction.commit()

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