# -*- coding: utf-8 -*-
#
# We patch plone.app.theming because we are overriding
# how normal plone theming works
#
#
import json
import logging
import re
from urlparse import urljoin

import Globals
from Acquisition import aq_parent
from castle.cms.utils import get_context_from_request
from chameleon import PageTemplate
from chameleon import PageTemplateLoader
from lxml import etree
from lxml import html
from plone import api
from plone.app.blocks import tiles
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.layout.globals.interfaces import IViewView
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.policy import ThemingPolicy
from plone.app.theming.utils import theming_policy
from plone.dexterity.interfaces import IDexterityContent
from plone.resource.interfaces import IResourceDirectory
from plone.resource.utils import queryResourceDirectory
from Products.CMFCore.interfaces import ISiteRoot
from repoze.xmliter.serializer import XMLSerializer
from repoze.xmliter.utils import getHTMLSerializer
from zExceptions import NotFound
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides


logger = logging.getLogger('castle.cms')

OVERRIDE_ENVIRON_KEY = 'castle.override.theme'
wrapper_xpath = etree.XPath('//*[@id="visual-portal-wrapper"]')
href_xpath = etree.XPath('//*[@href]')
src_xpath = etree.XPath('//*[@src]')
js_insert_xpath = etree.XPath('//link[@data-include-js]')
css_insert_xpath = etree.XPath('//link[@data-include-css]')
script_xpath = etree.XPath('//script')
body_xpath = etree.XPath('/html/body')
head_xpath = etree.XPath('/html/head')
contentpanel_xpath = etree.XPath("//*[@data-panel='content']")
content_xpath = etree.XPath('//*[@id="content"]')
column1_xpath = etree.XPath('//*[@id="portal-column-one"]')
column2_xpath = etree.XPath('//*[@id="portal-column-two"]')
jsslot_xpath = etree.XPath('//*[@id="javascript_head_slot"]')
styleslot_xpath = etree.XPath('//*[@id="style_slot"]')
dynamic_grid_xpath = etree.XPath('//*[@dynamic-grid]')
LAYOUT_NAME = re.compile(r'[a-zA-Z_\-]+/[a-zA-Z_\-]+')


class ThemeTemplateLoader(PageTemplateLoader):

    def __init__(self, theme, template_cache=None, *args, **kwargs):
        self.file_cache = {}
        if template_cache is None:
            template_cache = {}
        self.template_cache = template_cache
        self.theme = theme
        try:
            self.folder = queryResourceDirectory(THEME_RESOURCE_NAME, theme)
        except Exception:
            self.folder = None
        super(PageTemplateLoader, self).__init__(*args, **kwargs)

    def load(self, filename, backup='index.html'):
        """Load and return a template file.

        The format parameter determines will parse the file. Valid
        options are `xml` and `text`.
        """
        if filename in self.template_cache:
            return self.template_cache[filename]

        try:
            data = self.read_file(filename)
        except Exception:
            data = None
        if not data:
            filename = backup
            if filename in self.template_cache:
                return self.template_cache[filename]
            data = self.read_file(filename)

        template = PageTemplate(data)
        self.template_cache[filename] = template
        return template

    __getitem__ = load

    def read_file(self, filename):
        if self.folder is None:
            return
        if filename in self.file_cache:
            return self.file_cache[filename]
        try:
            if isinstance(filename, unicode):
                filename = filename.encode('utf8')
            result = unicode(self.folder.readFile(filename), 'utf8')
            self.file_cache[filename] = result
            return result
        except (NotFound, IOError):
            raise KeyError

    def load_raw(self, raw):
        return PageTemplate(raw)


def join(base, url):
    """
    Join relative URL
    """
    if not (url.startswith("/") or "://" in url):
        return urljoin(base, url)
    else:
        # Already absolute
        return url


def replace_el(el, replacement):
    el.getparent().replace(el, replacement)


def add_children(el, with_children):
    for child in with_children.getchildren():
        el.append(child)


class _Transform(object):
    """
    Warning: This object is being cached in a thread local so we can NOT
    store persistent data anywhere here...
    """
    def __init__(self, name):
        # provide backup theme in case missing
        self.name = name or 'castle.theme'
        self.template_cache = {}

    def __call__(self, request, result, context=None):
        if '++plone++' in request.ACTUAL_URL:
            return
        portal = api.portal.get()
        original_context = context
        if context is None or IResourceDirectory.providedBy(context):
            original_context = context = portal

        try:
            context_url = context.absolute_url()
        except AttributeError:
            # could be a form/browser class
            try:
                context = context.context
            except Exception:
                context = aq_parent(context)
            context_url = context.absolute_url()

        if (not ISiteRoot.providedBy(context) and
                not IDexterityContent.providedBy(context)):
            context = aq_parent(context)
        portal_url = portal.absolute_url()

        raw = False
        if isinstance(result, basestring):
            raw = True
        else:
            self.rewrite(result, context.absolute_url() + '/')
            result = result.tree

        theme_base_url = '%s/++%s++%s/index.html' % (
            portal_url,
            THEME_RESOURCE_NAME,
            self.name)

        content = self.get_fill_content(result, raw)
        utils = getMultiAdapter((context, request),
                                name='castle-utils')

        layout = self.get_layout(context, request=request)
        layout = layout(
            portal_url=portal_url,
            site_url=portal_url,
            context_url=context_url,
            request=request,
            context=context,
            portal=portal,
            site=portal,
            theme_base_url=theme_base_url,
            content=content,
            anonymous=api.user.is_anonymous(),
            debug=api.env.debug_mode(),
            utils=utils
        )

        dom = getHTMLSerializer([layout])
        self.rewrite(dom, theme_base_url)
        if not raw:
            # old style things...
            self.bbb(dom.tree, result)

        dom.tree = tiles.renderTiles(request, dom.tree)

        self.add_body_classes(original_context, context, request,
                              dom.tree, result, raw)

        self.add_included_resources(dom.tree, portal, request)
        self.dynamic_grid(dom.tree)

        return dom

    def add_viewlet_tile(self, portal, request, el, name):
        tile = queryMultiAdapter(
            (portal, request), name=name)
        alsoProvides(tile, IViewView)
        if tile:
            viewlet = tile.get_viewlet(tile.manager, tile.viewlet)
            if viewlet:
                parent = el.getparent()
                index = parent.index(el)
                viewlet.update()
                value = etree.fromstring('<head>' + viewlet.render() + '</head>')
                parent.remove(el)
                for idx, child in enumerate(value.getchildren()):
                    parent.insert(index + idx, child)

    def add_included_resources(self, dom, portal, request):
        # if theme has js/css drop points instead of using those tiles
        el = js_insert_xpath(dom)
        if len(el) > 0:
            self.add_viewlet_tile(portal, request, el[0],
                                  'plone.app.standardtiles.javascripts')
        el = css_insert_xpath(dom)
        if len(el) > 0:
            self.add_viewlet_tile(portal, request, el[0],
                                  'plone.app.standardtiles.stylesheets')

    def get_loader(self):
        return ThemeTemplateLoader(
            self.name, template_cache=self.template_cache)

    def get_raw_layout(self, context, loader=None):
        '''
        Get raw layout and do not compile with chemeleon
        '''
        if loader is None:
            loader = self.get_loader()
        layout_name = self.get_layout_name(context)
        try:
            return loader.read_file(layout_name)
        except KeyError:
            if layout_name != 'index.html':
                # try backup
                try:
                    return loader.read_file('index.html')
                except KeyError:
                    pass

    def get_layout_name(self, context, default_layout='index.html'):
        '''
        Get currently selected layout name for the context
        '''
        adapted = ILayoutAware(context, None)
        selected = None
        if adapted is not None:
            selected = adapted.pageSiteLayout
            if selected is None:
                context = aq_parent(context)
                while not ISiteRoot.providedBy(context):
                    adapted = ILayoutAware(context, None)
                    if adapted and adapted.sectionSiteLayout:
                        selected = adapted.sectionSiteLayout
                        break
                    context = aq_parent(context)

        if selected is None:
            if ISiteRoot.providedBy(context):
                # check if a default layout is set
                try:
                    selected = context.portal_registry['castle.cms.default_layout'] or default_layout  # noqa
                except (AttributeError, KeyError):
                    selected = default_layout
            else:
                selected = default_layout
        return selected

    def get_layout(self, context, default_layout='index.html',
                   request=None, loader=None):
        '''
        Get currently selected layout for the context
        '''
        if loader is None:
            loader = self.get_loader()
        if request is not None and 'X-CASTLE-LAYOUT' in request.environ:
            layout = loader.load_raw(request.environ['X-CASTLE-LAYOUT'])
            selected_name = 'environ'
        else:
            selected_name = self.get_layout_name(context, default_layout)

            try:
                layout = loader[selected_name]
            except Exception:
                logger.error('Failed parsing content layout', exc_info=True)
                layout = None

            if layout is None:
                # default to 'index.html' now
                layout = loader['index.html']

        layout.name = selected_name
        return layout

    def add_body_classes(self, original_context, context, request,
                         tree, result, raw=False):
        '''
        Dynamically add useful body classes for theming and JS.
        '''
        body_classes = ''
        if raw:
            # this is a content layout likely
            plone_layout = queryMultiAdapter(
                (original_context, request), name='plone_layout')
            if plone_layout:
                body_classes += ' ' + plone_layout.bodyClass(None, None)
        else:
            content_body = body_xpath(result)
            if len(content_body) > 0:
                body_classes += ' ' + content_body[0].attrib.get('class', '')

        body = body_xpath(tree)[0]
        from plone.app.blocks.layoutbehavior import ILayoutAware
        if ILayoutAware.providedBy(context):
            body_classes += ' template-layout'
            adapted = ILayoutAware(context, None)
            if adapted is not None:
                layout = getattr(adapted, 'contentLayout', None)
                if layout:
                    # Transform ++contentlayout++default/document.html
                    # into layout-default-document
                    names = LAYOUT_NAME.findall(layout)
                    if len(names) == 1:
                        body_classes += ' layout-' + names[0].replace('/', '-')
                else:
                    body_classes += ' layout-custom'

        try:
            body_classes += ' selected-layout-%s ' % original_context.getLayout()  # noqa
        except Exception:
            pass
        classes = '%s %s' % (
            body.attrib.get('class', ''),
            body_classes
        )
        body.attrib['class'] = classes

        plone_view = queryMultiAdapter(
            (original_context, request), name='plone')
        if plone_view:
            try:
                body.attrib.update(plone_view.patterns_settings())
            except AttributeError:
                plone_view = queryMultiAdapter(
                    (context, request), name='plone')
                if plone_view:
                    body.attrib.update(plone_view.patterns_settings())

    def rewrite(self, dom, base_url):
        '''
        Rewrite layout urls to be full public paths
        '''
        if hasattr(dom, 'tree'):
            tree = dom.tree
        else:
            tree = dom
        for node in href_xpath(tree):
            url = node.get('href')
            if url:
                url = join(base_url, url)
                node.set('href', url)
        for node in src_xpath(tree):
            url = node.get('src')
            if url:
                url = join(base_url, url)
                node.set('src', url)
        return tree

    def bbb(self, dom, result):
        """
        old style page template, do some bbb things here.
        1) implement javascript_head_slot
        2) implement style_slot
        """
        # add children of javascript_head_slot after all other
        # javascript on the page
        head = head_xpath(dom)
        if len(head) > 0:
            js_slot = jsslot_xpath(result)
            if len(js_slot) > 0:
                scripts = script_xpath(dom)
                if len(scripts) > 0:
                    script = scripts[-1]  # insert after last script on page
                    parent = script.getparent()
                    script_idx = parent.index(script)
                    for idx, child in enumerate(js_slot[0].getchildren()):
                        parent.insert(script_idx + 1 + idx, child)
                else:
                    add_children(head[0], js_slot[0])
            style_slot = styleslot_xpath(result)
            if len(style_slot) > 0:
                add_children(head[0], style_slot[0])

    def get_fill_content(self, result, raw=False):
        """
        get main, left and right columns so we can potentially
        render them in the template
        """
        main_html = ''
        column1_html = ''
        column2_html = ''
        if raw:
            main_html = result
        else:
            content = contentpanel_xpath(result)
            if len(content) == 0:
                content = content_xpath(result)
            if len(content) > 0:
                main_html = html.tostring(content[0])

            column1 = column1_xpath(result)
            if len(column1) > 0 and len(column1[0]) > 0:
                column1_html = html.tostring(column1[0])
            column2 = column2_xpath(result)
            if len(column2) > 0 and len(column2[0]) > 0:
                column2_html = html.tostring(column2[0])
        return {
            'main': main_html,
            'left': column1_html,
            'right': column2_html
        }

    def dynamic_grid(self, dom):
        '''
        If there is a attribute in the layout file of `dynamic-grid`,
        this function will look into the content of that layout
        and see if any of the columns are actually empty of content.

        If they are empty, they are removed and the sibling columns
        are resized to fill the full size of content.

        Additionally, the `data-grid` attribute is set so later
        column rendering can use the configured grid transform correctly.
        '''
        for container in dynamic_grid_xpath(dom):
            found = []
            classes = []
            for child in container.getchildren():
                # remove empties
                if len(child) == 0:
                    container.remove(child)
                else:
                    found.append(child)

            for child in found:
                if 'id' in child.attrib:
                    classes.append(child.attrib['id'])
                try:
                    width = int(
                        child.attrib.get('col-count-%i' % len(found), '4'))
                except Exception:
                    width = 4
                child.attrib['data-grid'] = json.dumps({
                    "type": "cell",
                    "info": {"pos": {"width": width, "x": 0}}
                })

            classes.append('-'.join(classes))
            classes.append('col-count-%i' % len(found))
            container.attrib['class'] = '{} {}'.format(
                container.attrib.get('class', ''),
                ' '.join(classes)
            )


def getTransform(context, request):
    DevelopmentMode = Globals.DevelopmentMode
    policy = theming_policy(request)

    # Obtain settings. Do nothing if not found
    settings = policy.getSettings()

    if settings is None:
        return None

    try:
        if not policy.isThemeEnabled():
            return None
    except Exception:
        pass

    cache = policy.getCache()

    # Apply theme
    transform = None

    if not DevelopmentMode and cache.transform:
        transform = cache.transform

    if transform is None:
        name = policy.getCurrentTheme()
        transform = _Transform(name)

        if not DevelopmentMode:
            cache.updateTransform(transform)

    return transform


def renderWithTheme(context, request, content='<div />'):
    """
    Render content against a theme. `content` should be
    html that is transformed into the theming engine.

    Also, this disables further theme transform since presumably
    this is already done.
    """
    transform = getTransform(context, request)
    if transform:
        request.response.setHeader('X-Theme-Applied', 'true')
        return transform(request, content, context=context)
    else:
        return content


class Policy(ThemingPolicy):
    '''
    Customized theming policy to override plone so we do not use
    diazo.

    Diazo is an extra layer of theming that we don't need to deal
    with since we have tiles and layouts.
    '''

    def getCurrentTheme(self):
        """The name of the current theme."""
        if OVERRIDE_ENVIRON_KEY in self.request.environ:
            return self.request.environ[OVERRIDE_ENVIRON_KEY]
        settings = self.getSettings()
        if settings.currentTheme:
            return settings.currentTheme

        return None

    def isThemeEnabled(self, settings=None):
        """Whether theming is enabled."""

        # Resolve DevelopmentMode late (i.e. not on import time) since it may
        # be set during import or test setup time
        DevelopmentMode = Globals.DevelopmentMode

        # Disable theming if the response sets a header
        if self.request.response.getHeader('X-Theme-Disabled'):
            return False

        # Check for diazo.off request parameter
        true_vals = ('1', 'y', 'yes', 't', 'true')
        if (DevelopmentMode and self.request.get(
                'diazo.off', '').lower() in true_vals):
            return False

        if not settings:
            settings = self.getSettings()
        if not settings.enabled:
            return False

        server_url = self.request.get('SERVER_URL')
        proto, host = server_url.split('://', 1)
        host = host.lower()
        serverPort = self.request.get('SERVER_PORT')

        for hostname in settings.hostnameBlacklist or ():
            if host == hostname or host == ':'.join((hostname, serverPort)):
                return False

        return True


def isPloneTheme(settings):
    return (settings.rules and
            settings.rules not in (None, '_', '') and
            settings.rules.endswith('.xml'))


def transformIterable(self, result, encoding):
    """
    Apply our customize transform that attempts to provide
    b/w compatibility with diazo if user still tries to use
    a diazo powered theme.
    """
    if self.request.response.getHeader('X-Theme-Applied'):
        return
    if not isinstance(result, XMLSerializer):
        return

    # Obtain settings. Do nothing if not found
    policy = theming_policy(self.request)
    settings = policy.getSettings()
    if settings is None:
        return None
    if not policy.isThemeEnabled():
        return None

    try:
        if isPloneTheme(settings):
            # XXX old style theme
            # manual render tiles, then do theme transform
            result.tree = tiles.renderTiles(self.request, result.tree)
            result = self._old_transformIterable(result, encoding)
            return result
    except AttributeError:
        pass

    DevelopmentMode = Globals.DevelopmentMode

    try:
        # if we are here, it means we are rendering the the
        # classic way and we need to do replacements.
        # check for #visual-portal-wrapper to make sure we need
        # transform this response
        # XXX WARNING: THIS IS NECESSARY
        wrapper = wrapper_xpath(result.tree)
        if len(wrapper) == 0:
            return None

        context = get_context_from_request(self.request)
        transform = getTransform(context, self.request)
        if transform is None:
            return None

        transformed = transform(self.request, result, context=context)
        if transformed is None:
            return None

        result = transformed
        if settings.doctype:
            result.doctype = settings.doctype
            if not result.doctype.endswith('\n'):
                result.doctype += '\n'
        return result
    except etree.LxmlError:
        if not(DevelopmentMode):
            raise
    return result


def renderLayout(context, request, layout):
    '''
    Render layout directly instead of allowing the
    engine to use the current layout in a context.

    This is useful when you want to use the tile engine
    but do not want to use the theme layout to render
    the full page of a site.
    '''
    request.environ['X-CASTLE-LAYOUT'] = layout
    return renderWithTheme(context, request)
