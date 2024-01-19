import logging

import transaction
from castle.cms.utils import retriable
from collective.celery import task



@task()
def grant_permissions():
    _grant_permissions()


@retriable()
def _grant_permissions():
    pass