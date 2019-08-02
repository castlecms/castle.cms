from castle.cms import cache
from castle.cms import social
from castle.cms.services.google import analytics
from plone import api
from Products.Five import BrowserView
from zope.component import getMultiAdapter

import json


class AnalyticsView(BrowserView):

    def __call__(self):
        self.request.response.setHeader('Content-type', 'application/json')
        paths = self.get_paths()
        if self.request.get('api') == 'ga':
            data = self.ga_api_call(paths)
        else:
            data = social.get_stats(self.context)
            if data:
                data = dict(data)

        return json.dumps({
            'paths': paths,
            'data': data
        })

    def ga_api_call(self, paths):
        service = analytics.get_ga_service()
        if not service:
            return

        profile = self.get_ga_profile(service)
        if not profile:
            return

        params = json.loads(self.request.get('params'))

        if self.request.get('type') == 'realtime':
            ga = service.data().realtime()
            if not params.pop('global', False):
                # need to restrict by filters
                path_query = ','.join(['rt:pagePath==%s' % p for p in paths])
                params['filters'] = path_query
        else:
            if not params.pop('global', False):
                # need to restrict by filters
                path_query = ','.join(['ga:pagePath==%s' % p for p in paths])
                params['filters'] = path_query
            ga = service.data().ga()

        cache_key = '-'.join(api.portal.get().getPhysicalPath()[1:])
        for key, value in params.items():
            cache_key += '%s=%s' % (key, value)

        try:
            result = cache.get(cache_key)
        except Exception:
            result = None
        if result is None:
            query = ga.get(ids='ga:' + profile, **params)
            result = query.execute()
            cache_duration = self.request.get('cache_duration')
            if cache_duration:
                cache.set(cache_key, result, int(cache_duration))
        return result

    def get_ga_profile(self, service):
        cache_key = '%s-ga-profile' % '-'.join(api.portal.get().getPhysicalPath()[1:])
        try:
            profile = cache.get(cache_key)
        except Exception:
            profile = None
        if profile is None:
            profile = analytics.get_ga_profile(service)
            cache.set(cache_key, profile, 60 * 60 * 1)
        return profile

    def get_paths(self):
        site_path = '/'.join(api.portal.get().getPhysicalPath())
        context_path = '/'.join(self.context.getPhysicalPath())
        base_path = context_path[len(site_path):]
        paths = [base_path, base_path + '/view']

        context_state = getMultiAdapter((self.context, self.request),
                                        name='plone_context_state')
        if context_state.is_portal_root():
            paths.append('/')
            paths.append('/main-page')
        return list(set(paths))
