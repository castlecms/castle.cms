# -*- coding: utf-8 -*-

from itertools import chain

from Acquisition import aq_inner
from castle.cms.pwexpiry.config import DATETIME_FORMATSTRING
from castle.cms.pwexpiry.events import UserUnlocked
from DateTime import DateTime
from Products.CMFPlone.controlpanel.browser.usergroups import \
    UsersGroupsControlPanelView

from plone.protect import CheckAuthenticator
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import normalizeString
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.event import notify


class PwExpiryControlPanel(UsersGroupsControlPanelView):

    def getWhitelisted(self):
        if self.whitelisted:
            return "\r\n".join(self.whitelisted)

    def __call__(self):

        form = self.request.form
        registry = getUtility(IRegistry)
        self.whitelisted = registry.get('plone.pwexpiry_whitelisted_users')

        submitted = form.get('form.submitted', False)
        whitelist_submitted = form.get('form.whitelist_submitted', False)

        if whitelist_submitted:
            users_to_whitelist = form.get('form.whitelisted_users', "").split('\r\n')
            self.whitelisted = filtered_users_to_whitelist = list()

            for userid in users_to_whitelist:
                # XXX: Should we do some checks here?
                if userid:
                    filtered_users_to_whitelist.append(unicode(userid))

            registry['plone.pwexpiry_whitelisted_users'] = set(filtered_users_to_whitelist)

        search = form.get('form.button.Search', None) is not None
        findAll = form.get('form.button.FindAll', None) is not None
        self.searchString = not findAll and form.get('searchstring', '') or ''
        self.searchResults = []
        self.newSearch = False

        if search or findAll:
            self.newSearch = True

        if submitted:
            if form.get('form.button.Modify', None) is not None:
                self.manageUser(form.get('users', None),)

        if not(self.many_users) or bool(self.searchString):
            self.searchResults = self.doSearch(self.searchString)
        return self.index()

    def doSearch(self, searchString):
        mtool = getToolByName(self, 'portal_membership')
        searchView = getMultiAdapter((aq_inner(self.context), self.request),
            name='pas_search')

        if searchString:
            explicit_users = list()
            for user in searchView.searchUsers(account_locked=True):
                added = False
                for field in ['login', 'fullname', 'email']:
                    if not added:
                        if searchString in user.get(field, '').lower():
                            explicit_users.append(user)
                            added = True
        else:
            explicit_users = searchView.searchUsers(account_locked=True)

        explicit_users = searchView.merge(explicit_users, 'userid')

        results = []
        for user_info in explicit_users:
            userId = user_info['id']
            user = mtool.getMemberById(userId)
            if user is None:
                continue
            user_info['password_date'] = \
                user.getProperty('password_date', '2000/01/01')
            user_info['last_notification_date'] = \
                user.getProperty('last_notification_date', '2000/01/01')
            user_info['fullname'] = user.getProperty('fullname', '')
            results.append(user_info)

        results.sort(key=lambda x: x is not None and x['fullname'] is not None and \
            normalizeString(x['fullname']) or '')
        return results

    def manageUser(self, users=None):
        if users is None:
            users = []
        CheckAuthenticator(self.request)

        if users:
            context = aq_inner(self.context)
            mtool = getToolByName(context, 'portal_membership')
            utils = getToolByName(context, 'plone_utils')

            unlocked = list()
            for user in users:
                if user.get('unlock'):
                    member = mtool.getMemberById(user.id)

                    member.setMemberProperties(
                        {'account_locked_date': DateTime('2000/01/01'),
                         'account_locked': False,
                         'password_tries': 0}
                    )
                    unlocked.append(user['id'])

                    notify(UserUnlocked(member))

            if unlocked:
                utils.addPortalMessage(
                    _(u'The following users were unlocked: %s'
                        % ', '.join(unlocked))
                )
            else:
                utils.addPortalMessage(_(u'No users were unlocked'))

    def formatDate(self, date):
        if date == DateTime('2000/01/01'):
            result = _(u'Never')
        else:
            result = date.strftime(DATETIME_FORMATSTRING)
        return result
