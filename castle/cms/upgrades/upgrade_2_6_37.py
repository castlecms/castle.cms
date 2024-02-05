from logging import getLogger
from zope.interface import noLongerProvides

import plone.api as api


CASTLE_LOGGER = getLogger('castle.cms')


def remove_itemplate_providers(logger=CASTLE_LOGGER):
    # this interface can be completely removed once we verify no content objects provide it
    # we don't want this upgrade step to break once ITemplate is gone, so import this way
    from castle.cms.interfaces import ITemplate

    portal_types_tool = api.portal.get_tool('portal_types')
    itemplate_objects = []

    # reindex site so we can be sure we really find every object that provides ITemplate
    # since we're already iterating through every object on the site, collect the objects
    # we care about in this step instead of a catalog search
    for portal_type in portal_types_tool:
        logger.info('reindexing object_provides for portal_type ' + portal_type)
        # this could take a while
        for portal_type_brain in api.content.find(portal_type=portal_type):
            try:
                content_object = portal_type_brain.getObject()
                content_object.reindexObject(idxs=['object_provides'])
                if ITemplate.providedBy(content_object):
                    itemplate_objects.append(content_object)
            except Exception:
                logger.info('something weird happened with ' + repr(portal_type_brain))
                continue

    itemplate_object_count = len(itemplate_objects)
    plural_suffix = '' if itemplate_object_count == 1 else 's'
    logger.info('{itemplate_object_count} content object{plural_suffix} provided ITemplate interface'.format(
        itemplate_object_count=itemplate_object_count,
        plural_suffix=plural_suffix,
    ))

    for itemplate_object in itemplate_objects:
        logger.info('removing ITemplate from object ' + itemplate_object.id)
        noLongerProvides(itemplate_object, ITemplate)
        itemplate_object.reindexObject(idxs=['object_provides'])


def upgrade(site, logger=CASTLE_LOGGER):
    try:
        remove_itemplate_providers()
    except ImportError:
        logger.info('ITemplate no longer exists, skipping most of this upgrade step')

    try:
        del api.portal.get().template_list
        logger.info('Deleted "template_list" from Portal object')
    except AttributeError:
        logger.info('Portal object did not have property "template_list"')
