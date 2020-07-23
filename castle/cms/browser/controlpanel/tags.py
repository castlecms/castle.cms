from plone.app.dexterity.behaviors.metadata import ICategorization
from plone import api
from Products.CMFPlone.resources import add_resource_on_request
from Products.Five import BrowserView
import json


class TagsView(BrowserView):
    label = 'Tag Manager'

    batch_size = 50
    remove_size = 25

    def __call__(self):
        # utility function to add resource to rendered page
        add_resource_on_request(self.request, 'castle-components-tag-manager')

        action = self.request.form.get('action')
        if action:
            self.request.response.setHeader('Content-type', 'application/json')
            if action == 'get':
                data = self.get()
            elif action == 'remove':
                data = self.remove()
            elif action == 'rename':
                data = self.rename()
            return json.dumps(data)
        return super(TagsView, self).__call__()

    def rename(self):
        tag = self.request.form.get('tag')
        new_tag = self.request.form.get('new_tag')
        catalog = api.portal.get_tool('portal_catalog')
        for brain in catalog(Subject=tag)[:self.remove_size]:
            obj = brain.getObject()
            bdata = ICategorization(obj, None)
            if bdata:
                if tag in bdata.subjects:
                    tags = list(bdata.subjects)
                    tags.remove(tag)
                    if new_tag not in tags:
                        tags.append(new_tag)
                    bdata.subjects = tuple(tags)
                    obj.reindexObject(idxs=['Subject'])
        try:
            total = len(catalog._catalog.getIndex('Subject')._index[tag])
        except Exception:
            total = 0
        return {
            'success': True,
            'tag': tag,
            'total': total
        }

    def remove(self):
        tag = self.request.form.get('tag')
        catalog = api.portal.get_tool('portal_catalog')
        for brain in catalog(Subject=tag)[:self.remove_size]:
            obj = brain.getObject()
            bdata = ICategorization(obj, None)
            if bdata:
                if tag in bdata.subjects:
                    tags = list(bdata.subjects)
                    tags.remove(tag)
                    bdata.subjects = tuple(tags)
                    obj.reindexObject(idxs=['Subject'])
        try:
            total = len(catalog._catalog.getIndex('Subject')._index[tag])
        except Exception:
            total = 0
        return {
            'success': True,
            'tag': tag,
            'total': total
        }

    def get(self):
        cat = api.portal.get_tool('portal_catalog')
        index = cat._catalog.getIndex('Subject')
        tags = []
        for name in index._index.keys():
            try:
                number_of_entries = len(index._index[name])
            except TypeError:
                continue
            tags.append({
                'name': name,
                'count': number_of_entries
            })

        sorted_tags = list(reversed(sorted(tags, key=lambda tag: tag['count'])))

        try:
            page = int(self.request.form.get('page'))
        except Exception:
            page = 1

        start = (page - 1) * self.batch_size
        end = start + self.batch_size
        return {
            'success': True,
            'tags': sorted_tags[start:end],
            'total': len(sorted_tags),
            'page': page,
            'batch_size': self.batch_size
        }
