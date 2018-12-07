from AccessControl import Unauthorized
from Acquisition import aq_parent
from castle.cms import cache
from castle.cms import linkintegrity
from castle.cms import utils
from castle.cms.utils import retriable
from collective.celery import task
from plone import api
from Products.CMFPlone.utils import pretty_title_or_id
from collective.celery.utils import getCelery

import logging
import transaction


logger = logging.getLogger('castle.cms')


def paste_error_handle(where, op, mdatas):
    user = api.user.get_current()
    email = user.getProperty('email')
    if email:
        name = user.getProperty('fullname') or user.getId()
        try:
            utils.send_email(
                recipients=email,
                subject="Paste Operation Failed(Site: %s)" % (
                    api.portal.get_registry_record('plone.site_title')),
                html="""
<p>Hi %s,</p>

<p>The site has failed to paste your items into the /%s folder.</p>

<p>Please contact your administrator.</p>""" % (
                    name, where.lstrip('/')))
        except Exception:
            logger.warn('Could not send status email ', exc_info=True)


@retriable(on_retry_exhausted=paste_error_handle)
def _paste_items(where, op, mdatas):
    logger.info('Copying a bunch of items')
    portal = api.portal.get()
    catalog = api.portal.get_tool('portal_catalog')
    dest = portal.restrictedTraverse(str(where.lstrip('/')))

    count = 0
    commit_count = 0
    if not getCelery().conf.task_always_eager:
        portal._p_jar.sync()

    try:
        if mdatas[0][0].startswith('cache:'):
            cache_key = mdatas[0][0].replace('cache:', '')
            mdatas = cache.get(cache_key)
    except IndexError:
        pass

    for mdata in mdatas[:]:
        count += len(catalog(path={'query': '/'.join(mdata), 'depth': -1}))
        ob = portal.unrestrictedTraverse(str('/'.join(mdata)), None)
        if ob is None:
            continue
        if op == 0:
            # copy
            api.content.copy(ob, dest, safe_id=True)
        else:
            api.content.move(ob, dest, safe_id=True)

        if count / 50 != commit_count:
            # commit every 50 objects moved
            transaction.commit()
            commit_count = count / 50
            if not getCelery().conf.task_always_eager:
                portal._p_jar.sync()
            # so we do not redo it
            try:
                mdatas.remove(mdata)
            except Exception:
                pass

    # we commit here so we can trigger conflict errors before
    # trying to send email
    transaction.commit()

    user = api.user.get_current()
    email = user.getProperty('email')
    if email:
        name = user.getProperty('fullname') or user.getId()
        try:
            utils.send_email(
                recipients=email,
                subject="Paste Operation Finished(Site: %s)" % (
                    api.portal.get_registry_record('plone.site_title')),
                html="""
    <p>Hi %s,</p>

    <p>The site has finished pasting items into /%s folder.</p>""" % (
                    name, where.lstrip('/')))
        except Exception:
            logger.warn('Could not send status email ', exc_info=True)


@task()
def paste_items(where, op, mdatas):
    _paste_items(where, op, mdatas)


def delete_error_handle(where, op, mdatas):
    user = api.user.get_current()
    email = user.getProperty('email')
    if email:
        name = user.getProperty('fullname') or user.getId()
        try:
            utils.send_email(
                recipients=email,
                subject="Delete Operation Failed(Site: %s)" % (
                    api.portal.get_registry_record('plone.site_title')),
                html="""
<p>Hi %s,</p>

<p>The site has failed to delete the items.</p>

<p>Please contact your administrator.</p>""" % (
                    name, where.lstrip('/')))
        except Exception:
            logger.warn('Could not send status email ', exc_info=True)


@retriable(on_retry_exhausted=delete_error_handle)
def _delete_items(uids):
    user = api.user.get_current()
    email = user.getProperty('email')
    name = user.getProperty('fullname') or user.getId()
    errors = []
    deleted = []
    site_path = '/'.join(api.portal.get().getPhysicalPath())

    for brain in api.portal.get_tool('portal_catalog')(UID=uids):
        obj = brain.getObject()

        try:
            lock_info = obj.restrictedTraverse('@@plone_lock_info')
        except AttributeError:
            lock_info = None
        if lock_info is not None and lock_info.is_locked():
            try:
                plone_lock_operations = obj.restrictedTraverse(
                    '@@plone_lock_operations')
                plone_lock_operations.safe_unlock()
            except AttributeError:
                pass

        parent = aq_parent(obj)
        obj_path = '/'.join(obj.getPhysicalPath())[len(site_path):]
        title = pretty_title_or_id(obj, obj)
        try:
            parent.manage_delObjects(obj.getId())
            deleted.append({
                'path': obj_path,
                'title': title})
        except Unauthorized:
            errors.append({
                'path': obj_path,
                'msg': 'Unauthorized to delete object',
                'title': title
            })
        except Exception:
            errors.append({
                'path': obj_path,
                'msg': 'Unknown error attempting to delete',
                'title': title
            })

    # we commit here so we can trigger conflict errors before
    # trying to send email
    transaction.commit()

    if email:
        errors_html = ''
        if len(errors) > 0:
            error_items_html = ''
            for error in errors:
                error_items_html += '<li>{0}({1}): {2}</li>'.format(
                    error['title'], error['path'], error['msg'])
            errors_html = """
<h3>There were errors attempting to delete some of the items</h3>
<ul>%s</ul>""" % error_items_html

        items_html = ''
        for item in deleted:
            items_html += '<li>{0}({1})</li>'.format(
                item['title'], item['path'])
        deleted_html = """
<h3>Deleted items</h3>
<ul>{0}</ul>""".format(items_html)
        try:
            utils.send_email(
                recipients=email,
                subject="Finished deleting items(Site: %s)" % (
                    api.portal.get_registry_record('plone.site_title')),
                html="""
<p>Hi {0},</p>

<p>The site has finished deleting items you asked for.</p>

{1}

{2}
""".format(name, deleted_html, errors_html))
        except Exception:
            logger.warn('Could not send status email ', exc_info=True)


@task()
def delete_items(uids):

    _delete_items(uids)


@task()
def scan_links(obj):
    if isinstance(obj, basestring):
        obj = api.portal.get().restrictedTraverse(obj, None)
        if obj is None:
            return
    linkintegrity.scan(obj)


@task.as_admin()
def trash_tree(obj):
    _trash_tree(obj)


@retriable()
def _trash_tree(obj):
    """
    this is for restoring and trashing content.
    goes up the tree and re-indexes
    """
    catalog = api.portal.get_tool('portal_catalog')

    # first, query with objects that are trashed
    for brain in catalog(path={'query': '/'.join(obj.getPhysicalPath()),
                               'depth': -1},
                         trashed=True):
        ob = brain.getObject()
        # we just want to reindex because trashed should get picked
        # up for indexing now
        ob.reindexObject(idxs=['trashed', 'modified'])

    # then for ones that are not
    for brain in catalog(path={'query': '/'.join(obj.getPhysicalPath()),
                               'depth': -1}):
        ob = brain.getObject()
        # we just want to reindex because trashed should get picked up
        # for indexing now
        ob.reindexObject(idxs=['trashed', 'modified'])
