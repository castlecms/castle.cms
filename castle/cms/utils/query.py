import logging

from plone import api
from plone.app.querystring import queryparser
from plone.app.querystring.interfaces import IParsedQueryIndexModifier
from zope.component import getUtilitiesFor


logger = logging.getLogger('castle.cms')


def parse_query_from_data(data, context=None):
    if context is None:
        context = api.portal.get()
    query = data.get('query', {}) or {}
    try:
        parsed = queryparser.parseFormquery(context, query)
    except KeyError:
        logger.info('Error parsing query {}'.format(repr(query)))
        parsed = {}

    index_modifiers = getUtilitiesFor(IParsedQueryIndexModifier)
    for name, modifier in index_modifiers:
        if name in parsed:
            new_name, query = modifier(parsed[name])
            parsed[name] = query
            # if a new index name has been returned, we need to replace
            # the native ones
            if name != new_name:
                del parsed[name]
                parsed[new_name] = query

    if data.get('sort_on'):
        parsed['sort_on'] = data['sort_on']
    if data.get('sort_reversed', False):
        parsed['sort_order'] = 'reverse'
    return parsed
