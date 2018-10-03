import json

from Acquisition import aq_base
from castle.cms.browser.utils import Utils
from castle.cms.interfaces import IAudio, ILDData, IVideo
from plone import api
from plone.dexterity.interfaces import IDexterityContent
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.browser.syndication.adapters import (DexterityItem,
                                                            FolderFeed)
from Products.CMFPlone.interfaces import ISiteSchema
from Products.CMFPlone.interfaces.syndication import IFeedItem
from Products.CMFPlone.utils import getSiteLogo
from ZODB.POSException import POSKeyError
from zope.component import adapts, getUtility, queryMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import implements


def format_date(dt):
    try:
        return dt.ISO8601()
    except Exception:
        return ''


class NoFileDexterityItem(DexterityItem):

    def __init__(self, context, feed):
        super(DexterityItem, self).__init__(context, feed)
        self.dexterity = IDexterityContent.providedBy(context)
        self.file = None


class LDData(object):
    implements(ILDData)
    adapts(IDexterityContent)

    type_ = 'WebPage'

    view_type = False

    def __init__(self, context):
        self.site = api.portal.get()
        feed = FolderFeed(self.site)
        self.item = None
        try:
            self.item = queryMultiAdapter((context, feed), IFeedItem)
        except POSKeyError:
            pass
        if self.item is None:
            self.item = NoFileDexterityItem(context, feed)
        self.context = context
        self.registry = getUtility(IRegistry)

    def get_data(self):
        data = {
            "@context": "http://schema.org",
            "@type": self.type_,
            "name": self.item.title,
            "headline": self.item.title,
            "url": self.item.link,
            "description": self.item.description,
            "datePublished": format_date(self.item.published),
            "dateModified": format_date(self.item.modified),
        }

        if getattr(aq_base(self.context), 'image', None) is not None:
            data['image'] = {
                "@type": "ImageObject",
                "url": "%s/@@images/image" % self.item.base_url,
            }
            data['thumbnailUrl'] = "%s/@@images/image/mini" % self.item.base_url  # noqa

        registry = getUtility(IRegistry)
        view_about = registry.get('plone.allow_anon_views_about', False)
        if view_about:
            try:
                author = self.context.creators[0]
                data['author'] = {
                    "@type": "Person",
                    "name": author
                }
            except Exception:
                pass
        return data


class LDAudioData(LDData):
    adapts(IAudio)

    _type = 'AudioObject'

    def get_data(self):
        data = super(LDAudioData, self).get_data()
        data['contentUrl'] = self.item.base_url
        try:
            data['caption'] = self.context.transcript.output
        except Exception:
            pass
        return data


class LDVideoData(LDAudioData):
    adapts(IVideo)

    _type = 'VideoObject'


class LDSiteData(object):
    implements(ILDData)
    adapts(ISiteRoot)

    def __init__(self, context):
        self.context = context

    def get_data(self):
        registry = getUtility(IRegistry)
        btype = registry.get('castle.business_type', None)
        bname = registry.get('castle.business_name', None)
        utils = Utils(self.context, getRequest())

        if not btype and bname:
            # return subset that uses site name, org type
            registry = getUtility(IRegistry)
            site_settings = registry.forInterface(ISiteSchema,
                                                  prefix="plone",
                                                  check=False)
            return {
                "@context": "http://schema.org",
                "@type": 'Organization',
                "name": site_settings.site_title,
                "url": utils.get_public_url(),
                "logo": {
                    "@type": "ImageObject",
                    "url": getSiteLogo()
                }
            }

        data = {
            "@context": "http://schema.org",
            "@type": btype,
            "name": bname,
            "url": utils.get_public_url(),
            'telephone': registry.get('castle.business_telephone', ''),
            "logo": {
                "@type": "ImageObject",
                "url": getSiteLogo()
            }
        }
        address = registry.get('castle.business_address', None)
        if address:
            data['address'] = {
                '@type': 'PostalAddress',
                'streetAddress': address,
                'addressLocality': registry.get('castle.business_city', ''),
                'addressRegion': registry.get('castle.business_state', ''),
                'postalCode': registry.get('castle.business_postal_code', ''),
                'addressCountry': registry.get('castle.business_country', '')
            }
        coordinates = registry.get('castle.business_coordinates', '')
        if coordinates:
            try:
                coordinates = json.loads(coordinates)
            except Exception:
                coordinates = None
            if coordinates:
                data['geo'] = {
                    '@type': 'GeoCoordinates',
                    'latitude': coordinates.get('lat', ''),
                    'longitude': coordinates.get('lng', '')
                }
        days = registry.get('castle.business_days_of_week', [])
        hours = []
        if days:
            hours.append({
                '@type': "OpeningHoursSpecification",
                'dayOfWeek': days,
                'opens': registry.get('castle.business_opens', ''),
                'closes': registry.get('castle.business_closes', ''),
            })
        for special in registry.get('castle.business_special_hours', []) or []:
            if special.count('|') != 2:
                continue
            day, opens, closes = special.split('|')
            hours.append({
                '@type': "OpeningHoursSpecification",
                'dayOfWeek': day,
                'opens': opens,
                'closes': closes
            })
        if hours:
            data['openingHoursSpecification'] = hours
        menu = registry.get('castle.business_menu_link', None)
        if menu:
            data["menu"] = menu
        if registry.get('castle.business_accepts_reservations', False):
            data["acceptsReservations"] = "True"

        try:
            data.update(json.loads(
                registry.get(
                    'castle.business_additional_configuration', '{}')))
        except Exception:
            pass
        return data
