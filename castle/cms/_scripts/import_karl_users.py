import argparse
import datetime
import json
import os

from zope.component.hooks import setSite, getSite
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
    
    for filename in profiles:
        json_fi = open(os.path.join(profiles_path, filename), 'r')
        profile = json.load(json_fi)
        json_fi.close()

        fullname = '{} {}'.format(profile['properties']['firstname'], profile['properties']['lastname'])
        try:
            user = api.user.create(email=profile['email'], 
                            username=profile['username'], 
                            password=None, 
                            roles=('Member',))
            
            user.setMemberProperties(mapping={
                'phone_number': profile['properties']['phone'],
                'biography': profile['properties']['biography'],
                'location': profile['properties']['location'],
                'fullname': fullname,
                'home': profile['properties']['home_path'],
            })

            user.fax = profile['properties']['fax'],
            user.office = profile['properties']['office'],
            user.firstname = profile['properties']['firstname'],
            user.lastname = profile['properties']['lastname'],
            user.categories = profile['properties']['categories'],
            user.two_factor_phone = profile['properties']['two_factor_phone'],
            user._alert_prefs= profile['properties']['_alert_prefs'],
            user.websites = profile['properties']['websites'],
            user.position = profile['properties']['position'],
            user.two_factor_verified = profile['properties']['two_factor_verified'],
            user.date_format = profile['properties']['date_format'],
            user.organization = profile['properties']['organization'],
            user.password_reset_key = profile['properties']['password_reset_key'],
            user.extension = profile['properties']['extension'],
            user.industry = profile['properties']['industry'],
            user.preferred_communities = profile['properties']['preferred_communities'],
            user.password_reset_time = profile['properties']['password_reset_time'],
            user.languages = profile['properties']['languages'],
            user.country = profile['properties']['country'],
            user.department = profile['properties']['department'],
            user._pending_alerts = profile['properties']['_pending_alerts'],
            user.room_no = profile['properties']['room_no'],

            transaction.commit()
        except Exception as e:
            logging.error('error while importing profile for {}, {}'.format(fullname, e))

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
                    
                    blog_attachments = {}

                    blog_file = open(os.path.join(blog_folder_path, blog_post))
                    blog_dump = json.load(blog_file)
                    blog_file.close()

                    for attachment in blog_dump['data']['attachments']:
                        # fake_attachment = 'Copy of _Stress Buster_ Challenge Tracker.pdf'
                        # attachment = fake_attachment
                        
                        split = attachment.split('.')
                        attachment_name = split[0]
                        
                        fi = open(os.path.join('{}/_blog_attachments/__data__{}.json'.format(basePath, attachment_name)), 'rb')
                        data_attachment_dump = json.load(fi)
                        fi.close()

                        attach_fi = open(os.path.join('{}/_blog_attachments/{}'.format(basePath, attachment)), 'rb')  # {}/groups/communities/<community_name>/blog/<blog_name>/<blog_item>.json
                        temp_fi = open('{}/{}'.format(basePath, attach_fi), 'wb')
                        temp_fi.write(attach_fi.read())
                        attach_fi.close()
                        temp_fi.close()

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
                                    filename=data_attachment_dump['filename'],            
                                )
                            else:
                                file_obj.file = NamedBlobFile(                          
                                    data=temp_fi,                                  
                                    contentType=data_attachment_dump['mimetype'],                   
                                    filename=attachment,            
                                )
                            blog_attachments.update({data_attachment_dump['filename']: file_obj.absolute_url_path()})
                            fi.close()
                        except Exception as e:
                            logging.error('{}, line 178'.format(e))
                    append_text = ''
                    if len(blog_attachments)>0:
                        append_text = '<br/><br/><h5>Attachments:</h5><br/><ul>'
                        for filename, url in blog_attachments.items():
                            append_text += '<li><a href="{}">{}</li>'.format(url, filename)
                        append_text += '</ul><br/><br/>'
                    text = blog_dump['text'] + append_text
                    blog_obj = api.content.create(type='News Item',
                                       title=blog_dump['title'],
                                       container=community_blog_folder,
                                       subject=blog_dump['title'],
                                       description=blog_dump['description'],
                                       contributors=blog_dump['modified_by'],
                                       effective_date=datetime.datetime.strptime(blog_dump['created'], "%Y-%m-%d %H:%M:%S.%f"),
                                       creation_date=datetime.datetime.strptime(blog_dump['created'], "%Y-%m-%d %H:%M:%S.%f"),
                                       comments=blog_dump['data']['comments'],
                                       text=text,
                                       creators=blog_dump['creator'],
                               )
                    if 'admin' in blog_obj.contributors:
                        index = blog_obj.contributors.index('admin')
                        contributors = blog_obj.contributors[:(index-1)] + blog_obj.contributors[(index+1):]
                        blog_obj.contributors = contributors
                    try:
                        mod = api.content.get('/blog/{}/{}'.format(community_name, blog_obj.id))
                        mod.setModificationDate(datetime.datetime.strptime(blog_dump['modified'], "%Y-%m-%d %H:%M:%S.%f"))                  
                    except Exception as e:
                        import pdb; pdb.set_trace()
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
    import_profiles(args)
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