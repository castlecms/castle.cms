from lxml.html import tostring
from lxml.html import fromstring
from castle.cms.archival import BaseArchivalTransformer


class ExampleArchivalTransformer(BaseArchivalTransformer):

    def __call__(self, html):
        dom = fromstring(html)
        dom.cssselect('.foo')[0].text = 'bar'
        return tostring(dom)
