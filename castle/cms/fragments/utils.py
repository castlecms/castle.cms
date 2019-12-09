from zope.component import getAllUtilitiesRegisteredFor
from castle.cms.fragments.interfaces import IFragmentsDirectory

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
        self._transaction_history = {
            "context" : '',
            "request" : '',
            "name"    : '',
            "utils"   : [],
            "result"  : '',    
        }


    def __call__(self, context, request, name):
        utils = getAllUtilitiesRegisteredFor(IFragmentsDirectory)
        utils.sort(key=lambda u: u.order)
        
        if not False in map(lambda x: True if x[0] == self._transaction_history.get(x[1]) else False,
                            [[context, "context"], [request, "request"], [name, "name"]]):  

            if not False in map(lambda x, y: True if x == self._transaction_history.get("utils")[y] else False,
                                utils, range(utils.length())):

                return self._transaction_history.get("result")

            
            
        self.reset_transaction_history()
        self.reinitialize_object_internal_database(context, request, name, utils)
        

        for util in reversed(utils):
            result = self.utility_get(util)
            if not result == 0:
                self._transaction_history["result"] = result
                return result
    
        try:
            return util_result_list[0]
        except:
            raise KeyError(name)

    def reset_transaction_history(self):
        self._transaction_history.clear()
        self._transaction_history = {
            "context" : '',
            "request" : '',
            "name"    : '',
            "utils"   : [],
            "result"  : '',    
        }

    def reinitialize_object_internal_database(self, context, request, name, utils):
        self._transaction_history["context"] = context
        self._transaction_history["request"] = request
        self._transaction_history["name"] = name
        self._transaction_history["utils"] = utils
        
    def utility_get(self, util):
        if util.layer is not None:
            if not util.layer.providedBy(request):
                return 0
        try:
            return util.get(self._transaction_history["context"],
                            self._transaction_history["request"],
                            self._transaction_history["name"])
        except KeyError:
            return 0
        
