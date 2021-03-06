
# Permissions for OurPost, an example                                                                                                                        
from django.db.models.manager import *

from apps.plus_permissions.models import SecurityTag
from apps.plus_permissions.interfaces import InterfaceReadProperty, InterfaceWriteProperty, InterfaceCallProperty

from apps.profiles.models import Profile
from apps.plus_permissions.models import SetSliderOptions, SetAgentDefaults, SetPossibleTypes, SetSliderAgents
from apps.plus_links.models import Link

# Here's the wrapping we have to put around it.                                                                                                              

content_type = Profile
child_types = [Link]
SetPossibleTypes(Profile, child_types)

class ProfileViewer: 
    user = InterfaceReadProperty
    about = InterfaceReadProperty
    place = InterfaceReadProperty
    website = InterfaceReadProperty
    homeplace = InterfaceReadProperty
    homehub = InterfaceReadProperty
    organisation = InterfaceReadProperty
    role = InterfaceReadProperty
    first_name = InterfaceReadProperty
    last_name = InterfaceReadProperty

    #address = InterfaceReadProperty
    country = InterfaceReadProperty
    display_name = InterfaceReadProperty
    title = InterfaceReadProperty
    get_display_name = InterfaceCallProperty
    status = InterfaceReadProperty
    cc_messages_to_email = InterfaceReadProperty

    get_url = InterfaceCallProperty
    get_display_name = InterfaceCallProperty
    get_description = InterfaceCallProperty
    get_author_name = InterfaceCallProperty
    get_author_copyright = InterfaceCallProperty
    get_created_date = InterfaceCallProperty
    get_feed_extras = InterfaceCallProperty

class ProfileEmailAddressViewer:
    email_address = InterfaceReadProperty


class ProfileHomeViewer:
    home = InterfaceReadProperty

class ProfileWorkViewer:
    work = InterfaceReadProperty

class ProfileMobileViewer:
    mobile = InterfaceReadProperty

class ProfileFaxViewer:
    fax = InterfaceReadProperty

class ProfileAddressViewer:
    address = InterfaceReadProperty
    post_or_zip = InterfaceReadProperty

class ProfileSkypeViewer:
    skype_id = InterfaceReadProperty

class ProfileSipViewer:
    sip_id = InterfaceReadProperty

class ProfileEditor: 
    pk = InterfaceReadProperty
    about = InterfaceWriteProperty
    place = InterfaceWriteProperty
    website = InterfaceWriteProperty

    organisation = InterfaceWriteProperty
    role = InterfaceWriteProperty

    status = InterfaceWriteProperty

    address = InterfaceWriteProperty
    country = InterfaceWriteProperty
    post_or_zip = InterfaceWriteProperty
    mobile = InterfaceWriteProperty
    work = InterfaceWriteProperty
    home = InterfaceWriteProperty
    fax = InterfaceWriteProperty
    email_address = InterfaceWriteProperty
    address = InterfaceWriteProperty
    skype_id = InterfaceWriteProperty
    sip_id = InterfaceWriteProperty
    homeplace = InterfaceWriteProperty
    homehub = InterfaceWriteProperty

    first_name = InterfaceWriteProperty
    last_name = InterfaceWriteProperty

    cc_messages_to_email = InterfaceWriteProperty
    change_avatar = InterfaceCallProperty

from apps.plus_permissions.models import add_type_to_interface_map

ProfileInterfaces = {'Viewer': ProfileViewer,
                     'Editor': ProfileEditor,
                     'EmailAddressViewer' : ProfileEmailAddressViewer,
                     'HomeViewer' : ProfileHomeViewer,
                     'WorkViewer' : ProfileWorkViewer,
                     'MobileViewer' : ProfileMobileViewer,
                     'FaxViewer' : ProfileFaxViewer,
                     'AddressViewer' : ProfileAddressViewer,
                     'SkypeViewer' : ProfileSkypeViewer,
                     'SipViewer' : ProfileSipViewer}


add_type_to_interface_map(Profile, ProfileInterfaces)

SliderOptions = {'InterfaceOrder':['Viewer'], 'InterfaceLabels':{'Viewer':'View', 'Editor':'Edit'}}
SetSliderOptions(Profile, SliderOptions) 





