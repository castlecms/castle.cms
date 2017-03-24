from castle.cms import tasks
from castle.cms.interfaces import ITrashed
from plone import api
from plone.dexterity.interfaces import IDexterityContainer
from zope.interface import alsoProvides
from zope.interface import noLongerProvides


def object(ob):
    state = api.content.get_state(obj=ob, default=None)
    if state is not None and state != 'private':
        try:
            api.content.transition(obj=ob, to_state='private')
        except api.exc.InvalidParameterError:
            pass

    alsoProvides(ob, ITrashed)

    ob.setModificationDate()
    ob.reindexObject(idxs=['trashed', 'object_provides', 'modified'])
    if IDexterityContainer.providedBy(ob):
        tasks.trash_tree.delay(ob)


def restore(ob):
    noLongerProvides(ob, ITrashed)
    ob.reindexObject(idxs=['trashed', 'object_provides'])
    if IDexterityContainer.providedBy(ob):
        tasks.trash_tree.delay(ob)
