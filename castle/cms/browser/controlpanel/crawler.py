from castle.cms.constants import CRAWLED_DATA_KEY
from castle.cms.constants import CRAWLED_SITE_ES_DOC_TYPE
from castle.cms.interfaces import ICrawlerConfiguration
from collective.elasticsearch.es import ElasticSearchCatalog
from elasticsearch import TransportError
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
        query = {
            "size": 0,
            "aggregations": {
                "totals": {
                    "terms": {
                        "field": "domain"
                    }
                }
            }
        }
        portal_catalog = api.portal.get_tool('portal_catalog')
        try:
            es = ElasticSearchCatalog(portal_catalog)
            result = es.connection.search(
                index=es.index_name,
                doc_type=CRAWLED_SITE_ES_DOC_TYPE,
                body=query)
        except TransportError:
            return []

        data = result['aggregations']['totals']['buckets']
        return data
