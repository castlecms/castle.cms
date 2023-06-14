from plone import api
import transaction
from datetime import datetime
import calendar
from .karl import Karl

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
