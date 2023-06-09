from .hidden import TestUser

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
