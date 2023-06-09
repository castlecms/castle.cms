from .karl import Karl
from plone import api

class KarlUsers(Karl):
    def get_users(self, user, username=None, fname=None, lname=None):
        if username:
            if username in user.id:
                return True
        if fname:
            if fname in user.firstname:
                return True
        if lname:
            if lname in user.lastname:
                return True
        return False
            
    def info(self):
        username = self.request.get('username')
        fname = self.request.get('fname')
        lname = self.request.get('lname')

        members_list = api.user.get_users()

        if username or fname or lname:
            filter(lambda x: self.get_users(user=x, username=username, fname=fname, lname=lname), members_list)
        return {
            'members': members_list,
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
    
