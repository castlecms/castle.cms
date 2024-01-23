import logging
from castle.cms.utils import retriable
from collective.celery import task
from plone.app.workflow import PloneMessageFactory as _
from plone.app.workflow.events import LocalrolesModifiedEvent
from zope.event import notify


@task()
def grant_permissions():
    _grant_permissions()


@retriable()
def _grant_permissions():
    # self.context.reindexObjectSecurity()
    # notify(LocalrolesModifiedEvent(self.context, self.request))
    pass
