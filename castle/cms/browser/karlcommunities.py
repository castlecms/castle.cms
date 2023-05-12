from Products.Five import BrowserView
from plone import api

class KarlCommunities(BrowserView):

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
        groups = api.group.get_groups(username=user.get('adobbin'))#'username'))
        groups = [group.id for group in groups]
        return groups

    def subscribe(self, group):
        import pdb; pdb.set_trace()
        user = api.user.get_current()
        api.group.add_user(groupname=group, username=user.get('adobbin'))#'username'))
        self.userGroups()
    
    def unsubscribe(self, group):
        import pdb; pdb.set_trace()
        user = api.user.get_current()
        api.group.remove_user(groupname=group, username=user.get('adobbin'))#'username'))
        self.userGroups()