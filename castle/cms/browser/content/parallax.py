from plone.dexterity.browser import edit
from Products.Five import BrowserView


class ParallaxEditForm(edit.DefaultEditForm):
    pass


ParallaxEditView = ParallaxEditForm
