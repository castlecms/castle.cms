from zope import schema
from zope.interface import Interface
from castle.cms.tiles.base import BaseTile
from castle.cms.vocabularies import AvailableFragments
from castle.cms.fragments.utils import getFragment


class FragmentTile(BaseTile):

    def render(self):
        fragment = self.data.get('fragment', '')
        if fragment:
            fragment = getFragment(
                self.context, self.request, fragment)
            options = {
                'tile': self
            }
            if hasattr(self, 'data_context'):
                options['data_context'] = self.data_context
            return fragment(options=options)
        return ''


class IFragmentTileSchema(Interface):

    fragment = schema.Choice(
        title=u"Fragment",
        source=AvailableFragments,
        required=True,
        default=None
    )
