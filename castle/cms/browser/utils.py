from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_parent
from castle.cms import cache
from castle.cms import utils
from castle.cms.behaviors.location import ILocation
from castle.cms.browser.nextprev import NextPrevious
from castle.cms.browser.security.login import SecureLoginView
from castle.cms.interfaces import IUtils
from castle.cms.vocabularies import LocationsVocabulary
from DateTime import DateTime
from datetime import datetime
from lxml import etree
from lxml.html import tostring
from plone import api
from plone.app.imaging.utils import getAllowedSizes
from plone.app.layout.globals.interfaces import IViewView
from plone.app.layout.navigation.defaultpage import getDefaultPage
from plone.app.layout.viewlets.common import GlobalSectionsViewlet
from plone.app.uuid.utils import uuidToObject
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.resources import add_resource_on_request
from Products.CMFPlone.utils import getSiteLogo
from Products.Five import BrowserView
from Products.ZCatalog.interfaces import ICatalogBrain
from unidecode import unidecode
from urlparse import parse_qs
from urlparse import urlparse
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zope.interface import implements
from zope.viewlet.interfaces import IViewlet
from zope.viewlet.interfaces import IViewletManager

import json


def _one(val):
    if type(val) in (list, tuple, set) and len(val) > 0:
        return val[0]


def _clean_youtube_id(val):
    return val.split('&')[0]


class Utils(BrowserView):
    implements(IUtils)

    def __init__(self, context, request):
        super(Utils, self).__init__(context, request)
        self.secure_login_view = SecureLoginView(context, request)

    @property
    @memoize
    def registry(self):
        return getUtility(IRegistry)

    @property
    @memoize
    def site(self):
        return api.portal.get()

    @property
    @memoize
    def image_size(self):
        return getAllowedSizes()

    @property
    def types_use_view_action(self):
        return frozenset(
            self.registry.get('plone.types_use_view_action_in_listings', []))

    def get_object_url(self, obj):
        if obj is None:
            return
        try:
            url = obj.getURL()
        except AttributeError:
            url = obj.absolute_url()
        if obj.portal_type in self.types_use_view_action:
            url += '/view'
        return url

    def get_object(self, val):
        if ICatalogBrain.providedBy(val):
            return val.getObject()
        if not val:
            return None
        if isinstance(val, list) and len(val) > 0:
            # if it's a list let's try to use the first value
            val = val[0]
        if isinstance(val, basestring):
            if val[0] == '/':
                # it's a path
                return self.site.restrictedTraverse(val.strip('/'), None)
            else:
                # try querying catalog
                obj = uuidToObject(val)
                if obj:
                    return obj
        if isinstance(val, basestring):
            return None
        return val

    def has_image(self, obj):
        return utils.has_image(obj)

    def get_path(self, obj):
        return utils.get_path(obj)

    def get_backend_url(self):
        return utils.get_backend_url()

    def get_backend_url_no_trailing_slash(self):
        _be_url = self.get_backend_url()
        return _be_url[:-1 if _be_url[-1] == '/' else None]

    def valid_date(self, date):
        if not date:
            return False
        if isinstance(date, basestring):
            date = DateTime(date)
        if date.year() == 1969:
            return False
        return True

    def iso_date(self, date):
        if not date:
            return ''
        if isinstance(date, basestring):
            date = DateTime(date)
        return date.ISO8601()

    def format_date(self, date, format='common', formatter=None):
        if not date:
            return ''
        if isinstance(date, basestring):
            date = DateTime(date)
        if isinstance(date, datetime):
            date = DateTime(date)

        if formatter is not None:
            try:
                return date.strftime(formatter)
            except Exception:
                pass

        if format == 'common':
            return date.fCommon()
        if format in ('dot', 'dotshort'):
            return '%s.%s.%s' % (
                str(date.year()),
                str(date.month()).zfill(2),
                str(date.day()).zfill(2))
        if format == 'usdot':
            return '%s.%s.%s' % (
                str(date.month()).zfill(2),
                str(date.day()).zfill(2),
                str(date.year()),)
        if format == 'notime':
            return ' '.join(date.fCommon().split(' ')[:-2])
        if format == 'nodate':
            return ' '.join(date.fCommon().split(' ')[-2:])
        if format == 'slash':
            return '%s/%s/%s' % (
                str(date.year()),
                str(date.month()).zfill(2),
                str(date.day()).zfill(2))
        if format == 'usslash':
            return '%s/%s/%s' % (
                str(date.month()).zfill(2),
                str(date.day()).zfill(2),
                str(date.year()),)

    def get_locations(self, obj):
        bdata = ILocation(obj, None)
        result = []
        if bdata and bdata.locations:
            vocab = LocationsVocabulary(self.context)
            for loc in bdata.locations:
                term = vocab.by_token.get(loc)
                if term:
                    result.append(term.title)
                else:
                    result.append(loc)
        return result

    def get_location(self, obj):
        try:
            location = obj.location
            if location:
                return location
        except AttributeError:
            pass

        if ICatalogBrain.providedBy(obj):
            obj = obj.getObject()

        bdata = ILocation(obj, None)
        if bdata and bdata.locations:
            vocab = LocationsVocabulary(self.context)
            term = vocab.by_token.get(bdata.locations[0])
            if term:
                return term.title
            else:
                return bdata.locations[0]

    def clean_youtube_url(self, url):
        parsed = urlparse(url)
        if parsed.query:
            query = parse_qs(parsed.query)
            if 'v' in query:
                return 'https://www.youtube-nocookie.com/embed/%s' % _one(query['v'])
        if '/embed/' in url:
            _id = _clean_youtube_id(url.partition('/embed/')[-1])
            return 'https://www.youtube-nocookie.com/embed/%s' % _id
        if 'youtu.be' in url:
            _id = _clean_youtube_id(url.partition('https://youtu.be/')[-1])
            return 'https://www.youtube-nocookie.com/embed/%s' % _id
        if 'youtube' in url and '/v/' in url:
            _id = _clean_youtube_id(url.partition('/v/')[-1])
            return 'https://www.youtube-nocookie.com/embed/%s' % _id
        return url

    def get_youtube_url(self, obj):
        if isinstance(obj, basestring):
            url = obj
        else:
            try:
                url = obj.youtube_url
            except AttributeError:
                return

        if url is None:
            return

        return self.clean_youtube_url(url)

    def get_external_youtube_url(self, obj):
        if isinstance(obj, basestring):
            url = obj
        else:
            try:
                url = obj.youtube_url
            except AttributeError:
                return

        return url

    def get_uid(self, obj):
        return IUUID(obj, None)

    def get_scale_url(self, content, scale='large'):
        return '%s/@@images/image/%s' % (content.absolute_url(), scale)

    def get_main_links(self):
        viewlet = GlobalSectionsViewlet(self.context, self.request, None)
        viewlet.update()
        selected_tab = viewlet.selected_portal_tab

        site = api.portal.get()
        site_default_page = getDefaultPage(site)
        if selected_tab == site_default_page:
            selected_tab = 'index_html'

        default_page_url = '{}/{}'.format(site.absolute_url(), site_default_page)
        tabs = []
        for tab in viewlet.portal_tabs:
            if tab['url'] == default_page_url:
                continue
            tabs.append(tab)

        return {
            'selected_portal_tab': selected_tab,
            'portal_tabs': tabs
        }

    def get_actions(self, name):
        context_state = getMultiAdapter((self.context, self.request),
                                        name=u'plone_context_state')
        return context_state.actions(name)

    def get_folder_section(self):
        section = self.context
        while True:
            parent = aq_parent(section)
            if IPloneSiteRoot.providedBy(parent) or parent is None:
                break
            section = parent
        sm = getSecurityManager()
        if not sm.checkPermission('View', section):
            return
        return section

    def get_public_url(self):
        return utils.get_public_url()

    def render_breadcrumbs(self):
        alsoProvides(self, IViewView)
        manager = queryMultiAdapter(
            (self.context, self.request, self),
            IViewletManager, name='plone.abovecontent'
        )
        viewlet = queryMultiAdapter(
            (self.context, self.request, self, manager),
            IViewlet, name='plone.path_bar'
        )
        if viewlet is not None:
            viewlet.update()
            return viewlet.render()
        else:
            return ''

    def search(self, **kwargs):
        catalog = api.portal.get_tool('portal_catalog')
        return catalog(**kwargs)

    def is_anonymous(self):
        return api.user.is_anonymous()

    def truncate_text(self, *args, **kwargs):
        return utils.truncate_text(*args, **kwargs)

    def get_popular_tags(self, limit=20):
        cache_key = '-'.join(self.site.getPhysicalPath()[1:]) + '-popular-tags-' + str(limit)

        try:
            result = cache.get(cache_key)
        except Exception:
            result = None
        if result is not None:
            return result

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

        sorted_tags = list(reversed(sorted(tags, key=lambda tag: tag['count'])))[:limit]

        cache.set(cache_key, sorted_tags, 60 * 5)
        return sorted_tags

    def focal_image_tag(self, brain, scale=None, className='', imageClassName='',
                        attributes=None, focal=None):
        # read https://github.com/jonom/jquery-focuspoint on how to calc
        image_info = utils.get_image_info(brain)

        attrib = {}
        if attributes is not None:
            attrib.update(attributes)

        if 'src' not in attrib:
            try:
                url = brain.getURL()
                alt = brain.Title
            except Exception:
                url = brain.absolute_url()
                alt = brain.Title()
            if not isinstance(alt, basestring):
                alt = ''
            attrib.update({
                'src': '{0}/@@images/image/{1}'.format(url, scale or ''),
                'alt': unidecode(alt),
                'class': imageClassName
            })

        el = etree.Element('div')
        el.attrib['class'] = 'focuspoint' if not className else 'focuspoint ' + className
        imEl = etree.Element('img')
        imEl.attrib.update(attrib)
        el.append(imEl)

        if not focal and image_info and 'focal_point' in image_info:
            focal = image_info['focal_point']

        if image_info and focal:
            width = image_info['width']
            height = image_info['height']
            focal_x = ((float(focal[0]) - (float(width) / 2)) / float(width)) * 2
            focal_y = -((float(focal[1]) - (float(height) / 2)) / float(height)) * 2

            sizes_info = {}
            for scale_name, scale_data in self.image_size.items():
                scale_ratio = float(scale_data[0]) / float(width)
                sizes_info[scale_name] = {
                    'w': int(float(width) * float(scale_ratio)),
                    'h': int(float(height) * float(scale_ratio))
                }

            el.attrib.update({
                'data-focus-x': str(focal_x),
                'data-focus-y': str(focal_y),
                'data-base-url': '{0}/@@images/image/'.format(url),
                'data-scale': scale,
                'data-w': str(width),
                'data-h': str(height),
                'data-scales-info': json.dumps(sizes_info)
            })

        return tostring(el)

    def focal_cover_image_tag(self, brain, scale=None, class_name='',
                              attributes=None, focal=None):
        # read https://github.com/jonom/jquery-focuspoint on how to calc
        image_info = utils.get_image_info(brain)

        attrib = {}

        if 'src' not in attrib:
            try:
                url = brain.getURL()
                alt = brain.Title
            except Exception:
                url = brain.absolute_url()
                alt = brain.Title()
            if not isinstance(alt, basestring):
                alt = ''
            attrib.update({
                'src': '{0}/@@images/image'.format(url),
                'alt': unidecode(alt),
                'class': 'pat-focuspoint-cover'
            })

        div_element = etree.Element('div')
        if class_name:
            div_element.attrib['class'] = class_name
        imEl = etree.Element('img')
        imEl.attrib.update(attrib)
        div_element.append(imEl)

        if not focal and image_info and 'focal_point' in image_info:
            focal = image_info['focal_point']

        if image_info and focal:
            width = image_info['width']
            height = image_info['height']
            focal_x = ((float(focal[0]) - (float(width) / 2)) / float(width)) * 2
            focal_y = -((float(focal[1]) - (float(height) / 2)) / float(height)) * 2

            sizes_info = {}
            for scale_name, scale_data in self.image_size.items():
                scale_ratio = float(scale_data[0]) / float(width)
                sizes_info[scale_name] = {
                    'w': int(float(width) * float(scale_ratio)),
                    'h': int(float(height) * float(scale_ratio))
                }

            div_element.attrib.update({
                'data-focus-x': str(focal_x),
                'data-focus-y': str(focal_y),
                'data-base-url': '{0}/@@images/image/'.format(url),
                'data-scale': scale,
                'data-w': str(width),
                'data-h': str(height),
                'data-scales-info': json.dumps(sizes_info),
            })
        return tostring(div_element)

    def focal_cover_video_tag(self, video_brain, scale=None, class_name='',
                              attributes=None, focal=None, muted=True):
        # read https://github.com/jonom/jquery-focuspoint on how to calc
        image_info = utils.get_image_info(video_brain)
        content_type = video_brain.file.contentType
        video_url = video_brain.absolute_url()
        download_url = '{0}/@@download/file/{1}'.format(video_url, video_brain.file.filename)
        has_image = self.has_image(video_brain)
        attrib = {}
        if attributes is not None:
            attrib.update(attributes)

        div_element = etree.Element('div')
        if class_name:
            div_element.attrib['class'] = class_name

        video_element = etree.Element('video')
        video_element.attrib.update({
            'class': 'pat-focuspoint-cover',
            'preload': 'none',
            'loop': 'true',
            'autoplay': 'true',
            'muted': ''
        })
        if has_image:
            video_element.attrib['poster'] = self.get_scale_url(video_brain, 'large')
        div_element.append(video_element)
        source_element = etree.Element('source')
        source_element.attrib.update({
            'src': download_url,
            'type': content_type,
        })
        video_element.append(source_element)

        if video_brain.subtitle_file:
            # does this work when there are subtitles?
            track_element = etree.Element('track')
            track_element.attrib.update({
                'kind': 'subtitles',
                'src': '{}/@@view/++widget++form.widgets.subtitle_file/@@download'.format(video_url),
                'srclang': 'en',
            })
            video_element.append(track_element)

        if not focal and image_info and 'focal_point' in image_info:
            focal = image_info['focal_point']

        if image_info and focal:
            width = image_info['width']
            height = image_info['height']
            focal_x = ((float(focal[0]) - (float(width) / 2)) / float(width)) * 2
            focal_y = -((float(focal[1]) - (float(height) / 2)) / float(height)) * 2

            sizes_info = {}
            for scale_name, scale_data in self.image_size.items():
                scale_ratio = float(scale_data[0]) / float(width)
                sizes_info[scale_name] = {
                    'w': int(float(width) * float(scale_ratio)),
                    'h': int(float(height) * float(scale_ratio))
                }

            div_element.attrib.update({
                'data-focus-x': str(focal_x),
                'data-focus-y': str(focal_y),
                'data-base-url': '{0}/@@images/image/'.format(video_url),
                'data-scale': scale,
                'data-w': str(width),
                'data-h': str(height),
                'data-scales-info': json.dumps(sizes_info),
            })

        return tostring(div_element)

    @property
    @memoize
    def normalizer(self):
        return getUtility(IIDNormalizer)

    def normalize(self, val):
        return self.normalizer.normalize(val)

    def get_registry_value(self, name, default=None):
        GENERIC_SITE_TITLE = 'CastleCMS'

        if name == 'plone.site_title' and self.secure_login_view.scrub_backend():
            return GENERIC_SITE_TITLE
        else:
            return self.registry.get(name, default)

    def get_logo(self):
        BLANK_IMAGE = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='

        if self.secure_login_view.scrub_backend():
            return BLANK_IMAGE
        else:
            return getSiteLogo()

    def get_next_prev(self, obj):
        try:
            nextprev = NextPrevious(obj)
            return {
                'next': nextprev.getNextItem(obj),
                'prev': nextprev.getPreviousItem(obj)
            }
        except ValueError:
            return {
                'next': None,
                'prev': None
            }

    def get_summary_text(self, obj):
        obj = aq_base(obj)
        try:
            return obj.overview.output
        except Exception:
            try:
                desc = obj.Description
                if callable(desc):
                    desc = desc()
                return desc
            except Exception:
                pass
        return ''

    def add_resource_on_request(self, resource):
        add_resource_on_request(self.request, resource)
