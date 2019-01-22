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
        feed = FolderFeed(site)
        item = queryMultiAdapter((self.context, feed), IFeedItem, default=None)
        if item is None:
            item = DexterityItem(self.context, feed)

        if item.has_image:
            for tag in tags[:]:
                if ('image' in tag.get('property', '') or
                        'image' in tag.get('itemprop', '') or
                        'image' in tag.get('name', '')):
                    tags.remove(tag)
                elif tag.get('name') == 'twitter:card':
                    # change to large summary
                    tag['content'] = 'summary_large_image'

            tags.extend([
                dict(property="og:image", content=item.image_url),
                dict(itemprop="image", content=item.image_url),
                dict(property="og:image:type", content=item.image_type),
                dict(name="twitter:image", content=item.image_url)
            ])

        if item.has_enclosure and item.file_length > 0:
            if item.file_type.startswith('audio'):
                tags.extend([
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
                tags.extend([
                    dict(name="twitter:card", content="player"),
                    dict(name="twitter:player:width", content="480"),
                    dict(name="twitter:player:height", content="225"),
                    dict(name="twitter:player", content='{}/@@videoplayer'.format(
                        self.get_https_url())),
                    dict(name="twitter:player:stream", content='{}/@@download'.format(
                        self.get_https_url())),
                    dict(name="twitter:player:stream:content_type", content=item.file_type)
                ])

        return tags

    def get_https_url(self):
        # Twitter Player Cards require HTTPS resource URLs
        url = self.context.absolute_url()
        return url.replace('http:', 'https:')
