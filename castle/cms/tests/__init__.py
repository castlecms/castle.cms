import warnings

from castle.cms.archival import BaseArchivalTransformer
from lxml.html import fromstring
from lxml.html import tostring


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)


class ExampleArchivalTransformer(BaseArchivalTransformer):

    def __call__(self, html):
        dom = fromstring(html)
        dom.cssselect('.foo')[0].text = 'bar'
        return tostring(dom)
