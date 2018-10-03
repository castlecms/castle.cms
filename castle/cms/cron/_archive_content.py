from AccessControl.PermissionRole import rolesForPermissionOn
from Acquisition import aq_parent
from castle.cms import archival
from castle.cms.cron.utils import login_as_admin
from castle.cms.cron.utils import setup_site
from castle.cms.cron.utils import spoof_request
from castle.cms.interfaces import IArchiveManager
from castle.cms.utils import get_backend_url
from castle.cms.utils import retriable
from castle.cms.utils import send_email
from plone import api
from plone.app.layout.navigation.defaultpage import getDefaultPage
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton

import logging
import transaction


logger = logging.getLogger('castle.cms')


@retriable(sync=True)
def archive(site):
    setup_site(site)

    if (not api.portal.get_registry_record('castle.archival_enabled') or
            not api.portal.get_registry_record('castle.aws_s3_bucket_name') or
            not api.portal.get_registry_record('castle.aws_s3_key') or
            not api.portal.get_registry_record('castle.aws_s3_secret') or
            not api.portal.get_registry_record('plone.public_url')):
        logger.error('Can not archive content. Either not enabled, S3 API not set or no public '
                     'url set')
        return

    storage = archival.Storage(site)
    man = archival.ArchiveManager()
    archive_manager = IArchiveManager(man)
    for brain in archive_manager.getContentToArchive():
        try:
            ob = brain.getObject()

            container = aq_parent(ob)
            if (IPloneSiteRoot.providedBy(container) and
                    getDefaultPage(container) == ob.getId()):
                continue

            allowed = set(rolesForPermissionOn('View', ob))
            if 'Anonymous' not in allowed:
                # we can *not* archive unpublished content
                continue
            new_url = storage.add_content(ob)

            # resets login creds..
            login_as_admin(app)  # noqa

            if new_url:
                logger.warn('imported %s -> %s' % (ob.absolute_url(), new_url))
                # XXX might need to re-architect... might get conflict errors with how slow
                # archiving takes...
                api.content.delete(ob)
                transaction.commit()
            else:
                logger.error('error importing %s' % ob.absolute_url())
        except Exception:
            logger.error('Error archiving %s' % brain.getPath(), exc_info=True)

    content_to_archive = archive_manager.getContentToArchive(7)
    if len(content_to_archive) == 0:
        return

    backend_url = get_backend_url()
    # send out email warning of content about to be archived
    email_text = """
<p>Warning, this content will be archived in 7 days.
Login to
<a href="{site_url}">{site_title}</a> to extend this content.
</p>
<ul>""".format(
        site_title=api.portal.get_registry_record('plone.site_title'),
        site_url=backend_url)

    site_url = api.portal.get().absolute_url()
    for brain in content_to_archive:
        url = brain.getURL()
        url = url.replace(site_url, backend_url)
        email_text += """<li>
<a href="{url}">{title}</a></li>""".format(url=url, title=brain.Title)

    email_text += '</ul>'

    for user in api.user.get_users():
        roles = api.user.get_roles(user=user)
        if ('Site Administrator' not in roles and
                'Manager' not in roles):
            continue
        email = user.getProperty('email')
        if not email:
            continue

        name = user.getProperty('fullname') or user.getId()
        html = '<p>Hi {name},</p>'.format(name=name) + email_text
        send_email(
            recipients=email,
            subject="Content will be archived(Site: %s)" % (
                api.portal.get_registry_record('plone.site_title')),
            html=html)


def run(app):
    singleton.SingleInstance('archivecontent')

    app = spoof_request(app)  # noqa
    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            try:
                archive(obj)
            except Exception:
                logger.error('Could not archive %s' % oid, exc_info=True)


if __name__ == '__main__':
    run(app)  # noqa
