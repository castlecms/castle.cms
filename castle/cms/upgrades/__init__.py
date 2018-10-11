from plone import api
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings


PROFILE_ID = 'profile-castle.cms:default'


def cook_js_resources(context, logger=None):
    cookWhenChangingSettings(api.portal.get())
