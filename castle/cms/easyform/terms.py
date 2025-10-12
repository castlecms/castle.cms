from castle.cms.interfaces import ICastleLayer
from z3c.form.interfaces import ITerms
from z3c.form.interfaces import IWidget
from z3c.form import term
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer

from .field import IQueryChoice


@implementer(ITerms)
@adapter(
    Interface,
    ICastleLayer,
    Interface,
    IQueryChoice,
    IWidget)
def QueryChoiceTerms(context, request, form, field, widget):
    return term.ChoiceTerms(context, request, form, field, widget)
