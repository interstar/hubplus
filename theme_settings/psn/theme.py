# selected by PROJECT_THEME

from django.utils.translation import ugettext_lazy as _

PROJECT_NAME=_("Mental Health and Psychosocial Support Network")
COPYRIGHT_HOLDER=_('Psychosocial Support Network')

VIRTUAL_HUB_NAME = 'MHPSS Network'
ALL_MEMBERS_NAME = 'All Members'
VIRTUAL_MEMBERS_GROUP_NAME = 'virtual_members'
VIRTUAL_MEMBERS_DISPLAY_NAME = 'MHPSS Network'

EXPLORE_NAME = _('Resources')

SITE_NAME = _("Psychosocial Support Network")
SITE_NAME_SHORT = _("MHPSS Network")

GROUP_TYPES = (
    (u'interest', u'Interest'),
    (u'organisation', u'Organisation'),
    (u'project', u'Project'),
    (u'internal', u'Internal'),
    (u'hub', u'Main Region'),
)

CONTACT_EMAIL= "info@psychosocialnetwork.net"
SUPPORT_EMAIL = "support@psychosocialnetwork.net"

HUB_NAME = _('Region')
HUB_NAME_PLURAL = _('Regions')
MAIN_HUB_NAME = _('Main Region')

EXPLORE_SEARCH_TITLE = _('explore search title')
MEMBER_SEARCH_TITLE = _('Search Members')
GROUP_SEARCH_TITLE = _('Search Groups')
HUB_SEARCH_TITLE = _('Search Regions')

TAG_SEARCH_TITLE = _('Find a Tag')
SIDE_SEARCH_TITLE = _('side search title')

STATUS_COPY = _('Update the Network, what are you doing right now ?')

INVITE_EMAIL_TEMPLATE = """
Dear {{first_name}} {{last_name}}, 

{{sponsor}} has invited you to become a member of MHPSS network.

Join and enter a worldwide community of people and organizations concerned with mental health & psychosocial support. Discover and learn about new Resources, Members, Groups and Regions from the worldwide network."""

APPLICATION_REJECT_TEMPLATE = """
Dear {{first_name}} {{last_name}},

Thank you for applying to join MHPSS network.

Unfortunately, we can not accept you to become a member at this time.

"""

PASSWORD_RESET_TEMPLATE = """
Dear %(display_name)s,

You have requested to change your password, to reset your password click here: %(link)s

Your username, in case you've forgotten : %(username)s

You should log in as soon as possible and change your password.

Thanks for using our site!
"""
