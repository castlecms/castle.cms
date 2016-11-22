from castle.cms import archival
from castle.cms.utils import retriable
from collective.celery import task
from plone.uuid.interfaces import IUUID
from zope.component.hooks import getSite


def _sync_and_store(storage, uid):
    # need to be a bit tricky here since this could take a while to do,
    # we want to re-sync db and THEN commit...
    data = storage.archives[uid]
    storage.site._p_jar.sync()

    storage.archives[uid] = data
    storage.path_to_uid[data['path']] = uid


@retriable()
def _archive_url(url, path, uid):
    storage = archival.Storage(getSite(), UrlOpener=archival.RequestsUrlOpener)
    storage.add_url(url, path, uid)
    _sync_and_store(storage, uid)


@retriable()
def _archive_content(obj):
    storage = archival.Storage(getSite())
    storage.add_content(obj)
    _sync_and_store(storage, IUUID(obj))


@task.as_admin()
def archive_url(url, path, uid):
    return _archive_url(url, path, uid)


@task.as_admin()
def archive_content(obj):
    return _archive_content(obj)
