import pycountry
from Acquisition import aq_parent
from castle.cms.fragments.interfaces import IFragmentsDirectory
from castle.cms.browser.survey import ICastleSurvey
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getAllUtilitiesRegisteredFor
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import directlyProvides
from zope.interface import implementer
from zope.interface import implements
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from plone.app.tiles.browser.edit import AcquirableDictionary
from plone.app.content.browser import vocabulary
import requests
import json


# XXX needs updating in 5.1
try:
    vocabulary.PERMISSIONS['plone.app.vocabularies.Groups'] = 'Modify portal content'
    vocabulary.PERMISSIONS['castle.cms.vocabularies.EmailCategories'] = 'Modify portal content'
    vocabulary.PERMISSIONS['castle.cms.vocabularies.Surveys'] = 'Modify portal content'
    vocabulary.PERMISSIONS['plone.app.vocabularies.Keywords'] = 'View'
    vocabulary.PERMISSIONS['castle.cms.vocabularies.ProvidesTitleSummaryLeadImage'] = 'View'
except KeyError:
    vocabulary._permissions['plone.app.vocabularies.Groups'] = 'Modify portal content'
    vocabulary._permissions['castle.cms.vocabularies.EmailCategories'] = 'Modify portal content'
    vocabulary._permissions['castle.cms.vocabularies.Surveys'] = 'Modify portal content'
    vocabulary._permissions['plone.app.vocabularies.Keywords'] = 'View'
    vocabulary._permissions['castle.cms.vocabularies.ProvidesTitleSummaryLeadImage'] = 'View'
vocabulary._unsafe_metadata.append('last_modified_by')


_blacklist = (
    'editbar',
    'footer',
    'mainlinks',
    'sidenav',
    'sitetitle',
    'statusmessage',
    'toplinks',
    'topsharing',
    'mobilelinks',
    'mobilenav',
    'announcement',
    'search')

_dashboard_available = (
    'dashboard-statistics',
    'dashboard-welcome'
)


def AvailableFragments(context):
    # need to move import here since vocab module is used in interfaces
    from castle.cms.interfaces import IDashboard

    if isinstance(context, AcquirableDictionary):
        context = aq_parent(context)
    is_dash = IDashboard.providedBy(context)

    utils = getAllUtilitiesRegisteredFor(IFragmentsDirectory)
    all_frags = []
    request = getRequest()
    for util in utils:
        if util.layer is not None:
            if not util.layer.providedBy(request):
                continue
        all_frags.extend(util.list())

    terms = [SimpleVocabulary.createTerm('', '', 'Select fragment')]
    frags = []
    for frag in set(all_frags):
        if (frag in _blacklist or
                (not is_dash and frag in _dashboard_available)):
            continue
        if frag[0] == '_' or frag[-1] == '_':
            continue
        frags.append(frag)
    frags.sort()
    for frag in frags:
        terms.append(
            SimpleVocabulary.createTerm(
                frag, frag, frag.capitalize().replace('-', ' ')))
    return SimpleVocabulary(terms)


directlyProvides(AvailableFragments, IContextSourceBinder)


class RegistryValueSource(object):
    implements(IContextSourceBinder)

    def __init__(self, key_name, default=[]):
        self.key_name = key_name
        self.default = default

    def __call__(self, context):
        registry = getUtility(IRegistry)
        terms = []
        for value in registry.get(self.key_name, self.default):
            key = value
            if '|' in value:
                key, _, value = value.partition('|')
            terms.append(
                SimpleVocabulary.createTerm(key, key.encode('utf-8'), value))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class LocationsVocabularyFactory(object):

    def __call__(self, context):
        return RegistryValueSource('castle.allowed_locations')(context)


LocationsVocabulary = LocationsVocabularyFactory()


@implementer(IVocabularyFactory)
class MimeTypeVocabularyFactory(object):

    def __call__(self, context):
        catalog = api.portal.get_tool('portal_catalog')
        catalog.uniqueValuesFor('contentType')
        terms = []
        for value in catalog.uniqueValuesFor('contentType'):
            human = value
            if 'html' in value:
                human = 'HTML'
            elif value.split('/')[0] in ('audio', 'video', 'image'):
                human = value.split('/')[-1].upper()
            terms.append(
                SimpleVocabulary.createTerm(
                    value, value.encode('utf-8'), human))
        return SimpleVocabulary(terms)


MimeTypeVocabulary = MimeTypeVocabularyFactory()


@implementer(IVocabularyFactory)
class RobotBehaviorVocabularyFactory(object):

    def __call__(self, context):
        terms = [
            {
                'value': 'index',
                'title': 'Index',
            },
            {
                'value': 'follow',
                'title': 'Follow links',
            },
            {
                'value': 'noimageindex',
                'title': 'Do not index images',
            },
            {
                'value': 'noarchive',
                'title': 'Search engines should not show a cached link to this page on a SERP.',
            },
            {
                'value': 'nosnippet',
                'title': 'Search engines should not show a snippet of this page (i.e. meta description) on a SERP.',  # noqa:E501
            },
        ]

        return SimpleVocabulary([
            SimpleTerm(
                value=term['value'],
                token=term['value'],
                title=term['title'],
            ) for term in terms
        ])


RobotBehaviorVocabulary = RobotBehaviorVocabularyFactory()


@implementer(IVocabularyFactory)
class EmailCategoryVocabularyFactory(object):

    def __call__(self, context):
        registry = getUtility(IRegistry)
        categories = registry.get('castle.subscriber_categories')
        terms = []

        for category in categories:
            terms.append(SimpleTerm(value=category, title=category))
        return SimpleVocabulary(terms)


EmailCategoryVocabulary = EmailCategoryVocabularyFactory()


@implementer(IVocabularyFactory)
class SurveyVocabularyFactory(object):

    def __call__(self, context):
        try:
            survey_settings = getUtility(IRegistry).forInterface(
                ICastleSurvey, check=False)
            list_url = '{}/survey-list'.format(survey_settings.survey_api_url)
            account_id = survey_settings.survey_account_id
            request_data = {
                'account_id': account_id
            }
            response = requests.post(list_url, data=json.dumps(request_data))
            result = response.json()
            surveys = result['list']
            terms = []
            for survey in surveys:
                terms.append(
                    SimpleTerm(title=survey['survey_name'], value=survey['uid']))
            return SimpleVocabulary(terms)
        except Exception:
            # error accessing survey api
            return SimpleVocabulary([
                SimpleTerm(title='Survey API is not set up properly',
                           value="no_api")])


SurveyVocabulary = SurveyVocabularyFactory()

BUSINES_TYPES = [
    'Restaurant',
    'AnimalShelter',
    'AutomotiveBusiness',
    'ChildCare',
    'DryCleaningOrLaundry',
    'EmergencyService',
    'EmploymentAgency',
    'EntertainmentBusiness',
    'FinancialService',
    'FoodEstablishment',
    'GovernmentOffice',
    'HealthAndBeautyBusiness',
    'HomeAndConstructionBusiness',
    'InternetCafe',
    'LegalService',
    'Library',
    'LodgingBusiness',
    'MedicalOrganization',
    'Organization',
    'ProfessionalService',
    'RadioStation',
    'RealEstateAgent',
    'RecyclingCenter',
    'SelfStorage',
    'ShoppingCenter',
    'SportsActivityLocation',
    'Store',
    'TelevisionStation',
    'TouristInformationCenter',
    'TravelAgency',
    'Airline',
    'Corporation',
    'EducationalOrganization',
    'GovernmentOrganization',
    'LocalBusiness',
    'NGO',
    'PerformingGroup',
    'SportsOrganization',
    'AutoPartsStore',
    'BikeStore',
    'BookStore',
    'ClothingStore',
    'ComputerStore',
    'ConvenienceStore',
    'DepartmentStore',
    'ElectronicsStore',
    'Florist',
    'FurnitureStore',
    'GardenStore',
    'GroceryStore',
    'HardwareStore',
    'HobbyShop',
    'HomeGoodsStore',
    'JewelryStore',
    'LiquorStore',
    'MensClothingStore',
    'MobilePhoneStore',
    'MovieRentalStore',
    'MusicStore',
    'OfficeEquipmentStore',
    'OutletStore',
    'PawnShop',
    'PetStore',
    'ShoeStore',
    'SportingGoodsStore',
    'TireShop',
    'ToyStore',
    'WholesaleStore'
]
BUSINES_TYPES.sort()
BusinessTypesVocabulary = SimpleVocabulary([
    SimpleVocabulary.createTerm('', '', 'n/a'),
] + [
    SimpleVocabulary.createTerm(name, name, name)
    for name in BUSINES_TYPES
])
del BUSINES_TYPES


BAD_TYPES = ("ATBooleanCriterion", "ATDateCriteria", "ATDateRangeCriterion",
             "ATListCriterion", "ATPortalTypeCriterion",
             "ATReferenceCriterion", "ATSelectionCriterion",
             "ATSimpleIntCriterion", "Plone Site",
             "ATSimpleStringCriterion", "ATSortCriterion", "TempFolder",
             "ATCurrentAuthorCriterion", "ATPathCriterion",
             "ATRelativePathCriterion", "Pad", 'Comment', 'Link')


class ReallyUserFriendlyTypesVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        site = getSite()
        ttool = getToolByName(site, 'portal_types', None)
        if ttool is None:
            return SimpleVocabulary([])

        items = [(ttool[t].Title(), t)
                 for t in ttool.listContentTypes()
                 if t not in BAD_TYPES]
        items.sort()
        items = [SimpleTerm(i[1], i[1], i[0]) for i in items]
        return SimpleVocabulary(items)


ReallyUserFriendlyTypesVocabularyFactory = ReallyUserFriendlyTypesVocabulary()


class CountriesVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        items = []
        for country in pycountry.countries:
            items.append(SimpleTerm(country.alpha2, country.alpha2,
                                    country.name))
        return SimpleVocabulary(items)


CountriesVocabularyFactory = CountriesVocabulary()


@implementer(IVocabularyFactory)
class ProvidesTitleSummaryLeadImageVocabulary(object):

    def __call__(self, context):
        catalog = api.portal.get_tool('portal_catalog')
        title_description_image_brains = catalog(self_or_child_has_title_description_and_image=True)
        folderish_brains = catalog(is_folderish=True)
        items = make_terms(title_description_image_brains, folderish_brains)

        return SimpleVocabulary(items)


ProvidesTitleSummaryLeadImageVocabularyFactory = ProvidesTitleSummaryLeadImageVocabulary()


def make_terms(brains1, brains2):
    results = []
    included_brains = []
    for brain in brains1:
        results.append((brain['UID'], brain['Title']))
        included_brains.append(brain['UID'])
    for brain in brains2:
        if brain['UID'] not in included_brains:
            results.append((brain['UID'], brain['Title']))
            included_brains.append(brain['UID'])

    return [SimpleTerm(value=result[0], token=result[0], title=result[1]) for result in results]
