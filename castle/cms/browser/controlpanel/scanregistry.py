from Products.Five.browser import BrowserView
from castle.cms.cron._scan_registry import get_registry_scan
from json import dumps as json_dumps
import plone.api as api


class ScanRegistryView(BrowserView):

    @property
    def portal_id(self):
        return self.context.absolute_url().split('/')[-1]

    @property
    def categorized_registry(self):
        registry_scan = get_registry_scan()
        registry_keys = registry_scan.keys()
        categorized_registry_scan = {}
        for key, value in registry_scan.items():
            if '/' in key:
                category, subkey = key.split('/')
                subkey = '/' + subkey
            else:
                category, subkey = self.get_category_and_subkey(registry_keys, key.split('.'))
            if category not in categorized_registry_scan:
                categorized_registry_scan[category] = {}
            categorized_registry_scan[category][subkey] = value
        return categorized_registry_scan

    @property
    def json_registry(self):
        return json_dumps(get_registry_scan())

    def should_be_category(self, keys, value, n=2):
        count = 0
        for key in keys:
            if key.startswith(value):
                count += 1
            if count >= n:
                return True
        return False

    def get_category_and_subkey(self, keys, key_parts, period_index=-1):
        if period_index == -1 * len(key_parts):
            key = '.'.join(key_parts)
            return ('uncategorized', key)
        proposed_category = '.'.join(key_parts[:period_index])
        if self.should_be_category(keys, proposed_category):
            new_key = '.' + '.'.join(key_parts[period_index:])
            return (proposed_category, new_key)
        return self.get_category_and_subkey(keys, key_parts, period_index - 1)
