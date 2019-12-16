from zope.interface import implements
from zope.component import getSiteManager
from zope.component import getAllUtilitiesRegisteredFor
from zope.component import queryUtility
from zope.component import getUtility
from castle.cms.fragments.interfaces import IFragmentsDirectory
from castle.cms.interfaces.cache import ICastleCmsgetFragment

import time


def getFragment(context, request, name):
    if not queryUtility(ICastleCmsgetFragment, "fragment_get"):
        ob = _getFragment()
        result = ob(context, request, name)
        getSiteManager().registerUtility(ob, ICastleCmsgetFragment, name="fragment_get")
    else:
        ob = getUtility(ICastleCmsgetFragment, "fragment_get")
        result = ob(context, request, name)
    return result


class _getFragment(object):
    implements(ICastleCmsgetFragment)
    _transaction_history = []

    def __init__(self):
        self._transaction_history.append({
            "context": '',
            "request": '',
            "name": '',
            "utils": [],
            "result": '',
            "creation_time": time.time()
            })

    def __call__(self, context, request, name):
        utils = getAllUtilitiesRegisteredFor(IFragmentsDirectory)
        utils.sort(key=lambda u: u.order)

        for transactions in self._transaction_history:
            # Helps to delete dictionaries that are older than 10 minutes
            if transactions.get("creation_time") - time.time() < 600 or not name == '':
                """
                Checks the transactions name, request and context against the received,
                if not found, move to the next one.
                """
                if transactions['name'] == name and transactions['request'] == request \
                   and transactions['context'] == context:
                    """
                    Going from in to out,
                    since utils is a list we check the inner list,
                    with x being the receiver, and y being the cached utils.
                    And if there is any that is false,
                    it will select true resulting in deleting the dictionary,
                    otherwise it will send the result.
                    """
                    if False in map(lambda x, y: True if x == transactions.get("utils")[y] else False,
                                    utils, range(utils.len())):

                        """
                        If we get different utilities, it means that the utilities has been updated,
                        henceforth delete the transaction.
                        """

                        self._transaction_history.remove(transactions)

                    else:

                        return transactions['result']

            else:
                self._transaction_history.remove(transactions)

        for util in reversed(utils):
            result = self.utility_get(context, request, name, util)
            if not result == 0:
                self.add_dictionary(context, request, name, utils, result)
                return result

        raise KeyError(name)

    def add_dictionary(self, context, request, name, utils, result):
        self._transaction_history.append({
            "context": context,
            "request": request,
            "name": name,
            "utils": utils,
            "result": result,
            "creation_time": time.time()
            })

    def utility_get(self, context, request, name, utils):
        if utils.layer is not None:
            if not utils.layer.providedBy(request):
                return 0
        try:
            return utils.get(context, request, name)
        except KeyError:
            return 0
