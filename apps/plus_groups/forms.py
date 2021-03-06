from datetime import datetime, timedelta
from django.contrib.contenttypes.models import ContentType
from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.hashcompat import sha_constructor
from django.utils.translation import ugettext_lazy as _, ugettext

from django.contrib.sites.models import Site
from django.contrib.auth.models import User


from apps.plus_groups.models import TgGroup, Location

from apps.plus_lib.utils import HTMLField, title_to_name, title_validation_regex

from django.conf import settings
from apps.plus_permissions.default_agents import get_or_create_root_location

from django.core.urlresolvers import reverse




PERMISSION_OPTIONS = (
    (u'public', u'Public'),
    (u'open', u'Open'),
    (u'invite', u'Invite'),
    (u'private', u'Private'),
)
CREATE_INTERFACES = (
    (u"CreateWikiPage", u"CreateWikiPage"),
    (u"CreateResource", u"CreateResource"), 
    (u"CreateNews", u"CreateNews"),
    (u"CreateEvent", u"CreateEvent")
)

reverse_lookup_dict = {'WikiPage': ['Page', 'view_WikiPage'],
                       'Resource': ['Upload', 'view_Resource']}

class AddContentForm(forms.Form):

    title = forms.CharField(max_length=100)
    current_app = forms.CharField(max_length=100)
    group = forms.IntegerField()
    create_iface = forms.ChoiceField(choices=CREATE_INTERFACES)
        #ensure name is unique for group and type
    def clean(self):
    
        self.cleaned_data['name'] = title_to_name(self.cleaned_data['title'])
        if not self.cleaned_data['name'] :
            self._errors['title']=_('Title must include alphabetic and / or numeric characters.')

        if self._errors:
            return self.cleaned_data

        self.cleaned_data['type_string'] = self.cleaned_data['create_iface'].split('Create')[1]
        cls = ContentType.objects.get(model=self.cleaned_data['type_string'].lower()).model_class()
        group = TgGroup.objects.get(id=self.cleaned_data['group'])
        validate_name_url(cls, group, self)
        return self.cleaned_data
    



def validate_name_url(cls, group, form):
    try:
        obj = cls.objects.get(name=form.cleaned_data['name'], in_agent=group.get_ref(), stub=False)
        type_label, lookup_string = reverse_lookup_dict[cls.__name__]
        existing_url = reverse(form.cleaned_data['current_app'] + ':' + lookup_string, args=[group.id, form.cleaned_data['name']])
        form._errors['title'] = _("There is already a <em>%s</em> in %s called <a href='%s'>%s</a>. Please choose a different title.") %(type_label, group.display_name.capitalize(), existing_url, form.cleaned_data['title'])
    except cls.DoesNotExist:
        pass


class TgGroupForm(forms.Form):
    
    name = forms.CharField(max_length=60)
    group_type = forms.ChoiceField(choices=settings.GROUP_TYPES)
    description = HTMLField()

    display_name = forms.CharField()
    address = forms.CharField(required=False)
    location = forms.CharField(required=False)
    permissions_set = forms.ChoiceField(choices=PERMISSION_OPTIONS)

    is_hub = forms.CharField()
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if not title_validation_regex().match(name) :
            raise forms.ValidationError(_("The name you have entered contains forbidden characters"))
        group_name=title_to_name(name)
        if TgGroup.objects.filter(group_name=group_name):
            raise forms.ValidationError(_("We already have a group with this name."))

        self.cleaned_data['display_name'] = name
        self.cleaned_data['group_name'] = group_name
        return group_name


    def clean_is_hub(self) :
        if self.cleaned_data['is_hub'] == 'True' : 
            self.cleaned_data['is_hub'] = True
        else :
            self.cleaned_data['is_hub'] = False
        return self.cleaned_data['is_hub']

    
    def save(self, user, site):

        if not self.cleaned_data['is_hub'] :
            place = get_or_create_root_location()
            group = site.create_TgGroup(
                group_name=self.cleaned_data['group_name'],
                display_name=self.cleaned_data['display_name'],
                group_type = self.cleaned_data['group_type'],
                level = 'member',
                user = user,
                description = self.cleaned_data['description'],
                permission_prototype = self.cleaned_data['permissions_set'],
                place = place,
                )
        else :
            group = site.create_hub(
                location_name = self.cleaned_data['display_name'], # not location, 
                group_name=self.cleaned_data['group_name'],
                display_name=self.cleaned_data['display_name'],
                group_type = self.cleaned_data['group_type'],
                level = 'member',
                user = user,
                description = self.cleaned_data['description'],
                address = self.cleaned_data['address'],
                permission_prototype = self.cleaned_data['permissions_set'],
                )

        group.save()
        return group
    
    
    
class TgGroupMemberInviteForm(forms.Form) :
    plain_text = forms.CharField()
    special_message = forms.CharField(required=False)

    
    def clean_plain_text(self) :
        from apps.plus_groups.models import infer_invited, InvalidInvited
        tt = self.cleaned_data['plain_text']
        try:
            invited = infer_invited(tt)
            self.cleaned_data['invited'] = invited
            return invited
        except InvalidInvited, ii :
            # so it's neither a known user or valid email address, not much more we can do
            raise forms.ValidationError(_('Not recognised as either existing username or an email'))


class TgGroupMessageMemberForm(forms.Form) :
    message_header = forms.CharField()
    message_body = forms.CharField()
  
