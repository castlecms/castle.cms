from plone import api
from plone.memoize.view import memoize
from castle.cms.browser.syndication import FolderFeed
from plone.app.layout.viewlets.social import SocialTagsViewlet as BaseSocialTagsViewlet
from zope.component.hooks import getSite
from Products.CMFPlone.interfaces.syndication import IFeedItem
from zope.component import queryMultiAdapter
from castle.cms.syndication import DexterityItem


class SocialTagsViewlet(BaseSocialTagsViewlet):
    @memoize
    def _get_tags(self):
        tags = super(SocialTagsViewlet, self)._get_tags()
        site = getSite()
        site_title = api.portal.get_registry_record('plone.site_title', default=None)
        feed = FolderFeed(site)
        item = queryMultiAdapter((self.context, feed), IFeedItem, default=None)
        if item is None:
            item = DexterityItem(self.context, feed)
        finaltags = []
        for tag in tags:
            if site_title and (tag.get('property', '') == 'og:title' or
                                    tag.get('name', '') == 'twitter:title'):
                tag['content'] = u'{} | {}'.format(tag['content'], site_title)
            if item.has_image:
                if tag.get('name', '') == 'twitter:card':
                    # change to large summary
                    tag['content'] = 'summary_large_image'
                if ('image' in tag.get('property', '') or
                        'image' in tag.get('itemprop', '') or
                        'image' in tag.get('name', '')):
                    continue
                finaltags.append(tag)
        if item.has_image:
            finaltags.extend([
                dict(property="og:image", content=item.image_url),
                dict(itemprop="image", content=item.image_url),
                dict(property="og:image:type", content=item.image_type),
                dict(name="twitter:image", content=item.image_url)
            ])
        if item.has_enclosure and item.file_length > 0:
            if item.file_type.startswith('audio'):
                finaltags.extend([
                    dict(name="twitter:card", content="player"),
                    dict(name="twitter:player:width", content="480"),
                    dict(name="twitter:player:height", content="55"),
                    dict(name="twitter:player", content='{}/@@audioplayer'.format(
                        self.get_https_url())),
                    dict(name="twitter:player:stream", content='{}/@@download'.format(
                        self.get_https_url())),
                    dict(name="twitter:player:stream:content_type", content=item.file_type)
                ])
            elif item.file_type.startswith('video'):
                finaltags.extend([
                    dict(name="twitter:card", content="player"),
                    dict(name="twitter:player:width", content="480"),
                    dict(name="twitter:player:height", content="225"),
                    dict(name="twitter:player", content='{}/@@videoplayer'.format(
                        self.get_https_url())),
                    dict(name="twitter:player:stream", content='{}/@@download'.format(
                        self.get_https_url())),
                    dict(name="twitter:player:stream:content_type", content=item.file_type)
                ])

        return finaltags

    def get_https_url(self):
        # Twitter Player Cards require HTTPS resource URLs
        url = self.context.absolute_url()
        return url.replace('http:', 'https:')
