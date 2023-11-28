from plone.app.registry.browser import controlpanel
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from castle.cms import cache
from castle.cms.constants import CRAWLED_DATA_KEY
from castle.cms.indexing import hps
from castle.cms.indexing import crawler
from castle.cms.interfaces import ICrawlerConfiguration


class CrawlerControlPanelForm(controlpanel.RegistryEditForm):
    schema_prefix = 'castle'
    schema = ICrawlerConfiguration
    id = "CrawlerControlPanel"
    label = u"Site Crawler Configuration"
    description = "Configure CastleCMS to crawl other sites and include " \
                  "those results in your site search. WildcardHPS must " \
                  "be enabled."


class CrawlerControlPanel(controlpanel.ControlPanelFormWrapper):
    form = CrawlerControlPanelForm
    index = ViewPageTemplateFile('templates/crawler.pt')

    def get_crawl_data(self):
        try:
            data = cache.get_client(CRAWLED_DATA_KEY)
        except Exception:
            return {}

        return data

    def get_index_summary(self):
        idx = crawler.index_name(hps.get_index_name())
        terms = dict(field="domain")
        result = hps.get_index_summary(idx, terms)
        return result
