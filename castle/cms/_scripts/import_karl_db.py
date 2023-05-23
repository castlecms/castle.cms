import argparse
import datetime
import json
import os
import shutil

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

logging.basicConfig(level=logging.INFO)

def import_profiles(args):
    profiles_path = os.path.join(args.dump_folder, 'profiles')
    profiles = os.listdir(profiles_path)
    
    for filename in profiles:
        user_file_path = os.path.join(profiles_path, filename)
        with open(user_file_path, 'r') as json_fi:
            profile = json.load(json_fi)
            fullname = '{} {}'.format(profile['properties']['firstname'], profile['properties']['lastname'])
            if api.user.get(username=profile['username']) is None:
                logging.info('creating profile for {}'.format(fullname))
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
                    logging.error('error while importing profile for {}'.format(fullname), exc_info=True)

def import_groups(args):
    site = api.content.get(path='/')
    if api.content.get('/{}/communities'.format(args.site_id)) is None:
        api.content.create(container=site, type='Folder', title='communities')
    
    groups_path = '{}/groups'.format(args.dump_folder)
    community_path = os.path.join(groups_path, 'communities')  # community_path = {}/groups/communities
    communities_list = import_communities(args, community_path)
    
    if api.group.get(groupname='KarlCommunities') is None:
        api.group.create(groupname='KarlCommunities', 
                        title='Communities', 
                        description='',
                        roles=[], 
                        groups=communities_list)
    else:
        karlcomm = api.group.get(groupname='KarlCommunities')
        groups = karlcomm.getProperty('groups')
        if groups is not None:
            for group in communities_list:
                karlcomm.append(group)
        else:
            groups = karlcomm
        karlcomm.setGroupProperties({'groups': groups})
    
    # ----------------creating base groups----------------
    all_groups = api.group.get_groups()
    moderators = []
    for group in all_groups:  # add all moderator groups to group KarlModerators
        if 'moderator' in group.id:
            moderators.append(group.id)
    moderators.append('KarlAdmin')
    if api.group.get(groupname='KarlModerator') is None:
        api.group.create(groupname='KarlModerator', 
                        title='Moderators', 
                        description='group moderators', 
                        roles=['Editor', 'Contributor'], 
                        groups=moderators)
    else:
        karlmoderator = api.group.get(groupname='KarlModerator')
        groups = karlmoderator.getProperty('groups')
        if groups is not None:
            for group in communities_list:
                karlmoderator.append(group)
        else:
            groups = karlmoderator
        karlmoderator.setGroupProperties({'groups': groups})
    
    if api.group.get(groupname='KarlAdmin') is None:
        api.group.create(groupname='KarlAdmin', 
                        title='Admin', 
                        description='admins', 
                        roles=['Site-Manager'], 
                        groups=[])
    
    if api.group.get(groupname='KarlStaff') is None:
        api.group.create(groupname='KarlStaff', 
                        title='Staff', 
                        description='karl staff', 
                        roles=['Reader'], 
                        groups=['KarlAdmin', 'KarlModerator'])
    
    if api.group.get(groupname='KarlCommunications') is None:
        api.group.create(groupname='KarlCommunications', 
                        title='Communications', 
                        description='', 
                        roles=[], 
                        groups=[])
    
    if api.group.get(groupname='KarlUserAdmin') is None:
        api.group.create(groupname='KarlUserAdmin', 
                        title='UserAdmin', 
                        description='', 
                        roles=[], 
                        groups=[])

    group_list = ['KarlAdmin', 'KarlUserAdmin', 'KarlStaff', 'KarlCommunications']
    # ----------------adding members to core groups----------------
    try:
        group_path = '{}/groups'.format(args.dump_folder)
        for groupname in group_list:  # for each of the core groups
            logging.info('adding members to {}'.format(groupname))
            with open('{}/group.{}.json'.format(group_path, groupname), 'r') as json_fi:
                fi = json.load(json_fi)

                for member in fi['members']:
                    try:
                        members = api.user.get_users(groupname=groupname)
                        if member not in members:
                            api.group.add_user(groupname=groupname, username=member)
                    except UserNotFoundError:  # not all users in db were migrated
                        pass
    except:
        logging.error('error while importing group {}'.format(group), exc_info=True)
    
def import_communities(args, path):  # path = {}/groups/communities
    def transverse(_folderpath, _sitepath):
        _sitepath = clean_name(_sitepath)
        for item in os.listdir(_folderpath):
            if os.path.isfile(os.path.join(_folderpath, item)):
                if not item.startswith('__data__') and api.content.get(os.path.join(_sitepath, item.lower())) is None:
                    comm_attachments(folderpath=_folderpath, sitepath=_sitepath, attachment=item.lower())
            else:
                parent = api.content.get(_sitepath)
                _container = api.content.get(os.path.join(_sitepath, clean_name(item.lower())))
                if _container is None:
                    logging.info('creating folder {}'.format(_sitepath))
                    api.content.create(container=parent, type='Folder', title=item.lower())
                next_sitepath = os.path.join(_sitepath, item.lower())
                next_folder = os.path.join(_folderpath, item.lower())
                transverse(_folderpath=next_folder, _sitepath=next_sitepath)
        transaction.commit()
    def comm_attachments(folderpath, sitepath, attachment):
        if api.content.get(os.path.join(sitepath, attachment)) is None:
            try:
                attachment_fi = os.path.splitext(attachment)
                attachment_name = attachment_fi[0]
                logging.info('importing attachment {}'.format(attachment))
                
                with open('{}/__data__{}.json'.format(folderpath, attachment_name), 'rb') as fi:
                    data_attachment_dump = json.load(fi)
                    try:
                        container = api.content.get(sitepath)
                        # if container is None: import pdb; pdb.set_trace()
                        file_obj = api.content.create(                          
                            container=container,
                            type='File', 
                            id=attachment,                             
                            title=attachment, 
                            safe_id=True
                        )
                        with open(os.path.join(folderpath, attachment), 'rb') as attach_fi:
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
                                    filename=data_attachment_dump['filename'],            
                                )
                        transaction.commit()
                    except:
                        logging.error('error while importing blog attachment {}'.format(attachment), exc_info=True)
            except:
                logging.error('unable to find attachment {} for {}\n'.format(attachment, folderpath), exc_info=True)
        else:
            logging.info('file {} already exists at {}'.format(attachment, sitepath))
    def clean_name(sitepath):
        replace = [':', ',', '.', '#']
        for char in replace:
            sitepath = sitepath.replace(char, '')
        replace = [' ', '(', ')']
        for char in replace:
            sitepath = sitepath.replace(char, '-')
        sitepath = sitepath.replace(' ', '-')
        while '--' in sitepath:
            sitepath = sitepath.replace('--', '-')
        if sitepath.endswith('-'):
            sitepath = sitepath[0:-1]
        return sitepath

    communities_site = api.content.get(path='/communities')
    
    communities_list = []
    blog_attachments = {}
    for community_name in os.listdir(path):
        communities_list.append(community_name)

        comm_sitepath = '/communities/{}'.format(community_name)
        if api.content.get(path=comm_sitepath) is None:
            api.content.create(container=communities_site, type='Folder', title=community_name)
        comm_site = api.content.get(comm_sitepath)

        logging.info('import community {}/{}'.format(len(communities_list), len(os.listdir(path))))
        comm_attach_sitepath = '{}/attachments'.format(comm_sitepath)
        if api.content.get(path=comm_attach_sitepath) is None:
            api.content.create(container=comm_site, type='Folder', title='attachments')
        else:
            communities_list.remove(community_name)

        # community files
        attach_path = '{}/groups/communities/{}/attachments'.format(args.dump_folder, community_name)
        if os.path.exists(attach_path):
            transverse(_folderpath=attach_path, _sitepath=comm_attach_sitepath)
        if api.content.get(path='{}/blog'.format(comm_sitepath)) is None:
            api.content.create(container=comm_site, type='Folder', title='blog')
        blog_site = api.content.get(path='{}/blog'.format(comm_sitepath))
        if api.content.get(path='{}/blog/attachments'.format(comm_sitepath)) is None:
            api.content.create(container=blog_site, type='Folder', title='attachments')

        try:  # create community
            with open(os.path.join(path, community_name, '{}.json'.format(community_name)), 'r') as fi:
                dump_fi = json.load(fi)
                if api.group.get(groupname='{}:moderators'.format(dump_fi['groupname'])) is None:
                    api.group.create(groupname='{}:moderators'.format(dump_fi['groupname']), 
                                    title='{}:moderators'.format(dump_fi['title']), 
                                    description=dump_fi['description'],
                                    roles=['Editor', 'Contributor'], 
                                    groups=[])
                if api.group.get(groupname='{}:members'.format(dump_fi['groupname'])) is None:
                    api.group.create(groupname='{}:members'.format(dump_fi['groupname']), 
                                    title='{}:members'.format(dump_fi['title']), 
                                    description=dump_fi['description'], 
                                    roles=['Reader',], 
                                    groups=['{}:moderators'.format(dump_fi['groupname'])])
                count = 0
                member_list = dump_fi['members']
                mem_count = 0
                for member in member_list:  # add community members to group
                    mem_count += 1
                    members = api.user.get_users(groupname='{}:members'.format(dump_fi['groupname']))
                    group_members = []
                    for person in members:
                        group_members.append(person.id)
                    if member not in group_members:
                        try:
                            api.group.add_user(groupname='{}:members'.format(dump_fi['groupname']), 
                                            username=member)
                            logging.info('{}/{} added {} to group {}'.format(mem_count, len(member_list), member, dump_fi['groupname']))
                        except UserNotFoundError:
                            logging.info('{}/{} user {} was not found'.format(mem_count, len(member_list), member))
                            pass
                    else:
                        logging.info('{}/{} {} is already a member of {}'.format(mem_count, len(member_list), member, dump_fi['groupname']))
                transaction.commit()
                for moderator in dump_fi['moderators']:  # add community moderators to group
                    moderators = api.user.get_users(groupname='{}:moderators'.format(dump_fi['groupname']))
                    if member not in moderators:
                        try:
                            api.group.add_user(groupname='{}:moderators'.format(dump_fi['groupname']), 
                                            username=moderator)
                        except UserNotFoundError:
                            continue
                transaction.commit()
        except:
            logging.error('error while importing community {}'.format(path), exc_info=True)
        community_folder_path = os.path.join(path, community_name)
        blog_folder_path = os.path.join(community_folder_path, 'blog')
        comm_blog_sitepath = '/communities/{}/blog'.format(community_name)
        # if community has a blog
        if os.path.exists(blog_folder_path):
            count = 0
            for blog_post in os.listdir(blog_folder_path):
                count += 1
                post_title = os.path.splitext(blog_post)[0].replace('.', '')
                comm_blogpost_sitepath = '{}/{}'.format(comm_blog_sitepath, post_title)
                if api.content.get(path=comm_blogpost_sitepath) is None:
                    logging.info('import blog, blog post {}/{}'.format(count, len(os.listdir(blog_folder_path))))
                    with open(os.path.join(blog_folder_path, blog_post)) as blog_file:
                        blog_dump = json.load(blog_file)
                        if api.content.get(path=comm_blogpost_sitepath) is None:
                            attachments_list = blog_dump['data']['attachments']
                            append_text = ''
                            #community blog
                            if len(attachments_list)>0:
                                attachments_path ='{}/attachments'.format(blog_folder_path)
                                blog_attachments = {}
                                for finame in attachments_list:
                                    finame = finame
                                    try:
                                        filename_tuple = os.path.splitext(finame)
                                        attachment_name = filename_tuple[0]
                                        
                                        with open('{}/__data__{}.json'.format(attachments_path, attachment_name), 'rb') as fi:
                                            data_attachment_dump = json.load(fi)
                                            try:
                                                blog_attach_sitepath = '{}/attachments'.format(comm_blog_sitepath)
                                                container = api.content.get(path=blog_attach_sitepath)
                                                file_obj = api.content.create(                          
                                                    container=container,
                                                    type='File',
                                                    id=finame,                             
                                                    title=finame, 
                                                    safe_id=True
                                                )
                                                
                                                with open(os.path.join(attachments_path, finame), 'rb') as attach_fi:
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
                                                            filename=finame,            
                                                        )
                                                    blog_attachments.update({data_attachment_dump['filename']: file_obj.absolute_url_path()})
                                            except:
                                                logging.error('error while importing blog attachment {}'.format(finame), exc_info=True)
                                    except:
                                        logging.error('unable to find blog attachment {} for {}\n'.format(finame, community_name), exc_info=True)
                                
                                if len(blog_attachments)>0:
                                    append_text = '<br/><br/><h5>Attachments:</h5><br/><ul>'
                                    for filename, url in blog_attachments.items():
                                        append_text += '<li><a href="{}">{}</li>'.format(url, filename)
                                    append_text += '</ul><br/><br/>'
                            text = blog_dump['text'] + append_text
                            blog_obj = api.content.create(
                                        container=blog_site,
                                        type='News Item',
                                        title=post_title,
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
                                mod = api.content.get(comm_blogpost_sitepath)
                                mod.setModificationDate(datetime.datetime.strptime(blog_dump['modified'], "%Y-%m-%d %H:%M:%S.%f"))                  
                            except:
                                logging.error('error trying to set modification date for community {} blog'.format(community_name), exc_info=True)
    return communities_list

def migrate(args):
    # import_profiles(args)
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