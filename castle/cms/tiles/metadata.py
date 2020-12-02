import json

from castle.cms.behaviors.location import ILocation
from castle.cms.behaviors.search import ISearch
from castle.cms.interfaces import ILDData
from castle.cms.utils import is_backend
from castle.cms.utils import site_has_icon
from plone.app.layout.globals.interfaces import IViewView
from plone.tiles import Tile
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.defaultpage import get_default_page
from Products.CMFPlone.log import logger
from unidecode import unidecode
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zope.viewlet.interfaces import IViewlet
from zope.viewlet.interfaces import IViewletManager
from castle.cms.constants import CASTLE_VERSION_STRING


head_viewlets = {
    'plone.htmlhead.title': 'plone.htmlhead',
    'plone.links.author': 'plone.htmlhead.links',
    'plone.links.RSS': 'plone.htmlhead.links',
    'plone.htmlhead.dublincore': 'plone.htmlhead',
    'plone.htmlhead.socialtags': 'plone.htmlhead'
}


def _date(obj, date):
    try:
        return getattr(obj, date)().ISO8601()
    except Exception:
        return ''


class MetaDataTile(Tile):

    def get_navigation_links(self):
        return u"""
<link rel="home"
      title="Front page"
      href="{url}"/>
<link rel="contents"
      href="{url}/sitemap"/>""".format(url=self.root_url)

    def get_icons(self):
        if not site_has_icon():
            return ''
        return '''
<link rel="apple-touch-icon" sizes="180x180" href="{url}/site-icon.png">
<link rel="icon" type="image/png" href="{url}/site-icon.png?scale=32" sizes="32x32">
<link rel="icon" type="image/png" href="{url}/site-icon.png?scale=16" sizes="16x16">
<link rel="manifest" href="{url}/manifest.json">
<meta name="theme-color" content="#ffffff">'''.format(url=self.root_url)

    def _wrap_ld(self, data):
        return '<script type="application/ld+json">' + json.dumps(data) + '</script>'

    def _get_robot_config(self, search):
        if(is_backend(self.request)):
            return search.backend_robot_configuration or []
        return search.robot_configuration or []

    def get_ld_data(self):
        result = ''
        ld = ILDData(self.context, None)
        if ld is None:
            return ''
        result += self._wrap_ld(ld.get_data())

        if ISiteRoot.providedBy(self.context):
            try:
                page = self.context[get_default_page(self.context)]
                result += self._wrap_ld(ILDData(page).get_data())
            except AttributeError:
                pass

        return result

    def get_basic_tags(self):
        try:
            context = self.context
            if ISiteRoot.providedBy(context):
                try:
                    context = context[get_default_page(context)]
                except AttributeError:
                    pass
            tags = {
                'modificationDate': _date(context, 'modified'),
                'publicationDate': _date(context, 'effective'),
                'expirationDate': _date(context, 'expires'),
                'generator': CASTLE_VERSION_STRING,
                "distribution": "Global",
            }
            ldata = ILocation(context, None)
            if ldata is not None:
                if ldata.locations:
                    location = ldata.locations
                    if type(location) in (list, tuple, set):
                        location = location[0]
                    tags['location'] = location

            search = ISearch(context, None)
            if search is not None:
                robot_configuration = self._get_robot_config(search)
                config = robot_configuration[:]
                if 'index' not in config:
                    config.append('noindex')
                if 'follow' not in config:
                    config.append('nofollow')
                tags['robots'] = ','.join(config)

            return ''.join([u'<meta name="{}" content="{}">'.format(name, value)
                            for name, value in tags.items()])
        except Exception:
            return u''

    def get_search_link(self):
        return '''
<link rel="search"
      title="Search this site"
      href="{url}/@@search" />'''.format(
            url=self.root_url
          )

    def get_printcss_link(self):
        template = ''' <link rel="stylesheet" href="{url}/++plone++castle/less/public/print.css" type="text/css" media="print">'''  # noqa:E501
        return template.format(url=self.root_url)

    def get_canonical_url(self):
        context_state = getMultiAdapter(
            (self.context, self.request), name=u'plone_context_state')
        canonical_object = context_state.canonical_object()
        if self.context != canonical_object:
            can_state = getMultiAdapter(
                (canonical_object, self.request), name=u'plone_context_state')
            url = can_state.view_url()
        else:
            url = context_state.view_url()
        return u'    <link rel="canonical" href="%s" />' % url

    def __call__(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                       name=u'plone_portal_state')
        self.root_url = portal_state.navigation_root_url()

        result = self.get_canonical_url()
        alsoProvides(self, IViewView)
        for name, manager_name in head_viewlets.items():
            manager = queryMultiAdapter(
                (self.context, self.request, self),
                IViewletManager, name=manager_name
            )
            viewlet = queryMultiAdapter(
                (self.context, self.request, self, manager),
                IViewlet, name=name
            )
            if viewlet is not None:
                try:
                    viewlet.update()
                    result += viewlet.render()
                except Exception:
                    logger.warn('Error rendering head viewlet %s' % name, exc_info=True)
        result += unidecode(self.get_basic_tags())
        result += unidecode(self.get_navigation_links())
        result += unidecode(self.get_ld_data())
        result += unidecode(self.get_icons())
        result += unidecode(self.get_search_link())
        result += unidecode(self.get_printcss_link())
        return u'<html><head>%s</head></html>' % result
