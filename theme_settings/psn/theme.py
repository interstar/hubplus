# selected by PROJECT_THEME

from django.utils.translation import ugettext_lazy as _

PROJECT_NAME=_("Mental Health and Psychosocial Support Network")
COPYRIGHT_HOLDER=_('MHPSS Network')

EXPLORE_NAME = _('Search')

HUB_NAME = _('Region')
HUB_NAME_PLURAL = _('Regions')
MAIN_HUB_NAME = _('Main Region')

# format: Title, url_name, current_area

HUB_APP_NAME = 'regions:groups'

TOP_LEVEL_TABS = [(_('Home'), 'home', ''), (_('Resources'), 'resources', 'resources'), (_('Members'), 'profile_list', 'members'),  (_("Groups"), 'groups:groups', 'groups'), (HUB_NAME_PLURAL, HUB_APP_NAME, 'hubs')]

VIRTUAL_HUB_NAME = 'all_members'
VIRTUAL_HUB_DISPLAY_NAME = 'MHPSS Network' 

SITE_NAME = _("Mental Health and Psychosocial Support Network")
SITE_NAME_SHORT = _("MHPSS Network")
SITE_NAME_SENTENCE = _("the MHPSS network")

GROUP_TYPES = (
    (u'interest', u'Interest'),
    (u'organisation', u'Organisation'),
    (u'project', u'Project'),
    (u'internal', u'Internal'),
    (u'region', u'Main Region'),
)

GROUP_HUB_TYPE = 'region'

EXPLORE_SEARCH_TITLE = _('Search Site')
MEMBER_SEARCH_TITLE = _('Search Members')
GROUP_SEARCH_TITLE = _('Search Groups')
HUB_SEARCH_TITLE = _('Search Regions')
RESOURCE_SEARCH_TITLE = _('Search Resources')

TAG_SEARCH_TITLE = _('Find a Tag')
SIDE_SEARCH_TITLE = _('side search title')

STATUS_COPY = _('Update the Network, what are you doing right now ?')

GROUP_INVITES_TO_NON_MEMBERS = False

INVITE_EMAIL_TEMPLATE = """
Dear {{first_name}} {{last_name}}, 

{{sponsor}} has invited you to become a member of MHPSS network.

Join and enter a worldwide community of people and organizations concerned with mental health & psychosocial support. Discover and learn about new Resources, Members, Groups and Regions from the worldwide network."""

GROUP_INVITE_SUBJECT_TEMPLATE = """Invitation to join {{group_name}}"""

GROUP_INVITE_TEMPLATE = """

Dear {{first_name}} {{last_name}},

{{sponsor}} has invited you to become a member of {{group_name}} on {{site_name}}.

{{special_message}}

Click on the following link to accept this invitation.

"""


PASSWORD_RESET_TEMPLATE = """
Dear %(display_name)s,

You have requested to change your password, to reset your password click here: %(link)s

Your username, in case you've forgotten : %(username)s

You should log in as soon as possible and change your password.

Thanks for using our site!
"""
#ALL THESE MESSAGES SHOULD BE DJANGO TEMPLATES LIKE THE ONE BELOW

APPLICATION_MESSAGE = """
You have received an application to: {{group_name}}

Please review applications to this group at {{review_url}}.

from: {{first_name}} {{last_name}}, {{organisation}}

email: {{email_address}}

{% if find_out %}
{{first_name}} {{last_name}} found out about {{group_name}} by:
{{find_out}}
{% endif %}

{% if country %}
{{first_name}} {{last_name}} comes from {{country}}
{% endif %}

{{first_name}} {{last_name}} wants to join {{group_name}} because:

{{request}}
"""


ACCEPTED_TO_GROUP = _("""
Dear %(applicant)s,

Your application to join the Psychosocial Support Network has been accepted. Please go to <a href="http://psychosocialnetwork.net/">the Psychosocial Support Network</a> to get started.

%(accepted_by)s
""")


APPLICATION_REJECT_TEMPLATE = """
Dear {{applicant}},

Unfortunately, we can not accept you to become a member of {{group_name}} at this time.

{{rejected_by}}

"""

# You should define the following in your local_settings.py file for your server.
# 
# GOOGLE_MAP_KEY = "ABQIAAAAUO5htA3plE0mHcReh9HGtxRH5sEjhzJfKqlMpdJ6oyx9YbCawRTJnbhBF8LBDrQ-Dos5hRa7KzIX4A"

# the following groups are to be hidden from the main group listing page
HIDDEN_GROUPS = [28, 4, 34, 10, 40, 142]


# should be over-ridden in local_settings.py
GOOGLE_ANALYTICS_TOKEN = 'UA-15037222-1'
