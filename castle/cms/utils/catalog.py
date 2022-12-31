from plone import api


def add_indexes(indexes):
    """
    indexes should be a tuple of (name of the index, index type)
    """
    catalog = api.portal.get_tool('portal_catalog')
    for name, _type in indexes.items():
        if name not in catalog.indexes():
            if type(_type) == dict:
                real_type = _type['type']
                del _type['type']
                catalog.addIndex(name, real_type, **_type)
            else:
                catalog.addIndex(name, _type)


def delete_indexes(indexes):
    catalog = api.portal.get_tool('portal_catalog')
    for name in indexes:
        if name in catalog.indexes():
            catalog.delIndex(name)


def add_metadata(metadata):
    catalog = api.portal.get_tool('portal_catalog')
    _catalog = catalog._catalog
    for name in metadata:
        if name not in catalog.schema():
            # override how this works normally to not cause a reindex
            schema = _catalog.schema
            names = list(_catalog.names)
            values = schema.values()
            if values:
                schema[name] = max(values) + 1
            else:
                schema[name] = 0
            names.append(name)

            _catalog.names = tuple(names)
            _catalog.schema = schema


def delete_metadata(metadata):
    catalog = api.portal.get_tool('portal_catalog')
    for name in metadata:
        if name in catalog.schema():
            catalog.delColumn(name)
