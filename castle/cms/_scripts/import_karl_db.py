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


def import_profiles(args):
    profiles_path = '{}/profiles'.format(args.dump_folder)
    profiles = os.listdir(profiles_path)
    
    for filename in profiles:
        with open(os.path.join(profiles_path, filename), 'r') as json_fi:
            profile = json.load(json_fi)

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
        except:
            logging.error('error while importing profile for {}, {}'.format(fullname), exc_info=True)

def import_groups(args):
    site = api.content.get(path='/')
    api.content.create(container=site, type='Folder', title='communities')
    
    groups_path = '{}/groups'.format(args.dump_folder)
    groups = os.listdir(groups_path)
    for group in groups:
        if os.path.isdir(os.path.join(groups_path, group)):
            if group == 'communities':  # the only folder in groups should be communities
                community_path = os.path.join(groups_path, 'communities')  # community_path = {}/groups/communities

                communities_list = import_communities(args, community_path)
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
                with open(os.path.join(groups_path, group), 'r') as json_fi:
                    fi = json.load(json_fi)

                for member in fi['members']:
                    try:
                        api.group.add_user(groupname=groupname, username=member)
                    except UserNotFoundError:  # not all users in db were migrated
                        pass
                    except:
                        logging.error('unexpected error', exc_info=True)
                group_list.remove(groupname)  # remove the group from the list to shorten the next for loop search
                break
    except:
        logging.error('error while importing group {}'.format(group), exc_info=True)
    
def import_communities(args, path):  # path = {}/groups/communities
    communities_list = []
    
    site = api.content.get(path='/')
    api.content.create(container=site, type='Folder', title='blog')
    blog_folder = api.content.get(path='/blog')
    
    for community_name in os.listdir(path):
        communities_list.append(community_name)
        logging.info('import communites {}/{}'.format(len(communities_list), len(os.listdir(path))))

        communities_site = api.content.get(path='/communities')
        api.content.create(container=blog_folder, type='Folder', title='{}'.format(community_name))
        blog_site = api.content.get(path='/blog/{}'.format(community_name))
        api.content.create(container=blog_site, type='Folder', title='attachments')
        attachment_folder = api.content.get(path='/blog/{}/attachments'.format(community_name))

        try:  # create community
            with open(os.path.join(path, community_name, '{}.json'.format(community_name)), 'r') as fi:
                dump_fi = json.load(fi)

            api.group.create(groupname='{}:moderators'.format(dump_fi['groupname']), 
                            title='{}:moderators'.format(dump_fi['title']), 
                            description=None, 
                            roles=['Editor', 'Contributor'], 
                            groups=[])
            api.group.create(groupname='{}:members'.format(dump_fi['groupname']), 
                            title='{}:members'.format(dump_fi['title']), 
                            description=None, 
                            roles=['Reader',], 
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
            api.content.create(container=communities_site, type='Document', title=community_name, description=dump_fi['description'])
        except:
            logging.error('error while importing community {}'.format(path), exc_info=True)

        community_folder_path = os.path.join(path, community_name)
        
        for obj in os.listdir(community_folder_path):
            if obj == '{}.json'.format(community_name):
                continue
            blog_folder_path = os.path.join(community_folder_path, obj)
            if os.path.isdir(os.path.join(community_folder_path, obj)) and obj == 'blog':  # if community has a blog
                count = 0
                for blog_post in os.listdir(blog_folder_path):
                    count += 1
                    logging.info('import blog, blog post {}/{}'.format(count, len(os.listdir(blog_folder_path))))
                    
                    blog_attachments = {}

                    with open(os.path.join(blog_folder_path, blog_post)) as blog_file:
                        blog_dump = json.load(blog_file)

                    for attachment in blog_dump['data']['attachments']:
                        try:
                            filename_tuple = os.path.splitext(attachment)
                            attachment_name = filename_tuple[0]
                            
                            with open(os.path.join('{}/_blog_attachments/__data__{}.json'.format(args.dump_folder, attachment_name)), 'rb') as fi:
                                data_attachment_dump = json.load(fi)
                        except:
                            logging.error('unable to find blog attachment {} for community {}\n'.format(attachment, community_name), exc_info=True)
                        try:
                            file_obj = api.content.create(                          
                                container=attachment_folder,
                                type='File', 
                                id=attachment,                             
                                title=attachment, 
                                safe_id=True
                            )
                            with open(os.path.join('{}/_blog_attachments/{}'.format(args.dump_folder, attachment)), 'rb') as attach_fi:
                                if 'image' in data_attachment_dump['mimetype']:
                                    file_obj.file = NamedBlobImage(                          
                                        data=attach_fi.read(),                                  
                                        contentType=data_attachment_dump['mimetype'],                   
                                        filename=data_attachment_dump['filename'],            
                                    )
                                else:
                                    file_obj.file = NamedBlobFile(                          
                                        data=attach_fi.read(),                                  
                                        contentType=data_attachment_dump['mimetype'],                   
                                        filename=attachment,            
                                    )
                            blog_attachments.update({data_attachment_dump['filename']: file_obj.absolute_url_path()})
                        except:
                            logging.error('error while importing blog attachment {}'.format(attachment), exc_info=True)
                    append_text = ''
                    if len(blog_attachments)>0:
                        append_text = '<br/><br/><h5>Attachments:</h5><br/><ul>'
                        for filename, url in blog_attachments.items():
                            append_text += '<li><a href="{}">{}</li>'.format(url, filename)
                        append_text += '</ul><br/><br/>'
                    text = blog_dump['text'] + append_text
                    blog_obj = api.content.create(
                                       container=blog_site,
                                       type='News Item',
                                       title=blog_dump['title'],
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
                    except:
                        logging.error('error trying to set modification date for community {} blog'.format(community_name), exc_info=True)
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