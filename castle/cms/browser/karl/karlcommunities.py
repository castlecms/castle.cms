import logging
from plone import api
import transaction
from datetime import datetime
from .hidden import TestUser
import calendar

class CommunitySubscription():
    def __call__(self):        
        parts = self.request.getURL().split('/')
        length = len(parts)
        if '@@subscribe-community' in parts[length-1]:
            self.subscribe()
        elif '@@unsubscribe-community' in parts[length-1]:
            self.unsubscribe()
        else:
            raise Exception
    
    def get_group(self):
        group_name = self.request.get('groupname')
        group = api.group.get(groupname='{}:members'.format(group_name))
        return group

    def subscribe(self):
        group = self.get_group()
        self.request.response.redirect('{}/@@karl-communities'.format(self.context.absolute_url()))
        user = api.user.get_current()
        transaction.commit()
        api.group.add_user(groupname=group.id, username=user.id)

    def unsubscribe(self):
        group = self.get_group()
        user = api.user.get_current()
        api.group.remove_user(groupname=group.id, username=user.id)
        transaction.commit()
        self.request.response.redirect('{}/@@karl-communities'.format(self.context.absolute_url()))

class Karl(TestUser):
    base_groups = ['Administrators', 'KarlAdmin', 'KarlCommunications', 'KarlCommunities', 'KarlModerator', 'KarlStaff', 'KarlUserAdmin', 'Reviewers', 'Site Administrators', 'AuthenticatedUsers']

    def rescentPage(self, data_list):
        if len(data_list) == 0 or data_list is None:
            return 1
        recent_page = self.request.get('recentPage')
        if recent_page is None:
            recent_page = 1
        else:
            recent_page = int(recent_page)
        last_page = len(data_list)/20 if len(data_list)%20 == 0 else len(data_list)/20+1
        if recent_page<1 or recent_page> last_page:
            raise Exception('page out of range')
        return recent_page
    
    def sort_by_mod_date(self, _obj):
            return _obj.modified()
    
    def transverse_folder(self, folder, data):
        for key, value in folder.items():
            if key == 'files' or key == 'blog' or key == 'wiki':
                pass
            else:
                data.append(value)
            if value.portal_type == 'Folder':
                self.transverse_folder(value, data)
        return data

class KarlCommunities(Karl):

    def info(self):
        groups = api.group.get_groups()
        subscribe_groups = []
        for group in groups:
            if ':members' in group.id:
                subscribe_groups.append(group)   
        return {
            'groups': subscribe_groups
        }

    def userGroups(self):
        user = api.user.get_current()
        groups = api.group.get_groups(username=user.id)
        groups = [group.id for group in groups]
        return groups
    
class KarlGroup(Karl):
    def info(self):
        groupname = self.request.get('groupname')
        group = api.group.get(groupname='{}:members'.format(groupname))
        properties = group.getProperties()
        name = group.id.split(':')[0]
        community_folder = group.communities.get(name)
        blog = community_folder.get('blog')
        if blog is None or len(blog.values()) == 0:
            blog = None
        wiki  =  community_folder.get('wiki')
        if wiki is None or len(wiki.values()) == 0:
            wiki = None

        data_list = list()
        
        self.transverse_folder(community_folder, data_list)
        if data_list is not None and len(data_list) != 0:
            data_list.sort(reverse=True, key=self.sort_by_mod_date)
        recent_page = self.rescentPage(data_list)
        
        user = api.user.get_current()
        roles = api.user.get_roles(username=user.id)

        return {
            'communityId': community_folder.id,
            'title': properties.get('title'),
            'id': group.title_or_id,
            'description': properties.get('description'),
            'files': data_list,
            'recentsPage': recent_page,
            'blog': blog,
            'wiki': wiki,
            'roles': roles,
        }
    
class KarlDashboard(Karl):
    def info(self):
        user = api.user.get_current()
        data_list = list()
        
        group_list = api.group.get_groups(username=user.id)
        
        for group in group_list:
            name = group.id.split(':')[0]
            if name in self.base_groups:
                continue
            community_folder = group.get('communities').get(name)
            self.transverse_folder(community_folder, data_list)
        
        if data_list is not None and len(data_list) != 0:
            data_list.sort(reverse=True, key=self.sort_by_mod_date)

        recent_page = self.rescentPage(data_list)

        communities_of_interest = api.group.get_groups()
        for group in self.base_groups:
            communities_of_interest.remove(api.group.get(groupname=group))
        for group in group_list:
            try:
                communities_of_interest.remove(group)
            except:
                pass
        for group in api.user.get_users(groupname='KarlModerator'):
            try:
                communities_of_interest.remove(group)
            except:
                pass
        for group in communities_of_interest:
            if 'members' not in group.id:
                communities_of_interest.remove(group)

        roles = api.user.get_roles(username=user.id)

        return {
            'user': user,
            'files': data_list,
            'recentsPage': recent_page,
            'coi': communities_of_interest,
            'roles': roles
        }
    
class KarlProfile(Karl):    
    def info(self):
        user = api.user.get_current()
        data_list = list()        
        group_list = api.group.get_groups(username=user.id)
        
        def user_contribution(folder, data):
            for key, value in folder.items():
                if key == 'files' or key == 'blog' or key == 'wiki':
                    pass
                else:
                    if user.id in value.creators or user.id in value.contributors:
                        data.append(value)
                if value.portal_type == 'Folder':
                    user_contribution(value, data)
            return data

        for group in group_list:
            name = group.id.split(':')[0]
            if name in self.base_groups or group.id.split(':')[1] == 'moderators':
                continue
            community_folder = group.get('communities').get(name)
            user_contribution(community_folder, data_list)
        if data_list is not None and len(data_list) != 0:
            data_list.sort(reverse=True, key=self.sort_by_mod_date)
        
        recent_page = self.rescentPage(data_list)

        roles = api.user.get_roles(username=user.id)
        
        return {
            'user': user,
            'files': data_list,
            'recentsPage': recent_page,
            'roles': roles,
        }
    
class KarlBlog(Karl):
    def get_archived(self, item, month, year):
        mod = item.modified()
        if mod.month() == month and mod.year() == year:
            return True
        else:
            return False

    def info(self):
        groupname = self.request.get('groupname')
        date = self.request.get('date')
        group = api.group.get(groupname='{}:members'.format(groupname))
        properties = group.getProperties()
        name = group.id.split(':')[0]
        community_folder = group.communities.get(name)
        blog = community_folder.get('blog')
        if len(blog.values()) == 0:
            blog = None

        data_list = list()
        archive = list()

        self.transverse_folder(community_folder['blog'], data_list)
        if len(data_list) != 0:
            data_list.sort(reverse=True, key=self.sort_by_mod_date)
        
            for item in data_list:
                mod = item.modified()
                _date = '{} {}'.format(calendar.month_name[mod.month()], mod.year())
                if _date not in archive:
                    archive.append(_date)
            
            # filter by date
            if date is not None:
                date = date.split('-')
                month_name = date[0]
                year = int(date[1])
                month = datetime.strptime(month_name, '%B').month
                
                data_list = filter(lambda x: self.get_archived(x, month, year), data_list)
                
        
        user = api.user.get_current()
        roles = api.user.get_roles(username=user.id)

        return {
            'communityId': community_folder.id,
            'title': properties.get('title'),
            'files': data_list,
            'archive': archive,
            'roles': roles,
        }