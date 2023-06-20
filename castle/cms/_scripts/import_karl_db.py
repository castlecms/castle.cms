import argparse
import datetime
import json
import os

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
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

def import_profiles(args):
    profiles_path = '{}/profiles'.format(args.dump_folder)
    profiles = os.listdir(profiles_path)
    count = 0
    for filename in profiles:
        count += 1  # keep track of import profiles for logging purposes
        user_file_path = os.path.join(profiles_path, filename)
        with open(user_file_path, 'r') as json_fi:
            profile = json.load(json_fi)
            
            fullname = '{} {}'.format(profile['properties']['firstname'], profile['properties']['lastname'])
            logging.info('{}/{} reading profile for {}'.format(count, len(profiles), fullname))
            
            if api.user.get(username=profile['username']) is None:
                logging.info('creating profile')
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
            else:
                logging.info('profile already exists')

def import_groups(args):
    site = api.content.get(path='/')
    if api.content.get('/{}/communities'.format(args.site_id)) is None:  # create communitites folder
        api.content.create(container=site, type='Folder', title='communities')
    
    groups_path = '{}/groups'.format(args.dump_folder)  # community_path = {}/groups/
    community_path = '{}/communities'.format(groups_path)  # community_path = {}/groups/communities
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
    transaction.commit()

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
        transaction.commit()
    except:
        logging.error('error while importing group {}'.format(group), exc_info=True)
    
def import_communities(args, path):  # path = {}/groups/communities
    def clean_name(sitepath):
        replace = [':', ',', '#']
        for char in replace:
            sitepath = sitepath.replace(char, '')
        replace = [' ', '(', ')', '.']
        for char in replace:
            sitepath = sitepath.replace(char, '-')
        sitepath = sitepath.replace(' ', '-')
        while '--' in sitepath:
            sitepath = sitepath.replace('--', '-')
        if sitepath.endswith('-'):
            sitepath = sitepath[:-1]
        if sitepath.startswith('-'):
            sitepath = sitepath[1:]
        return sitepath
    
    def transverse(_folderpath, _sitepath):
        _sitepath = clean_name(_sitepath)
        for item in os.listdir(_folderpath):
            if os.path.isfile(os.path.join(_folderpath, item)):
                if not item.startswith('__data__'):
                    comm_attachments(folderpath=_folderpath, sitepath=_sitepath, attachment=item.lower())
            else:
                parent = api.content.get(_sitepath)
                path = clean_name(os.path.join(_sitepath, item.lower()))
                _container = api.content.get(path)
                if _container is None:
                    logging.info('creating folder {}/{}'.format(_sitepath, item.lower()))
                    api.content.create(container=parent, type='Folder', title=item.lower())
                    transaction.commit()
                next_sitepath = os.path.join(_sitepath, item.lower())
                next_folder = os.path.join(_folderpath, item.lower())
                transverse(_folderpath=next_folder, _sitepath=next_sitepath)
        transaction.commit()

    def comm_attachments(folderpath, sitepath, attachment):
        def attachment_check():
            name, ext = os.path.splitext(attachment)
            name = clean_name(name)
            clean_attachment = '{}{}'.format(name, ext)
            if api.content.get(os.path.join(sitepath, clean_attachment)) is None:
                return False  # if attachment doesn't exists
            else:
                return True

        if attachment_check():
            return
        
        if api.content.get(os.path.join(sitepath, attachment)) is None:
            try:
                attachment_fi = os.path.splitext(attachment)
                attachment_name = attachment_fi[0]
                logging.info('importing attachment {}'.format(attachment))
                
                with open('{}/__data__{}.json'.format(folderpath, attachment_name), 'rb') as fi:
                    data_attachment_dump = json.load(fi)
                    try:
                        container = api.content.get(sitepath)
                        if api.content.get(os.path.join(sitepath, attachment_name)) is None:
                            file_obj = api.content.create(                          
                                container=container,
                                type='File', 
                                id=attachment_name,                             
                                title=attachment_name, 
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
                        
                            try:
                                file_obj.setModificationDate(datetime.datetime.strptime(data_attachment_dump['modified'], "%Y-%m-%d %H:%M:%S.%f"))
                                file_obj.creation_date = (datetime.datetime.strptime(data_attachment_dump['created'], "%Y-%m-%d %H:%M:%S.%f"))
                                transaction.commit()
                            except:
                                logging.error('error trying to set modification/creation date for attachment'.format(attachment), exc_info=True)
                    except:
                        logging.error('error while importing attachment {}'.format(attachment), exc_info=True)
            except:
                logging.error('unable to find attachment {} for {}\n'.format(attachment, folderpath), exc_info=True)
        else:
            logging.info('file {} already exists at {}'.format(attachment, sitepath))
    
    communities_site = api.content.get(path='/communities')
    
    communities_list = []
    blog_attachments = {}
    for community_name in os.listdir(path):
        if community_name == ".DS_Store": 
            continue
        communities_list.append(community_name)

        comm_sitepath = '/communities/{}'.format(community_name)
        if api.content.get(path=comm_sitepath) is None:
            api.content.create(container=communities_site, type='Folder', title=community_name)
        comm_site = api.content.get(comm_sitepath)

        logging.info('import community {}/{}'.format(len(communities_list), len(os.listdir(path))))
        comm_attach_sitepath = '{}/files'.format(comm_sitepath)
        if api.content.get(path=comm_attach_sitepath) is None:
            api.content.create(container=comm_site, type='Folder', title='files')
        else:
            communities_list.remove(community_name)

        # community files
        attach_path = '{}/groups/communities/{}/attachments'.format(args.dump_folder, community_name)
        if os.path.exists(attach_path):
            transverse(_folderpath=attach_path, _sitepath=comm_attach_sitepath)
        if api.content.get(path='{}/blog'.format(comm_sitepath)) is None:
            api.content.create(container=comm_site, type='Folder', title='blog')
        blog_site = api.content.get(path='{}/blog'.format(comm_sitepath))
        if api.content.get(path='{}/blog/files'.format(comm_sitepath)) is None:
            api.content.create(container=blog_site, type='Folder', title='files')

        transaction.commit()

        try:  # create community
            with open('{}/{}/{}.json'.format(path, community_name, community_name), 'r') as fi:
                dump_fi = json.load(fi)
                if api.group.get(groupname='{}:moderators'.format(dump_fi['groupname'])) is None:
                    api.group.create(groupname='{}:moderators'.format(dump_fi['groupname']), 
                                    title=dump_fi['title'],
                                    description=dump_fi['description'],
                                    roles=['Editor', 'Contributor'], 
                                    groups=[])
                if api.group.get(groupname='{}:members'.format(dump_fi['groupname'])) is None:
                    api.group.create(groupname='{}:members'.format(dump_fi['groupname']), 
                                    title=dump_fi['title'],
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
        
        # community blog
        community_folder_path = os.path.join(path, community_name)
        blog_folder_path = '{}/blog'.format(community_folder_path)
        comm_blog_sitepath = '/communities/{}/blog'.format(community_name)
        if os.path.exists(community_folder_path):
            count = 0
            for blog_post in os.listdir(community_folder_path):
                if os.path.isdir(os.path.join(community_folder_path, blog_post)) or not blog_post.startswith('blog'):
                    continue
                count += 1
                post_title = os.path.splitext(blog_post)[0].replace('.', '')
                comm_blogpost_sitepath = '{}/{}'.format(comm_blog_sitepath, post_title[4:])
                if api.content.get(path=comm_blogpost_sitepath) is None:
                    logging.info('import blog, blog post {}'.format(post_title[4:]))
                    with open(os.path.join(community_folder_path, blog_post)) as blog_file:
                        blog_dump = json.load(blog_file)
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
                                            blog_attach_sitepath = '{}/files'.format(comm_blog_sitepath)
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
                                                transaction.commit()
                                            
                                            try:
                                                file_obj.setModificationDate(datetime.datetime.strptime(data_attachment_dump['modified'], "%Y-%m-%d %H:%M:%S.%f"))
                                                file_obj.creation_date = (datetime.datetime.strptime(data_attachment_dump['created'], "%Y-%m-%d %H:%M:%S.%f"))
                                                transaction.commit()
                                            except:
                                                logging.error('error trying to set modification/creation date for attachment'.format(finame), exc_info=True)
                                                blog_attachments.update({data_attachment_dump['filename']: file_obj.absolute_url_path()})
                                            
                                            transaction.commit()
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
                            soup = BeautifulSoup(text, features="html.parser")
                            blog_obj = api.content.create(
                                            container=blog_site,
                                            type='News Item',
                                            title=blog_dump['title'],
                                            description=blog_dump['description'],
                                            contributors=blog_dump['modified_by'],
                                            effective_date=datetime.datetime.strptime(blog_dump['created'], "%Y-%m-%d %H:%M:%S.%f"),
                                            creation_date=datetime.datetime.strptime(blog_dump['created'], "%Y-%m-%d %H:%M:%S.%f"),
                                            comments=blog_dump['data']['comments'],
                                            text=soup.text,
                                            creators=(blog_dump['creator'],),
                                        )
                            if 'admin' in blog_obj.contributors:
                                index = blog_obj.contributors.index('admin')
                                if index - 1 == -1:
                                    contributors = blog_obj.contributors[1:]
                                elif index + 1 == len(blog_obj.contributors):
                                    contributors = blog_obj.contributors[:-1]
                                else:
                                    contributors = blog_obj.contributors[:(index-1)] + blog_obj.contributors[(index+1):]
                                blog_obj.contributors = contributors
                            try:
                                blog_obj.setModificationDate(datetime.datetime.strptime(blog_dump['modified'], "%Y-%m-%d %H:%M:%S.%f"))
                                transaction.commit()
                            except:
                                logging.error('error trying to set modification date for community {} blog'.format(community_name), exc_info=True)
        
        # community wiki
        wiki_folder_path = '{}/{}'.format(community_folder_path, 'wiki')  # {}/groups/communities/<community_name>/wiki
        if os.path.exists(wiki_folder_path):
            comm_wiki_sitepath = '/communities/{}/wiki'.format(community_name)
            if api.content.get(comm_wiki_sitepath) is None:
                api.content.create(container=comm_site, type='Folder', title='wiki')
            comm_wiki_site = api.content.get(comm_wiki_sitepath)

            for wiki_page in os.listdir(wiki_folder_path):
                try:
                    page, ext = os.path.splitext(wiki_page)
                    page = page.replace('_', '-')
                    if api.content.get(os.path.join(comm_wiki_sitepath, page)) is None:
                        logging.info('importing wiki page {} for community {}'.format(wiki_page, community_name))
                        with open(os.path.join(wiki_folder_path, wiki_page)) as wiki_file:
                            wiki_dump = json.load(wiki_file)
                            soup = BeautifulSoup(wiki_dump['text'])
                            # create wiki page
                            api.content.create(
                                        container=comm_wiki_site,
                                        type='Document',
                                        title=wiki_dump['title'],
                                        description=wiki_dump['description'],
                                        text=soup.text,
                                    )
                            transaction.commit()
                except:
                    logging.error('error importing wiki page {}'.format(wiki_page))
    return communities_list

def import_tags(args):
    tags_path = '{}/tags'.format(args.dump_folder)
    tags_dir = os.listdir(tags_path)
    for tag_fi in tags_dir:
        tag_path = '{}/{}'.format(tags_path, tag_fi)
        with open(tag_path, 'r') as json_fi:
            import pdb; pdb.set_trace()
            tag_info = json.load(json_fi)
            group = api.group.get('{}:members'.format(tag_info['community']))

def migrate(args):
    # import_profiles(args)
    # import_groups(args)
    import_tags(args)
    # transaction.commit()

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