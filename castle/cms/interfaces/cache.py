from zope.interface import Interface

class ICastleCmsgetFragment(Interface):
    """
    Provides a cache and a call into the zope architecture for tile fragments.  A cache to save on computational time and a zope
    system call to find utilities if the cache is out of date or it can't find the result in the cache.
    """

    def add_dictionary(context, request, name, utils, result):
        "adds to the list a new dictionary"

    def utility_get(context, request, name, utils):
        "It gets the information from a single utility."
        "Using the context, request, and name as keys and util as the utility."
        "Is very computationally expensive"

