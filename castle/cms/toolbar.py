import copy
import json
import logging

from AccessControl import getSecurityManager
from Acquisition import aq_inner
from Acquisition import aq_parent
from castle.cms import caching
from castle.cms.interfaces import IDashboard
from castle.cms.interfaces import IToolbarModifier
from castle.cms.utils import get_chat_info
from plone import api
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.layout.navigation.defaultpage import getDefaultPage
from plone.cachepurging.interfaces import ICachePurgingSettings
from plone.dexterity.interfaces import IDexterityContainer
from plone.dexterity.interfaces import IDexterityItem
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.locking.interfaces import ITTWLockable
from plone.memoize.view import memoize
from plone.protect.authenticator import createToken
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import _checkPermission
from Products.CMFPlacefulWorkflow.permissions import ManageWorkflowPolicies
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.CMFPlone.PloneBaseTool import createExprContext
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getAllUtilitiesRegisteredFor
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import implements


logger = logging.getLogger('castle.cms')


class BaseToolbarModifier(object):
    order = 0
    layer = None
    implements(IToolbarModifier)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, result_menu, name, view):
        raise NotImplementedError()


class MenuItem(object):

    _id = None
    title = None
    order = 0
    permission = None
    path = ''
    icon_class = None
    csrf = False
    condition = None
    attrs = {}

    def __init__(self, toolbar):
        self.toolbar = toolbar
        self.context = self.toolbar.real_context
        self.folder = self.toolbar.folder
        self.site = self.toolbar.site
        if self._id is None:
            self._id = self.title.replace(' ', '-').lower()
        if self.icon_class is None:
            self.icon_class = 'icon-' + self._id

    @property
    def url(self):
        url = self.context.absolute_url() + '/' + self.path
        if self.csrf:
            if '?' in url:
                url += '&'
            else:
                url += '?'
            return url + '_authenticator=' + self.toolbar.csrf_token
        else:
            return url

    @property
    def available(self):
        if self.permission is not None:
            if not api.user.has_permission(self.permission, obj=self.context):
                return False
        if self.condition is not None:
            try:
                if not self.condition(self):
                    return False
            except Exception:
                logger.warn(
                    'Error running condition check for toolbar item %s' % self._id,  # noqa
                    exc_info=True)
                return False
        return True

    def dict(self):
        attrs = self.attrs.copy()
        attrs.update({
            'title': self.title,
            'url': self.url,
            'id': self._id,
            'icon_class': self.icon_class
        })
        return attrs


class FolderMenuItem(MenuItem):
    def __init__(self, toolbar):
        super(FolderMenuItem, self).__init__(toolbar)
        if IDexterityItem.providedBy(self.context):
            self.context = aq_parent(self.context)


class SiteMenuItem(MenuItem):
    def __init__(self, toolbar):
        super(SiteMenuItem, self).__init__(toolbar)
        self.context = toolbar.site


class NonRootMenuItem(MenuItem):
    @property
    def available(self):
        if self.toolbar.context_state.is_portal_root():
            return False
        return super(NonRootMenuItem, self).available


Spacer = 'spacer'


def MenuItemFactory(title, Base=MenuItem, **kwargs):
    class _MenuItem(Base):
        def __init__(self, toolbar):
            self.title = title
            for field_name, value in kwargs.items():
                setattr(self, field_name, value)
            super(_MenuItem, self).__init__(toolbar)
    return _MenuItem


class Utils(object):

    @property
    @memoize
    def toolbar(self):
        toolbar = Toolbar(self.context, self.request)
        toolbar.update()
        return toolbar

    def user_folder(self):
        pm = api.portal.get_tool('portal_membership')
        return pm.getHomeUrl()

    def paste_available(self):
        if not IDexterityContainer.providedBy(self.toolbar.real_context):
            return False
        try:
            return self.toolbar.folder.cb_dataValid()
        except AttributeError:
            return True
        return False

    def non_root_item(self):
        menuItem = MenuItemFactory('#', Base=NonRootMenuItem)
        return menuItem(self.toolbar).available

    def container_url(self):
        context = self.context
        if IDexterityItem.providedBy(context):
            context = aq_parent(context)

        return context.absolute_url()

    def has_layout(self):
        return ILayoutAware.providedBy(self.context)

    def show_rename(self):
        return (api.user.has_permission("Delete objects", obj=self.toolbar.folder) and  # noqa
                api.user.has_permission("Copy or Move", obj=self.toolbar.context) and  # noqa
                api.user.has_permission("Add portal content", obj=self.toolbar.context) and not  # noqa
                self.toolbar.context_state.is_portal_root())

    def show_invalidate(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ICachePurgingSettings, check=False)
        cf = caching.cloudflare.get()
        return cf.enabled or settings.cachingProxies


class Toolbar(BrowserView):
    """
    info this needs to gather...:

    - (x)menu items
    - (x)breadcrumbs
    - (x)available content to add
    - (x)user information
    - (x)site setup menu
    - (x)user menu
    - (x)workflow state information
    - (x)byline information
    - (x)locking information needs to be moved here as well
    """

    def get_addable_types(self):
        """Return menu item entries in a TAL-friendly form."""
        data = {
            'types': []
        }
        idnormalizer = queryUtility(IIDNormalizer)

        constraints = ISelectableConstrainTypes(self.folder, None)
        data['canConstrainTypes'] = False
        if constraints is not None:
            if constraints.canSetConstrainTypes() and \
                    constraints.getDefaultAddableTypes():
                data.update({
                    'canConstrainTypes': True,
                    'constrainUrl': '%s/folder_constraintypes_form' % (
                        self.folder.absolute_url(),)
                })

        site_path = '/'.join(self.site.getPhysicalPath())
        context = self.real_context
        if not IDexterityContainer.providedBy(context):
            context = aq_parent(context)
        folder_path = '/'.join(context.getPhysicalPath())[len(site_path):]
        if not folder_path:
            folder_path = '/'

        for t in self.folder.allowedContentTypes():
            typeId = t.getId()
            data['types'].append({
                'id': typeId,
                'safeId': idnormalizer.normalize(typeId),
                'title': t.Title(),
                'description': t.Description(),
                'folderPath': folder_path
            })

        return data

    def get_user_info(self):
        return {
            'id': self.user.getUserName(),
            'name': self.user.getProperty('fullname') or self.user.getUserName(),  # noqa
            'last_login_time': self._toIso(self.user.getProperty('last_login_time'))  # noqa
        }

    def get_workflow_info(self):
        state = state_id = None
        wf_tool = api.portal.get_tool('portal_workflow')
        workflows = wf_tool.getWorkflowsFor(self.real_context)
        if not workflows:
            return
        state_id = wf_tool.getInfoFor(
            ob=self.real_context, name='review_state')
        if not state_id:
            return
        for w in workflows:
            if state_id in w.states:
                state = w.states[state_id]
                break
        if not state:
            return

        transitions = []

        for action in wf_tool.listActionInfos(object=self.real_context):
            if action['category'] != 'workflow':
                continue

            transition = action.get('transition', None)
            if transition is not None:
                description = transition.description

            if action['allowed']:
                transitions.append({
                    'id': action['id'],
                    'title': action['title'],
                    'description': description
                })

        placeful = False
        try:
            pw = api.portal.get_tool('portal_placeful_workflow')
        except Exception:
            pw = None
        if pw is not None:
            if _checkPermission(ManageWorkflowPolicies, self.real_context):
                placeful = True

        return {
            'state': {
                'id': state_id,
                'title': state.title,
                'description': state.description
            },
            'transitions': transitions,
            'placefulAllowed': placeful,
            'publishRequireQualityCheck': self.registry.get(
                'castle.publish_require_quality_check', True)
        }

    def _toIso(self, dt):
        if dt:
            return dt.ISO8601()

    def get_content_info(self):
        creator_id = self.real_context.Creator()
        creator = api.user.get(creator_id)
        contributors = []
        for contributor in self.real_context.Contributors():
            user = api.user.get(contributor)
            if user:
                contributors.append({
                    'id': contributor,
                    'name': user.getProperty('fullname') or contributor
                })
        return {
            'creator': {
                'id': creator_id,
                'name': creator and creator.getProperty('fullname') or creator_id  # noqa
            },
            'expires': self._toIso(self.real_context.expires()),
            'effective': self._toIso(self.real_context.effective()),
            'modified': self._toIso(self.real_context.modified()),
            'contributors': contributors
        }

    def get_lock_info(self):
        if ITTWLockable.providedBy(self.real_context):
            info = getMultiAdapter(
                (self.real_context, self.request), name="plone_lock_info")
            details = info.lock_info()
            if details:
                details = details.copy()
                _type = details.pop('type')
                details['timeout'] = _type.timeout
                details['user_unlockable'] = _type.user_unlockable
            try:
                return {
                    'locked': info.is_locked_for_current_user(),
                    'stealable': info.lock_is_stealable(),
                    'details': details
                }
            except TypeError:
                return {
                    'locked': False,
                    'stealable': True,
                    'details': {}
                }

    @memoize
    def get_menu_modifiers(self):
        results = []
        utils = getAllUtilitiesRegisteredFor(IToolbarModifier)
        utils.sort(key=lambda u: u.order)
        for util in reversed(utils):
            if util.layer is not None:
                if not util.layer.providedBy(self.request):
                    continue
            results.append(util(self.real_context, self.request))
        return results

    def get_menu(self, name, additional=[]):
        menu = self._get_actions_menu(name, additional)
        for modifier in self.get_menu_modifiers():
            replacement = modifier(menu, name, self)
            if replacement:
                menu = replacement
        return menu

    def get_addon_buttons(self):
        return api.portal.get_registry_record(
            'castle.toolbar_buttons', default={
                'side_toolbar': [],
                'top_toolbar': []
            })

    def _get_portal_actions(self, name):
        if name not in self.pactions:
            return []
        return self.pactions[name].listActions()

    def has_permission(self, permissions):
        if type(permissions) not in (list, tuple, set):
            permissions = [permissions]
        sm = getSecurityManager()
        for permission in permissions:
            if sm.checkPermission(permission, self.real_context):
                return True
        return False

    def _get_actions_menu(self, name, additional=[]):
        menu = []

        actions = [x for x in self._get_portal_actions(name)]

        if additional is not []:
            # Include actions from the old default portal_actions to provide
            # support for Plone 5 add-ons
            for action in additional:
                actions += [x for x in self._get_portal_actions(action)]

        urlExpr = 'url_expr_object'
        conditionExpr = 'available_expr_object'
        iconExpr = 'icon_expr_object'

        for action in actions:
            if action.title == 'Spacer':
                menu.append('spacer')
                continue

            obj = copy.copy(action.__dict__)

            if obj.get('icon_class') is None:
                obj['icon_class'] = 'icon-%s' % obj['id']

            if urlExpr in obj:
                try:
                    obj['url'] = obj[urlExpr](self.econtext)
                except Exception:
                    logger.info('Could not render url expression for menu item: {}'.format(
                        obj['id']), exc_info=True)
                    continue
                del obj[urlExpr]

            if iconExpr in obj:
                del obj[iconExpr]

            if conditionExpr in obj:
                try:
                    if not obj[conditionExpr](self.econtext):
                        continue
                except Exception:
                    logger.info('Could not render condition expression for menu item: {}'.format(
                        obj['id']), exc_info=True)
                    continue
                del obj[conditionExpr]

            if obj['permissions'] and not self.has_permission(obj['permissions']):  # noqa
                continue

            if 'url' not in obj:
                obj['url'] = '#'

            if 'csrf' in obj:
                url = obj['url']
                if '?' in url:
                    url += '&'
                else:
                    url += '?'
                url = url + '_authenticator=' + self.csrf_token

                obj['url'] = url

            del obj['url_expr']

            menu.append(obj)

        return menu

    @property
    @memoize
    def real_context(self):
        context = self.context
        if ISiteRoot.providedBy(context):
            # we're at site root but actually kind of want context front page
            try:
                context = context[getDefaultPage(context)]
            except (AttributeError, KeyError):
                pass
        if IDashboard.providedBy(context):
            context = self.site
        return context

    @property
    @memoize
    def context_state(self):
        return getMultiAdapter(
            (aq_inner(self.real_context), self.request),
            name=u'plone_context_state')

    def update(self):
        self.site = api.portal.get()

        self.folder = self.context_state.folder()

        self.user = api.user.get_current()
        self.csrf_token = createToken()
        self.registry = getUtility(IRegistry)
        self.pactions = api.portal.get_tool('portal_actions')

        self.econtext = createExprContext(
            self.folder, self.site, self.real_context)

    def __call__(self):
        self.update()

        if (self.request.form.get('fc-reload') or
                'folder_contents' in self.request.URL or
                self.request.get('disable_border', False)):
            main_menu = self.get_menu('folder_contents_menu')
        else:
            main_menu = self.get_menu('toolbar_menu',
                                      ['object_buttons', 'object'])

        breadcrumbs_view = getMultiAdapter((self.real_context, self.request),
                                           name='breadcrumbs_view')

        user_menu = self.get_menu('user_menu', ['user'])
        management_menu = self.get_menu('management_menu')

        chat_info = get_chat_info()

        data = {
            'data-base-url': self.real_context.absolute_url(),
            'data-view-url': self.context_state.view_url(),
            'main_menu': main_menu,
            'management_menu': management_menu,
            'user_menu': user_menu,
            'add': self.get_addable_types(),
            'breadcrumbs': breadcrumbs_view.breadcrumbs(),
            'addon_buttons': self.get_addon_buttons(),
            'user': self.get_user_info(),
            'workflow': self.get_workflow_info(),
            'content': self.get_content_info(),
            'lock_info': self.get_lock_info(),
            'messages': list(reversed(IStatusMessage(self.request).get_all())),
            'user_id': api.user.get_current().getId(),
            'chat_info': chat_info
        }

        if '@@castle-toolbar' in self.request.URL:
            # if this was called from a request, set the ct header
            self.request.response.setHeader('Content-Type', 'application/json')

        return json.dumps(data)
