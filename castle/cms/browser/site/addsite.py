from castle.cms import install
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFPlone.browser.admin import AddPloneSite
from Products.CMFPlone.browser.admin import Overview
from Products.CMFPlone.factory import _DEFAULT_PROFILE
from Products.CMFPlone.factory import addPloneSite
from Products.CMFPlone.resources.browser.combine import combine_bundles
from zope.interface import alsoProvides

try:
    from sites import get_site_container
except ImportError:
    get_site_container = False

import json
import logging
import socket
import transaction


LOGGER = logging.getLogger('Products.CMFPlone')


DYNAMIC_STORAGE_ENABLED = False
if get_site_container is None:
    # requires zope version with this
    DYNAMIC_STORAGE_ENABLED = False


class AddCastleSite(AddPloneSite):

    def buildSite(self, form):
        # CSRF protect. DO NOT use auto CSRF protection for adding a site
        alsoProvides(self.request, IDisableCSRFProtection)
        self.request.response.setHeader('Content-type', 'application/json')

        extension_ids = form.get('extension_ids[]', [])
        extension_ids.append('castle.cms:default')

        # TODO: barceloneta needs to just be removed
        if 'plonetheme.barceloneta:default' in extension_ids:
            extension_ids.remove('plonetheme.barceloneta:default')

        site_id = form.get('site_id', 'Castle')

        try:
            site = addPloneSite(
                self.get_creation_context(site_id),
                site_id,
                title=form.get('title', ''),
                profile_id=form.get('profile_id', _DEFAULT_PROFILE),
                extension_ids=extension_ids,
                setup_content=form.get('setup_content', True),
                default_language=form.get('default_language', 'en'),
                portal_timezone=form.get('portal_timezone', 'UTC')
            )

            # delete news/events since they have default pages attached to them
            api.content.delete(objects=(site['news'], site['events']))
            install.tiles(site, self.request)

            # need to reindex
            catalog = api.portal.get_tool('portal_catalog')
            catalog.manage_catalogRebuild()

            combine_bundles(site)

            if DYNAMIC_STORAGE_ENABLED:
                url = '{}/sites/{}'.format(self.context.absolute_url(), site_id)
            else:
                url = '{}/{}'.format(self.context.absolute_url(), site_id)

            # we do not allow basic auth
            acl_users = site.acl_users
            acl_users.manage_delObjects(['credentials_basic_auth'])

            cookie_auth = acl_users.credentials_cookie_auth
            # this is relative to [site]/acl_users/credentials_basic_auth
            # otherwise, doing /login on a site would redirect to [root]/@@secure-login
            cookie_auth.login_path = u'../../@@secure-login'

            return json.dumps({
                'success': True,
                'url': url
            })

        except Exception as e:
            LOGGER.error('Error creating site', exc_info=True)
            transaction.abort()  # abort creating this site if there was an error
            return json.dumps({'success': False, 'msg': str(e)})

    def get_creation_context(self, site_id):
        if not DYNAMIC_STORAGE_ENABLED:
            return self.context

        site_app = get_site_container(site_id)
        site_app = site_app.__of__(self.context)
        return site_app

    def __call__(self):

        def labeled_map(labelName, valueName, values):
            return {x[labelName]: x[valueName] for x in values}

        form = self.request.form
        submitted = form.get('submitted', False)

        if submitted:
            return self.buildSite(form)

        timezone_data = self.timezones()
        timezones = {x: labeled_map('label', 'value', timezone_data[x]) for x in timezone_data}

        defaultLanguage = self.browser_language()
        language_data = self.grouped_languages(defaultLanguage)
        languages = {x['label']: labeled_map('label', 'langcode', x['languages'])
                     for x in language_data}

        form_data = {}
        form_data['default_language'] = defaultLanguage
        form_data['timezones'] = timezones
        form_data['languages'] = languages
        form_data['action_url'] = self.context.absolute_url() + '/@@plone-addsite'

        profiles = self.profiles()['extensions']
        addons = {}
        for profile in profiles:

            if 'selected' in profile:
                selected = True
            else:
                selected = False

            addons[profile['id']] = {
                'description': profile['description'],
                'title': profile['title'],
                'checked': selected,
                'type': 'checkbox'
            }
        form_data['extensions'] = addons
        self.form_data = json.dumps(form_data)
        return self.index()


class Overview(Overview):

    def from_local_or_IP(self):
        try:
            host = self.request.get_header('host').split(':')[0]
        except AttributeError:
            return False  # no host header
        try:
            socket.inet_aton(host)
            return True
        except Exception:
            if host.lower() == 'localhost':
                return True
        return False

    def __call__(self):
        return self.index()
