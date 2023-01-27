from castle.cms import ua
from castle.cms.interfaces import IDashboardUtils
from castle.cms.lockout import get_active_sessions
from castle.cms.lockout import SessionManager
from castle.cms.utils import publish_content
from collective.elasticsearch.es import ElasticSearchCatalog
from elasticsearch import TransportError
from plone import api
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import IHideFromBreadcrumbs
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.Five import BrowserView
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import alsoProvides
from zope.interface import implements
from zope.security import checkPermission

import socket


class Dashboard(BrowserView):

    def __call__(self):
        self.dashboard = self.get_dashboard()
        view = api.content.get_view(
            name='layout_view', context=self.dashboard, request=self.request)
        self.request.set('disable_border', 1)
        self.request.set('disable_plone.leftcolumn', 0)
        self.request.set('disable_plone.rightcolumn', 0)
        return view()

    def get_dashboard(self):
        write = False
        with api.env.adopt_roles(['Manager']):
            if 'dashboards' not in self.context.objectIds():
                write = True
                api.content.create(type='Folder', title='Dashboards', id='dashboards',
                                   container=self.context, exclude_from_nav=True)
            dashboards = self.context['dashboards']
            if not IHideFromBreadcrumbs.providedBy(dashboards):
                alsoProvides(dashboards, IHideFromBreadcrumbs)
            if api.content.get_state(obj=dashboards, default='Unknown') not in (
                    'published', 'publish_internally'):
                write = True
                publish_content(dashboards)

        member = api.user.get_current()
        user_id = member.getId()
        if user_id not in dashboards.objectIds():
            with api.env.adopt_roles(['Manager']):
                write = True
                # first make sure it is in allowed types...
                pts = api.portal.get_tool('portal_types')
                Folder = pts['Folder']
                if 'Dashboard' not in Folder.allowed_content_types:
                    allowed = list(Folder.allowed_content_types)
                    allowed.append('Dashboard')
                    Folder.allowed_content_types = tuple(allowed)

                aspect = ISelectableConstrainTypes(dashboards)
                if (aspect.getConstrainTypesMode() != 1 or
                        ['Dashboard'] != aspect.getImmediatelyAddableTypes()):
                    aspect.setConstrainTypesMode(1)
                    aspect.setImmediatelyAddableTypes(['Dashboard'])

                api.content.create(type='Dashboard', title='Dashboard', id=user_id,
                                   container=dashboards, exclude_from_nav=True)

        dashboard = dashboards[user_id]
        if dashboard.getOwner().getId() != user_id:
            with api.env.adopt_roles(['Manager']):
                write = True
                dashboard.changeOwnership(member.getUser(), recursive=False)
                dashboard.reindexObjectSecurity()
        if write:
            alsoProvides(self.request, IDisableCSRFProtection)

        return dashboard


class DashboardUtils(BrowserView):
    implements(IDashboardUtils)

    default_interests = (
        'Document',
        'News Item',
        'Link',
        'Folder',
        'UPLOAD',
        'MANAGE'
    )

    def __call__(self):
        alsoProvides(self.request, IBlocksTransformEnabled)

        self.site = api.portal.get()
        if (self.request.REQUEST_METHOD == 'POST' and
                self.request.form.get('removesession') == 'yes'):
            session_id = self.request.form.get('id')
            user = api.user.get_current()
            sm = SessionManager(api.portal.get(), self.request, user)
            sm.session_id = session_id
            sm.expire()
        self._user_cache = {}
        self.pas_member = getMultiAdapter(
            (self.site, self.request), name=u"pas_member")
        self.util = getMultiAdapter((self.site, self.request),
                                    name="castle-utils")
        self.sessions = self.get_open_sessions()

        self.has_add_permission = api.user.has_permission(
            'Add portal content', obj=self.site)

        return self

    def parse_ua(self, session):
        return '%s: %s' % ua.simple_detect(session['ua'])

    def get_open_sessions(self):
        keys_key = '%s-session-%s*' % (
            '-'.join(self.site.getPhysicalPath()[1:]),
            api.user.get_current().getId()
        )
        session_id = self.request.cookies.get('castle_session_id', None)
        sessions = []
        for session in get_active_sessions(keys_key):
            if session['id'] == session_id:
                continue
            sessions.append(session)
        return sessions

    def whois(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            pass

    def get_creator(self, item):
        if item.Creator in self._user_cache:
            return self._user_cache[item.Creator]
        info = self.pas_member.info(item.Creator)
        self._user_cache[item.Creator] = info
        return info

    def get_modifier(self, item):
        try:
            modifier = item.last_modified_by
            try:
                # to check if it is hashable and correct type
                foobar = modifier in self._user_cache  # noqa
            except Exception:
                modifier = item.Creator
        except Exception:
            modifier = item.Creator
        if modifier in self._user_cache:
            return self._user_cache[modifier]
        info = self.pas_member.info(modifier)
        self._user_cache[modifier] = info
        return info

    def _paging(self, query, name):
        try:
            start = int(self.request.form.get(name + '_start'))
        except Exception:
            start = 0
        end = start + 30
        catalog = api.portal.get_tool('portal_catalog')
        # query['sort_limit'] = end
        results = catalog(**query)
        return {
            'start': start,
            'end': end,
            'results': results[start:end],
            'name': name,
            'total': len(results)
        }

    def get_recently_modified(self):
        query = dict(sort_on='modified', sort_order='reverse')
        return self._paging(query, 'modified')

    def get_recently_created(self):
        query = dict(sort_on='created', sort_order='reverse')
        return self._paging(query, 'created')

    def get_in_review(self):
        query = dict(sort_on='modified', review_state='pending', sort_order='reverse')
        return self._paging(query, 'review')

    def get_totals(self):
        query = {
            "size": 0,
            "aggregations": {
                "totals": {
                    "terms": {
                        "field": "portal_type"
                    }
                }
            }
        }
        portal_catalog = api.portal.get_tool('portal_catalog')
        try:
            es = ElasticSearchCatalog(portal_catalog)
            result = es.connection.search(
                index=es.index_name,
                doc_type=es.doc_type,
                body=query)
        except TransportError:
            return []

        return result['aggregations']['totals']['buckets']

    def _get_base_interest_query(self):
        return {
            "size": 0,
            "aggregations": {
                "totals": {
                    "terms": {
                        "field": "parent_folder"
                    }
                }
            }
        }

    def _make_query(self, query):
        portal_catalog = api.portal.get_tool('portal_catalog')
        try:
            es = ElasticSearchCatalog(portal_catalog)
            return es.connection.search(
                index=es.index_name,
                doc_type=es.doc_type,
                body=query)['aggregations']['totals']['buckets']
        except TransportError:
            return []

    def _get_creation_areas_of_interest(self, user_id):
        query = self._get_base_interest_query()
        query['aggregations']['totals']["aggregations"] = {
            "types": {
                "terms": {
                    "field": "portal_type"
                }
            }
        }
        query['query'] = {
            'filtered': {
                'filter': {
                    "and": [
                        {'term': {'Creator': user_id}}
                    ]
                },
                'query': {"match_all": {}}
            }
        }
        return self._make_query(query)

    def _get_contribution_areas_of_interest(self, user_id):
        query = self._get_base_interest_query()
        query['query'] = {
            'filtered': {
                'filter': {
                    "and": [
                        {'term': {'contributors': user_id}}
                    ]
                },
                'query': {"match_all": {}}
            }
        }
        return self._make_query(query)

    def is_root(self, obj):
        return IPloneSiteRoot.providedBy(obj)

    def get_path(self, obj):
        site_path = '/'.join(self.site.getPhysicalPath())
        obj_path = '/'.join(obj.getPhysicalPath())
        return obj_path[len(site_path):]

    def find_areas_of_interest(self):
        max_size = 6
        user_id = api.user.get_current().getId()
        site_path = '/'.join(self.site.getPhysicalPath())
        registry = getUtility(IRegistry)

        interests = []
        upload_found = False
        manage_site_found = False
        for result in self._get_creation_areas_of_interest(user_id):
            for tcount in result['types']['buckets'][:2]:  # max 2 per location
                pt = tcount['key']
                if pt in ('Image', 'File', 'Video', 'Audio'):
                    upload_found = True
                    continue
                if pt in ('Dashboard', 'Feed'):  # ignored types, we should check nice types
                    continue
                interests.append((tcount['key'], result['key'], result['doc_count']))
        if upload_found:
            interests.append(('UPLOAD', '', 1))

        for result in self._get_contribution_areas_of_interest(user_id):
            # since so many will have these areas, ignore
            if result['key'].split('/')[-1] in ('image-repository',
                                                'file-repository'):
                continue
            if result['key'] == site_path:
                manage_site_found = True
                # make it last
                interests.append(('MANAGE', result['key'], -1))
            else:
                interests.append(('MANAGE', result['key'], result['doc_count'] - 1))

        if len(interests) == 0:
            default_interests = list(self.default_interests[:])
            for idx, itype in enumerate(reversed(default_interests)):
                interests.append((itype, site_path, idx))
        elif len(interests) < 6:
            max_size = 6
            default_interests = list(self.default_interests[:])
            if upload_found:
                default_interests.remove('UPLOAD')
            if not manage_site_found:
                default_interests.remove('MANAGE')
            existing = dict([(i[0], i[1]) for i in interests])
            for itype in default_interests:
                if itype in existing and existing[itype] != site_path:
                    continue
                interests.append((itype, site_path, 0))

        interests = [i for i in reversed(sorted(interests, key=lambda x: x[2]))]

        # now to check access
        pts = api.portal.get_tool('portal_types')
        checked_interests = []
        for interest in interests:
            itype = interest[0]
            loc = interest[1]
            if loc != site_path:
                rel_path = loc[len(site_path):]
                folder = api.content.get(path=str(rel_path))
            else:
                folder = self.site

            if itype == 'MANAGE':
                if folder is None:
                    continue
                if checkPermission('cmf.ListFolderContents', folder):
                    checked_interests.append({
                        'type': itype,
                        'loc': folder
                    })
            elif itype == 'UPLOAD':
                file_location = registry.get('file_repo_location', '/file-repository')
                image_location = registry.get('image_repo_location', '/image-repository')
                video_location = registry.get('video_repo_location', '/video-repository')
                audio_location = registry.get('audio_repo_location', '/audio-repository')
                file_folder = api.content.get(path=str(file_location))
                image_folder = api.content.get(path=str(image_location))
                audio_folder = api.content.get(path=str(audio_location))
                video_folder = api.content.get(path=str(video_location))
                tocheck = (
                    ('File', file_folder),
                    ('Image', image_folder),
                    ('Audio', audio_folder),
                    ('Video', video_folder)
                )
                if file_folder is not None or image_folder is not None:
                    for pt_id, folder in tocheck:
                        if folder is None:
                            continue
                        pt = pts[pt_id]
                        if checkPermission(pt.add_permission, folder):
                            checked_interests.append({
                                'type': 'UPLOAD',
                                'loc': None
                            })
                            break
            else:
                if folder is None:
                    continue
                pt = pts[itype]
                if checkPermission(pt.add_permission, folder):
                    checked_interests.append({
                        'type': itype,
                        'loc': folder,
                        'pt': pt
                    })
        return checked_interests[:max_size]
