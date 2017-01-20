from castle.cms import constants
from castle.cms.vocabularies import BusinessTypesVocabulary
from plone.keyring import django_random
from Products.CMFPlone.interfaces import controlpanel
from Products.CMFPlone.utils import validate_json
from zope import schema
from zope.interface import Interface
from zope.schema.vocabulary import SimpleVocabulary

def create_term(val, label):
    return SimpleVocabulary.createTerm(val, val, label)


class ISocialMediaSchema(controlpanel.ISocialMediaSchema):
    twitter_consumer_key = schema.TextLine(
        title=u'Twitter consumer key',
        default=None,
        required=False)

    twitter_consumer_secret = schema.TextLine(
        title=u'Twitter consumer secret',
        default=None,
        required=False)

    twitter_oauth_token = schema.TextLine(
        title=u'Twitter OAuth token',
        required=False)

    twitter_oauth_secret = schema.TextLine(
        title=u'Twitter OAuth secret',
        required=False)

    twitter_screen_name = schema.TextLine(
        title=u'Twitter Screen Name',
        required=False)

    twitter_timeline_widget = schema.TextLine(
        title=u'Twitter widget ID',
        required=True,
        default=u'684100313582833665')

    disquis_shortname = schema.TextLine(
        title=u'Disqus Shortname',
        description=u'If provided, Disqus will be used instead of '
                    u"Plone's default commenting mechanism. You need "
                    u'to sign up for disqus in order for this feature to work',
        required=False,
        default=None)

    youtube_channel = schema.URI(
        title=u'Youtube channel URL',
        required=False
    )

    google_plus_username = schema.TextLine(
        title=u'Google+ username',
        required=False
    )

    github_username = schema.TextLine(
        title=u'Github Username',
        required=False
    )


class ISiteSchema(controlpanel.ISiteSchema):
    short_site_title = schema.TextLine(
        title=u'Short site title',
        default=u"Castle",
        required=False)

    site_icon = schema.ASCII(
        title=u"Site Icon",
        description=u'Castle will use this icon to generate all the various '
                    u'icons for mobile devices necessary',
        required=False,
    )

    public_url = schema.TextLine(
        title=u'Public site url',
        default=None,
        required=False)

    backend_url = schema.TextLine(
        title=u'Backend site url',
        default=u'',
        required=False)

    system_email_addresses = schema.List(
        title=u"System email addresses",
        description=u'List of admin email addresses',
        default=[],
        missing_value=[],
        value_type=schema.TextLine(),
        required=False)

    disable_contact_form = schema.Bool(
        title=u'Disable contact form',
        default=False)

    enable_notification_subscriptions = schema.Bool(
        title=u'Enable notification subscriptions',
        description=u'By going to @@subscribe',
        default=False)


class ISecuritySchema(controlpanel.ISecuritySchema):
    failed_login_attempt_window = schema.Int(
        title=u'Failed login attempts window(seconds)',
        required=True,
        default=900)

    max_failed_login_attempts = schema.Int(
        title=u'Max failed login attempts',
        required=True,
        default=8)

    days_to_clean_disabled_users = schema.Int(
        title=u'Number of days before disabled users are removed',
        default=30
    )

    login_shield_setting = schema.Choice(
        title=u'Login shield',
        description=u'Require user to login before they can even '
                    u'access the site',
        default=constants.SHIELD.NONE,
        vocabulary=SimpleVocabulary([
            create_term(constants.SHIELD.NONE, 'Not active'),
            create_term(constants.SHIELD.BACKEND, 'Protect only backend urls'),
            create_term(constants.SHIELD.ALL, 'Protect all traffic. BE CAREFUL ACTIVATING THIS.'),
        ])
    )

    two_factor_enabled = schema.Bool(
        title=u'Require two factor authentication',
        description=u'Requires users to have email and/or phone number set',
        default=False,
    )

    restrict_logins_to_countries = schema.Tuple(
        title=u'Restrict logins to countries',
        description=u'Choose countries that logins should be restricted to. '
                    u'This feature only works if your proxy server is '
                    u'forwarding the user country code to the Castle server. '
                    u'Leave empty to allow all logins.',
        missing_value=(),
        default=(),
        required=False,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.Countries'
        )
    )


class IAnnoucementData(Interface):
    show_announcement = schema.Bool(
        title=u'Show site announcement',
        default=False,
        required=False)

    site_announcement = schema.Text(
        title=u"Site announcement",
        default=u'<p><strong>Breaking News:</strong> '
                u'<a href="#" style="color: white;">Follow Updates from...</a></p>',
        required=False
    )

    subscriber_categories = schema.List(
        title=u'Subscription Categories',
        description=u"Categories that users can subscribe to. One per line",
        default=[],
        missing_value=[],
        required=False,
        value_type=schema.TextLine())


class ISiteConfiguration(Interface):

    image_repo_location = schema.TextLine(
        title=u'Image repo path',
        required=True,
        default=u'/image-repository')

    file_repo_location = schema.TextLine(
        title=u'File repo path',
        required=True,
        default=u'/file-repository')

    audio_repo_location = schema.TextLine(
        title=u'Audio repo location',
        required=True,
        default=u'/audio-repository')

    video_repo_location = schema.TextLine(
        title=u'Video repo location',
        required=True,
        default=u'/video-repository')

    max_file_size = schema.Int(
        title=u'Max file size(MB)',
        description=u'Before uploading to S3 storage',
        default=50)

    allowed_locations = schema.List(
        title=u'Allowed locations',
        default=[],
        missing_value=[],
        required=False,
        value_type=schema.TextLine())

    publish_require_quality_check = schema.Bool(
        title=u'Require quality check in publishing',
        description=u'Require quality check passing before content can be published. If it '
                    u'does not pass, user needs to add comment in order to override.',
        default=False
    )


class IAPISettings(Interface):
    princexml_server_url = schema.TextLine(
        title=u'PrinceXML server url',
        description=u'required in order to convert documents',
        default=u'http://localhost:6543/convert',
        required=False)

    google_maps_api_key = schema.TextLine(
        title=u'Google Maps API Key',
        default=None,
        required=False)

    google_api_email = schema.TextLine(
        title=u'Google API Email',
        default=None,
        required=False)

    google_api_service_key_file = schema.ASCII(
        title=u"Google API Service Key File",
        description=u'Private key file',
        required=False,
    )

    google_analytics_id = schema.TextLine(
        title=u'Google Analytics ID',
        description=u'for use with gathering content statistics',
        required=False)

    recaptcha_public_key = schema.TextLine(
        title=u'Recaptcha 3 Public Key',
        required=False)

    recaptcha_private_key = schema.TextLine(
        title=u'Recaptcha 3 Private Key',
        required=False)

    aws_s3_key = schema.TextLine(
        title=u'AWS S3 Key',
        required=False,
        default=None)

    aws_s3_secret = schema.TextLine(
        title=u'AWS S3 Secret',
        required=False,
        default=None)

    aws_s3_bucket_name = schema.TextLine(
        title=u'AWS S3 Bucket',
        required=False,
        default=None)

    aws_s3_host_endpoint = schema.TextLine(
        title=u'AWS Host endpoint',
        description=u'Leave empty unless you know what you are doing here.',
        required=False,
        default=None)

    aws_s3_base_url = schema.TextLine(
        title=u'AWS File Base Url',
        description=u'If you are providing your own domain name to serve files from',
        required=False,
        default=None)

    plivo_auth_id = schema.TextLine(
        title=u'Plivo Auth ID',
        description=u'Text messaging API',
        required=False)

    plivo_auth_token = schema.TextLine(
        title=u'Plivo Auth Token',
        required=False)

    plivo_phone_number = schema.TextLine(
        title=u'Plivo Source Number',
        description=u'For making text messages from',
        required=False)

    etherpad_url = schema.TextLine(
        title=u'Etherpad Url',
        required=False
    )

    etherpad_api_key = schema.TextLine(
        title=u'Etherpad API Key',
        required=False
    )

    cf_api_key = schema.TextLine(
        title=u'Cloudflare API Key',
        description=u'Setting an API Key here and enabling cache purging '
                    u'activates purging against Cloudflare.',
        required=False
    )

    cf_email = schema.TextLine(
        title=u'Cloudflare Email',
        description=u'One associated with cloudflare api key',
        required=False
    )

    cf_zone_id = schema.TextLine(
        title=u'Cloudflare Zone ID',
        required=False)

    rocket_chat_front_page = schema.TextLine(
        title=u'Rocket.Chat User URL',
        description=u'URL of the Rocket.Chat server to connect to',
        required=False
    )

    rocket_chat_secret = schema.TextLine(
        title=u'Rocket.Chat secret',
        description=u'Text string used to salt Rocket.Chat authentication tokens',
        required=False,
        default=unicode(django_random.get_random_string(64))
    )

class IArchivalSettings(Interface):
    archival_enabled = schema.Bool(
        title=u'Archival Enabled',
        description=u'Archives are stored in configured AWS bucket',
        default=False)

    archival_number_of_days = schema.Int(
        title=u'Archival number of days from last edit',
        description=u'For the archival to find content to archive',
        default=365 * 3)

    archival_types_to_archive = schema.List(
        title=u'Types to archive',
        default=[
            'News Item'
        ],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary="castle.cms.vocabularies.ReallyUserFriendlyTypes"))

    archival_states_to_archive = schema.List(
        title=u'States to archive',
        description=u'These MUST be states that allow anonymous users to view the content. '
                    u'Any states that do not, will be ignored',
        default=[
            'published'
        ],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary="plone.app.vocabularies.WorkflowStates"))

    archival_replacements = schema.Dict(
        title=u'Archival replacements',
        description=u'Replacement text that will be applied to the content being archived.',
        default={},
        missing_value={},
        required=False,
        key_type=schema.TextLine(),
        value_type=schema.TextLine())


class ICastleSettings(
        ISiteConfiguration,
        IAPISettings,
        IAnnoucementData,
        IArchivalSettings):
    pass


class IBusinessData(Interface):
    business_type = schema.Choice(
        title=u'Business Type',
        vocabulary=BusinessTypesVocabulary,
        default=None,
        required=False
    )

    business_name = schema.TextLine(
        title=u'Business Name',
        required=False)

    business_address = schema.TextLine(
        title=u'Address',
        required=False)

    business_city = schema.TextLine(
        title=u'City',
        required=False)

    business_state = schema.TextLine(
        title=u'State',
        required=False)

    business_postal_code = schema.TextLine(
        title=u'Postal Code',
        required=False)

    business_country = schema.TextLine(
        title=u'Country',
        required=False,
        default=u'US')

    business_coordinates = schema.Text(
        title=u'Coordinates',
        description=u'Search for address to get the coordinates of business address',
        default=u'{}',
        required=False,
        constraint=validate_json
    )

    business_telephone = schema.TextLine(
        title=u'Telephone',
        required=False)

    business_days_of_week = schema.List(
        title=u'Days open',
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary([
                SimpleVocabulary.createTerm('Monday', 'Monday', 'Monday'),
                SimpleVocabulary.createTerm('Tuesday', 'Tuesday', 'Tuesday'),
                SimpleVocabulary.createTerm('Wednesday', 'Wednesday', 'Wednesday'),
                SimpleVocabulary.createTerm('Thursday', 'Thursday', 'Thursday'),
                SimpleVocabulary.createTerm('Friday', 'Friday', 'Friday'),
                SimpleVocabulary.createTerm('Saturday', 'Saturday', 'Saturday'),
                SimpleVocabulary.createTerm('Sunday', 'Sunday', 'Sunday')
            ])
        )
    )

    business_opens = schema.TextLine(
        title=u'Opens',
        description=u'In the format of 08:00',
        required=False)

    business_closes = schema.TextLine(
        title=u'Closes',
        description=u'In the format of 08:00',
        required=False)

    business_special_hours = schema.List(
        title=u'Special hours',
        description=u'In the format Day|Opens|Closes. Example: Saturday|08:00|12:00',
        value_type=schema.TextLine(),
        default=[],
        required=False)

    business_menu_link = schema.TextLine(
        title=u'Menu link',
        description=u'If your business has a menu, provide link here',
        required=False)

    business_accepts_reservations = schema.Bool(
        title=u'Accepts Reservations',
        default=False)

    business_additional_configuration = schema.Text(
        title=u'Additional Configuration',
        description=u'See https://developers.google.com/structured-data/local-businesses/ '
                    u'for details on how to configuration business search data',
        constraint=validate_json,
        required=False)


class ICrawlerConfiguration(Interface):
    crawler_active = schema.Bool(
        title=u'Active',
        required=False,
        default=False)

    crawler_index_archive = schema.Bool(
        title=u'Index archives',
        required=False,
        default=False
    )

    crawler_site_maps = schema.List(
        title=u'Site maps',
        required=False,
        value_type=schema.TextLine()
    )

    crawler_user_agent = schema.TextLine(
        title=u'User Agent',
        description=u'User agent to use when crawling sites',
        default=u'Castle CMS Crawler 1.0'
    )
