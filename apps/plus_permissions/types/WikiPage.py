
# Permissions for OurPost, an example 
from django.db import models

from apps.plus_permissions.models import SetSliderOptions, SetAgentSecurityContext, SetAgentDefaults, SetPossibleTypes, SetSliderAgents, SliderOptions, add_type_to_interface_map, get_interface_map, SetVisibleTypes, SetTypeLabels

from apps.plus_permissions.interfaces import InterfaceReadProperty, InterfaceWriteProperty, InterfaceCallProperty


from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from apps.plus_groups.models import TgGroup

from apps.plus_wiki.models import WikiPage
content_type = WikiPage

from apps.plus_permissions.default_agents import get_or_create_root_location, get_anonymous_group, get_all_members_group, get_creator_agent


# This represents a typical model type from another django or pinax app


# And these are the "child" types that can be created inside this type. 
# Currently OurPost has none, but, for example, a TgGroup can have OurPosts or WikiPages etc.
child_types = []
SetPossibleTypes(content_type, child_types)
SetVisibleTypes(content_type, [WikiPage])
SetTypeLabels(content_type, 'Page')


# Here's the wrapping we have to put around it.

class WikiPageViewer: 
    name = InterfaceReadProperty
    title = InterfaceReadProperty
    content = InterfaceReadProperty
    license = InterfaceReadProperty
    copyright_holder = InterfaceReadProperty
    links_to = InterfaceReadProperty
    in_agent = InterfaceReadProperty
    stub = InterfaceReadProperty
    created_by = InterfaceReadProperty
    creation_time = InterfaceReadProperty
    author = InterfaceReadProperty
    get_display_name = InterfaceReadProperty
    get_attachments = InterfaceCallProperty
    is_downloadable = InterfaceCallProperty

    get_url = InterfaceCallProperty
    get_display_name = InterfaceCallProperty
    get_description = InterfaceCallProperty
    get_author_name = InterfaceCallProperty
    get_author_copyright = InterfaceCallProperty
    get_created_date = InterfaceCallProperty
    get_feed_extras = InterfaceCallProperty

class WikiPageEditor:
    set_name = InterfaceCallProperty
    title = InterfaceWriteProperty
    content = InterfaceWriteProperty
    license = InterfaceWriteProperty
    copyright_holder = InterfaceWriteProperty
    stub = InterfaceWriteProperty
    author = InterfaceWriteProperty

class WikiPageCreator:
    created_by = InterfaceWriteProperty

class WikiPageManager:
    delete = InterfaceCallProperty
    move_to_new_group = InterfaceCallProperty

class WikiPageCommentor: 
    comment = InterfaceCallProperty

class WikiPageCommentViewer:
    view_comments = InterfaceReadProperty

if not get_interface_map(WikiPage):
    WikiPageInterfaces = {'Viewer':WikiPageViewer,
                          'Editor':WikiPageEditor,
                          'Manager':WikiPageManager,
                          'Creator':WikiPageCreator,
                          "Commentor":WikiPageCommentor,
                          "ViewComments":WikiPageCommentViewer}

    add_type_to_interface_map(content_type, WikiPageInterfaces)

if not SliderOptions.get(WikiPage, False):
    SetSliderOptions(WikiPage, {'InterfaceOrder':['Viewer', 'Editor','Commentor', 'Manager', 'ManagePermissions'], 'InterfaceLabels':{'Viewer':'View', 'Editor':'Edit', 'Commentor':'Comment', 'Manager':'Manage (Move / Delete)', 'ManagePermissions':'Change Permissions'}})



