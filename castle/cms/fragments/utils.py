from zope.component import getAllUtilitiesRegisteredFor
from castle.cms.fragments.interfaces import IFragmentsDirectory

import time
import threading

_local_cache = threading.local()

# Optimize this
def getFragment(context, request, name):
    if not hasattr(_local_cache, '_getFragment'):
        _local_cache._getFragment = ''
        ob = _getFragment()
    else:
        ob = _local_cache._getFragment
    result = ob(context, request, name)
    _local_cache._getFragment = ob
    return result


class _getFragment(object):
    
    def __init__(self):
        """
        The init creates the dictionary of dictionaries so that we can use multiple fragments that came before this.  
        It should also automatically delete any dictionary that is older than 10 - 20 minutes.
        """
        self._transaction_history = [{
            "context"        : '',
            "request"        : '',
            "name"           : '',
            "utils"          : [],
            "result"         : '',
            "creation_time"  : time.time(),
        }]
        self._p_changed = True


    def __call__(self, context, request, name):
        utils = getAllUtilitiesRegisteredFor(IFragmentsDirectory)
        utils.sort(key=lambda u: u.order)
        
        for transactions in self._transaction_history:
            # Helps to delete dictionaries that are older than 10 minutes
            if transactions.get("creation_time") - time.time() < 6000:                        
                """ Going from in to out, lambda creates a mini function with a list of two variables, 
                x[0] is the received variables, and x[1] is the cached variables.  
                The map creates a list of trues and falses and 
                if there is a false in the list it will automatically skip this."""
                if not False in map(lambda x: True if x[0] == transactions.get(x[1]) else False,
                                [[context, "context"], [request, "request"], [name, "name"]]):  
                    """ Again going from in to out, 
                    since utils is a list we check the inner list, 
                    with x being the receiver, and y being the cached utils."""
                    if not False in map(lambda x, y: True if x == transactions.get("utils")[y] else False,
                                    utils, range(utils.len())):
                    
                        return self._transaction_history.get("result")
            else:
                self._transaction_history.remove(transactions)
                self._p_changed = True

        for util in reversed(utils):
            result = self.utility_get(context, request, name, util)
            if not result == 0:
                self.add_dictionary(context, request, name, utils, result)
                return result
    
        raise KeyError(name)

    def add_dictionary(self, context, request, name, utils, result):
        self._transaction_history.append({
            "context"       : context,
            "request"       : request,
            "name"          : name,
            "utils"         : utils,
            "result"        : result,
            "creation_time" : time.time()
            })
        self._p_changed = True

    def utility_get(self, context, request, name, utils):
        if utils.layer is not None:
            if not utils.layer.providedBy(request):
                return 0
        try:
            return utils.get(context, request, name)
        except KeyError:
            return 0
        
