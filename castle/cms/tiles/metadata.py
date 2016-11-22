from castle.cms.behaviors.location import ILocation
from castle.cms.interfaces import ILDData
from castle.cms.utils import site_has_icon
from plone.app.layout.globals.interfaces import IViewView
from plone.app.layout.navigation.defaultpage import getDefaultPage
from plone.tiles import Tile
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.log import logger
from unidecode import unidecode
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zope.viewlet.interfaces import IViewlet
from zope.viewlet.interfaces import IViewletManager

import json


head_viewlets = {
    'plone.htmlhead.title': 'plone.htmlhead',
    'plone.links.author': 'plone.htmlhead.links',
    'plone.links.RSS': 'plone.htmlhead.links',
    'plone.links.canonical_url': 'plone.htmlhead.links',
    'plone.htmlhead.dublincore': 'plone.htmlhead',
    'plone.htmlhead.socialtags': 'plone.htmlhead'
}


def _date(obj, date):
    try:
        return getattr(obj, date)().ISO8601()
    except:
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

    def get_ld_data(self):
        result = ''
        ld = ILDData(self.context, None)
        if ld is None:
            return ''
        result += self._wrap_ld(ld.get_data())

        if ISiteRoot.providedBy(self.context):
            try:
                page = self.context[getDefaultPage(self.context)]
                result += self._wrap_ld(ILDData(page).get_data())
            except AttributeError:
                pass

        return result

    def get_basic_tags(self):
        try:
            context = self.context
            if ISiteRoot.providedBy(context):
                try:
                    context = context[getDefaultPage(context)]
                except AttributeError:
                    pass
            try:
                subject = context.Subject()
            except:
                subject = []

            tags = {
                'description': context.Description(),
                'keywords': ','.join(subject),
                'modificationDate': _date(context, 'modified'),
                'publicationDate': _date(context, 'effective'),
                'expirationDate': _date(context, 'expires'),
                'generator': 'Castle CMS 1.0'
            }
            ldata = ILocation(context, None)
            if ldata is not None:
                if ldata.locations:
                    location = ldata.locations
                    if type(location) in (list, tuple, set):
                        location = location[0]
                    tags['location'] = location

            return ''.join([u'<meta name="{}" content="{}">'.format(name, value)
                            for name, value in tags.items()])
        except:
            return u''

    def get_search_link(self):
        return '''
<link rel="search"
      title="Search this site"
      href="{url}/@@search" />'''.format(
            url=self.root_url
          )

    def __call__(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                       name=u'plone_portal_state')
        self.root_url = portal_state.navigation_root_url()

        result = u''
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
                except:
                    logger.warn('Error rendering head viewlet %s' % name, exc_info=True)
        result += unidecode(self.get_basic_tags())
        result += unidecode(self.get_navigation_links())
        result += unidecode(self.get_ld_data())
        result += unidecode(self.get_icons())
        result += unidecode(self.get_search_link())
        return u'<html><head>%s</head></html>' % result
