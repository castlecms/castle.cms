from castle.cms import social
from castle.cms.tiles.base import BaseTile
from plone.autoform import directives as form
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.interface import Interface
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class SharingTile(BaseTile):

    def render(self):
        return self.index()

    @property
    def buttons(self):
        return self.data.get('buttons',
                             ['twitter', 'facebook', 'email', 'print', 'share'])

    def get_counts(self):
        return social.get_stats(self.context)


class ISharingTileSchema(Interface):

    form.widget('buttons', CheckBoxFieldWidget)
    buttons = schema.List(
        title=u'Buttons',
        description=u'Types of share buttons',
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary([
                SimpleTerm('twitter', 'twitter', 'Twitter'),
                SimpleTerm('facebook', 'facebook', 'Facebook'),
                SimpleTerm('email', 'email', 'Email'),
                SimpleTerm('print', 'print', 'Print'),
                SimpleTerm('share', 'share', 'Share')
            ])
        ),
        default=['twitter', 'facebook', 'email', 'print', 'share']
    )
