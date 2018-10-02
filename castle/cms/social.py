from zope.annotation.interfaces import IAnnotations


COUNT_ANNOTATION_KEY = 'castle.socialcounts'


def get_stats(obj):
    annotations = IAnnotations(obj)
    return annotations.get(COUNT_ANNOTATION_KEY)
