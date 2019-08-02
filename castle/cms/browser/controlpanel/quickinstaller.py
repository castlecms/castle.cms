from Products.CMFPlone.controlpanel.browser import quickinstaller
from Products.CMFCore.utils import getToolByName
import Products.CMFPlone
import logging
from Products.CMFPlone import PloneMessageFactory as _
from Products.statusmessages.interfaces import IStatusMessage
from plone.memoize import view


class ManageProductsView(quickinstaller.ManageProductsView):
    upgradable_only = (
        'castle.cms',
        'castle.theme',
        'plone.app.standardtiles',
        'plone.app.tiles',
        'plone.app.mosaic',
        'collective.documentviewer',
        'collective.elasticsearch',
        'Products.CMFPlone'
    )

    @view.memoize
    def marshall_addons(self):
        addons = super(ManageProductsView, self).marshall_addons()
        for product_id in ('castle.cms', 'castle.theme', 'plone.app.mosaic'):
            profile_id = '{}:default'.format(product_id)
            profile_version = str(self.ps.getVersionForProfile(profile_id))
            installed_profile_version = str('.'.join(self.ps.getLastVersionForProfile(profile_id)))
            addons[product_id]['upgrade_info'] = dict(
                required=profile_version != installed_profile_version,
                available=len(self.ps.listUpgrades(profile_id)) > 0,
                hasProfile=True,
                installedVersion=installed_profile_version,
                newVersion=profile_version,
            )
        return addons

    def get_installed(self):
        return [p for p in self.get_addons(apply_filter='installed').values()
                if p['id'] not in self.upgradable_only]

    def get_available(self):
        return [p for p in self.get_addons(apply_filter='available').values()
                if p['id'] not in self.upgradable_only]

    def upgrade_product(self, product):
        '''
        Also upgrade profiles
        '''
        # XXX remove customization in future versions!!!
        if not Products.CMFPlone.__version__.startswith('5.0'):
            raise Exception('Incompatible upgrade mechanisms')
        if super(ManageProductsView, self).upgrade_product(product):
            messages = IStatusMessage(self.request)
            try:
                profile_id = '{}:default'.format(product)
                steps_to_run = self.ps.listUpgrades(profile_id)
                if steps_to_run:
                    self.ps.upgradeProfile(profile_id)
                return True
            except Exception as ex:
                logging.error("Could not upgrade %s: %s" % (product, ex))
                messages.addStatusMessage(
                    _(u'Error upgrading ${product}.', mapping={'product': product}), type="error")
                return False
        else:
            return False


class UpgradeProductsView(quickinstaller.UpgradeProductsView):

    def __call__(self):
        qi = ManageProductsView(self.context, self.request)
        products = self.request.get('prefs_reinstallProducts', None)
        if products:
            for product in products:
                qi.upgrade_product(product)

        purl = getToolByName(self.context, 'portal_url')()
        self.request.response.redirect(purl + '/prefs_install_products_form')
