from plone import api
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings


def upgrade(context, logger=None):
    cookWhenChangingSettings(api.portal.get())
