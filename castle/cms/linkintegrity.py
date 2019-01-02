from castle.cms.interfaces import IReferenceNamedImage
from plone.app.uuid.utils import uuidToObject
from persistent.mapping import PersistentMapping
from persistent.dict import PersistentDict
from lxml.html import fromstring
from lxml.html import tostring
from plone import api
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.linkintegrity import handlers as li
from plone.app.linkintegrity.parser import extractLinks
from plone.tiles.data import ANNOTATIONS_KEY_PREFIX
from z3c.relationfield import RelationValue
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.keyreference.interfaces import NotYet


def scan(obj):
    """ a dexterity based object was modified """
    if not li.check_linkintegrity_dependencies(obj):
        return
    refs = get_content_links(obj)
    li.updateReferences(obj, refs)


def get_ref(obj, intids=None):
    if intids is None:
        intids = getUtility(IIntIds)
    try:
        objid = intids.getId(obj)
    except KeyError:
        try:
            intids.register(obj)
            objid = intids.getId(obj)
        except NotYet:
            # if we get a NotYet error, the object is not
            # attached yet and we will need to get links
            # at a later time when the object has an intid
            pass
    return objid


def get_content_links(obj):
    refs = set()
    if ILayoutAware.providedBy(obj):
        behavior_data = ILayoutAware(obj)
        # get data from tile data
        annotations = IAnnotations(obj)
        for key in annotations.keys():
            if key.startswith(ANNOTATIONS_KEY_PREFIX):
                data = annotations[key]
                refs |= get_tile_data_links(obj, data)
        if not behavior_data.contentLayout and behavior_data.content:
            dom = fromstring(behavior_data.content)
            for el in dom.cssselect('.mosaic-text-tile .mosaic-tile-content'):
                links = extractLinks(tostring(el))
                refs |= li.getObjectsFromLinks(obj, links)
    try:
        # scan more than just this we probably should...
        value = obj.text.raw
        links = extractLinks(value)
        refs |= li.getObjectsFromLinks(obj, links)
    except AttributeError:
        pass

    if getattr(obj, 'image', None):
        if IReferenceNamedImage.providedBy(obj.image):
            sub_obj = uuidToObject(obj.image.reference)
            if sub_obj:
                objid = get_ref(obj)
                if objid:
                    refs.add(RelationValue(objid))
    return refs


def get_tile_data_links(obj, data):
    refs = set()
    if type(data) in (dict, PersistentMapping, PersistentDict):
        for field_name in ('content', 'video', 'image', 'images', 'audio'):
            if field_name not in data:
                continue
            val = data.get(field_name)
            if isinstance(val, basestring):
                links = extractLinks(val)
                refs |= li.getObjectsFromLinks(obj, links)
            elif isinstance(val, list):
                # could be list of uids
                refs |= get_refs_from_uids(val)
    return refs


def get_refs_from_uids(uids):
    intids = getUtility(IIntIds)
    objects = set()
    catalog = api.portal.get_tool('portal_catalog')
    for brain in catalog(UID=uids):
        obj = brain.getObject()
        objid = get_ref(obj, intids)
        if objid:
            relation = RelationValue(objid)
            objects.add(relation)
    return objects
