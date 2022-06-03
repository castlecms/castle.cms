from castle.cms.constants import CRAWLED_DATA_KEY
from castle.cms.interfaces import ICrawlerConfiguration
from wildcard.hps.opensearch import WildcardHPSCatalog
from castle.cms.indexing import hps
from opensearchpy import TransportError
from plone import api
from plone.app.registry.browser import controlpanel
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.annotation.interfaces import IAnnotations


class CrawlerControlPanelForm(controlpanel.RegistryEditForm):
    schema_prefix = 'castle'
    schema = ICrawlerConfiguration
    id = "CrawlerControlPanel"
    label = u"Site Crawler Configuration"
    description = "Configure Elastic search to crawl other sites and include those results in your site search. Elastic search must be enabled."  # noqa


class CrawlerControlPanel(controlpanel.ControlPanelFormWrapper):
    form = CrawlerControlPanelForm
    index = ViewPageTemplateFile('templates/crawler.pt')

    def get_crawl_data(self):
        annotations = IAnnotations(self.context)
        if CRAWLED_DATA_KEY not in annotations:
            return {
                'tracking': {}
            }
        return annotations[CRAWLED_DATA_KEY]

    def get_index_summary(self):
        hpscatalog = hps.get_connection()
        idx = '{}_crawler'.format(hpscatalog.index_name)
        terms = dict(field="domain")
        result = hps.get_index_summary(idx, terms)
        return result
