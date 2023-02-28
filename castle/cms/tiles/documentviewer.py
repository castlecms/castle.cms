from plone import api
from plone.autoform import directives as form
from plone.supermodel import model
from plone.tiles.interfaces import IPersistentTile
from zope import schema
from zope.component import getMultiAdapter
from zope.interface import implementer

from castle.cms.tiles.base import BaseTile
from castle.cms.widgets import RelatedItemFieldWidget


@implementer(IPersistentTile)
class DocumentViewerTile(BaseTile):

    def __call__(self):
        if self.data.get('documentUID') is None:
            return ''

        doc = api.content.get(UID=self.data['documentUID'])
        if doc:
            viewer = getMultiAdapter((doc, self.request), name="docviewertile")
            return viewer()
        return '<html><body><pCould not find file</p></body></html>'


class IDocumentViewerTileSchema(model.Schema):
    form.widget(documentUID=RelatedItemFieldWidget)
    documentUID = schema.List(
        title=u'Document',
        description=u'The file to display in the document viewer',
        required=True
    )
