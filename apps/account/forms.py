
import re

from django import forms
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.encoding import smart_unicode
from django.utils.hashcompat import sha_constructor

#from misc.utils import get_send_mail
#send_mail = get_send_mail()
from django.core.mail import send_mail
from django.core.urlresolvers import reverse


from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from emailconfirmation.models import EmailAddress
from account.models import Account

from timezones.forms import TimeZoneField

from account.models import PasswordReset

from plus_contacts.models import Contact, Application
from plus_permissions.default_agents import get_site, get_admin_user

from plus_groups.models import TgGroup
from django.utils.translation import ugettext, ugettext_lazy as _


alnum_re = re.compile(r'^[\w\s]+$')
ascii_re = re.compile(r'^[a-z0-9A-Z\.]+$')

class LoginForm(forms.Form):

    username = forms.CharField(label=_("Username"), max_length=30, widget=forms.TextInput())
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(render_value=False))
    remember = forms.BooleanField(label=_("Remember Me"), help_text=_("If checked you will stay logged in for 3 weeks"), required=False)

    user = None

    def clean(self):
        if self._errors:
            return
        user = authenticate(username=self.cleaned_data["username"], password=self.cleaned_data["password"])
        if user:
            if user.is_active:
                self.user = user
            else:
                raise forms.ValidationError(_("This account is currently inactive."))
        else:
            raise forms.ValidationError(_("The username and/or password you specified are not correct."))
        return self.cleaned_data

    def login(self, request):

        if self.is_valid():
            login(request, self.user)
            request.user.message_set.create(message=ugettext(u"Successfully logged in as %(username)s.") % {'username': self.user.username})
            if self.cleaned_data['remember']:
                request.session.set_expiry(60 * 60 * 24 * 7 * 3)
            else:
                request.session.set_expiry(0)
            return True
        return False


class SignupForm(forms.Form):

    username = forms.CharField(label=_("Username"), max_length=30, widget=forms.TextInput())
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput(render_value=False))
    password2 = forms.CharField(label=_("Password (again)"), widget=forms.PasswordInput(render_value=False))
    email = forms.EmailField(label=_("Email (optional)"), required=False, widget=forms.TextInput())
    confirmation_key = forms.CharField(max_length=40, required=False, widget=forms.HiddenInput())

    def clean_username(self):
        if not ascii_re.search(self.cleaned_data["username"]):
            raise forms.ValidationError(_("Usernames can only contain letters, numbers and underscores."))
        try:
            user = User.objects.get(username__iexact=self.cleaned_data["username"])
        except User.DoesNotExist:
            return self.cleaned_data["username"]
        raise forms.ValidationError(_("This username is already taken. Please choose another."))

    def clean(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data



class OpenIDSignupForm(forms.Form):
    username = forms.CharField(label="Username", max_length=30, widget=forms.TextInput())
    email = forms.EmailField(label="Email (optional)", required=False, widget=forms.TextInput())
    
    def __init__(self, *args, **kwargs):
        # @@@ this method needs to be compared to django-openid's form.
        
        # Remember provided (validated!) OpenID to attach it to the new user later.
        self.openid = kwargs.pop("openid")
        # TODO: do something with this?
        reserved_usernames = kwargs.pop("reserved_usernames")
        no_duplicate_emails = kwargs.pop("no_duplicate_emails")
        super(OpenIDSignupForm, self).__init__(*args, **kwargs)
    
    def clean_username(self):
        if not alnum_re.search(self.cleaned_data["username"]):
            raise forms.ValidationError(u"Usernames can only contain letters, numbers and underscores.")
        try:
            user = User.objects.get(username__iexact=self.cleaned_data["username"])
        except User.DoesNotExist:
            return self.cleaned_data["username"]
        raise forms.ValidationError(u"This username is already taken. Please choose another.")

    def save(self):
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        new_user = User.objects.create_user(username, "", "!")

        if email:
            new_user.message_set.create(message="Confirmation email sent to %s" % email)
            EmailAddress.objects.add_email(new_user, email)

        if self.openid:
            # Associate openid with the new account.
            new_user.openids.create(openid = self.openid)
        return new_user


class UserForm(forms.Form):

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(UserForm, self).__init__(*args, **kwargs)

class AccountForm(UserForm):

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        try:
            self.account = Account.objects.get(user=self.user)
        except Account.DoesNotExist:
            self.account = Account(user=self.user)


class AddEmailForm(UserForm):

    email = forms.EmailField(label=_("Email"), required=True, widget=forms.TextInput(attrs={'size':'30'}))

    def clean_email(self):
        try:
            EmailAddress.objects.get(user=self.user, email=self.cleaned_data["email"])
        except EmailAddress.DoesNotExist:
            return self.cleaned_data["email"]
        raise forms.ValidationError(_("This email address already associated with this account."))

    def save(self):
        self.user.message_set.create(message=ugettext(u"Confirmation email sent to %(email)s") % {'email': self.cleaned_data["email"]})
        return EmailAddress.objects.add_email(self.user, self.cleaned_data["email"])


class ChangePasswordForm(UserForm):

    oldpassword = forms.CharField(label=_("Current Password"), widget=forms.PasswordInput(render_value=False))
    password1 = forms.CharField(label=_("New Password"), widget=forms.PasswordInput(render_value=False))
    password2 = forms.CharField(label=_("New Password (again)"), widget=forms.PasswordInput(render_value=False))

    def clean_oldpassword(self):
        if not self.user.check_password(self.cleaned_data.get("oldpassword")):
            raise forms.ValidationError(_("Please type your current password."))
        return self.cleaned_data["oldpassword"]

    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]

    def save(self):
        self.user.set_password(self.cleaned_data['password1'])
        self.user.save()
        self.user.message_set.create(message=ugettext(u"Password successfully changed."))


class SetPasswordForm(UserForm):
    
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput(render_value=False))
    password2 = forms.CharField(label=_("Password (again)"), widget=forms.PasswordInput(render_value=False))
    
    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]
    
    def save(self):
        self.user.set_password(self.cleaned_data["password1"])
        self.user.save()
        self.user.message_set.create(message=ugettext(u"Password successfully set."))

class ResetPasswordForm(forms.Form):
    
    email = forms.EmailField(label=_("Email"), required=True, widget=forms.TextInput(attrs={'size':'30'}))

    def clean_email(self):
        if User.objects.filter(email_address=self.cleaned_data["email"]).count() == 0 :
            raise forms.ValidationError(_("Email address not recognised for any user account"))
        return self.cleaned_data["email"]

    def save(self, domain):

        for user in User.objects.filter(email_address__iexact=self.cleaned_data["email"]):
            temp_key = sha_constructor("%s%s%s" % (
                settings.SECRET_KEY,
                user.email,
                settings.SECRET_KEY,
            )).hexdigest()
            
            # save it to the password reset model
            try:
                password_reset = PasswordReset.objects.get(user=user,temp_key=temp_key, reset=False) 
            except PasswordReset.DoesNotExist:
                password_reset = PasswordReset(user=user, temp_key=temp_key)
                password_reset.save()
            
            #send the password reset email
            subject = _("Password reset email sent")
            link = 'http://'+domain+reverse('acct_passwd_reset_key',args=(temp_key,))
            message = _(settings.PASSWORD_RESET_TEMPLATE) % {
                "display_name" : user.get_display_name(),
                "username": user.username,
                "link" : link,
            }
            send_mail(subject, message, settings.SUPPORT_EMAIL, [user.email_address],fail_silently=False)
        return self.cleaned_data["email"]
        
class ResetPasswordKeyForm(forms.Form):
    
    password1 = forms.CharField(label=_("New Password"), widget=forms.PasswordInput(render_value=False))
    password2 = forms.CharField(label=_("New Password (again)"), widget=forms.PasswordInput(render_value=False))
    temp_key = forms.CharField(widget=forms.HiddenInput)

    def clean_temp_key(self):

        temp_key = self.cleaned_data.get("temp_key")
        if not PasswordReset.objects.filter(temp_key=temp_key, reset=False).count() == 1:
            raise forms.ValidationError(_("Temporary key is invalid."))
        return temp_key

    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]

    def save(self):
        # get the password_reset object
        temp_key = self.cleaned_data.get("temp_key")
        password_resets = PasswordReset.objects.filter(temp_key__exact=temp_key)
        if password_resets :
            password_reset = password_resets[0]
        
        # now set the new user password
        user = User.objects.get(passwordreset__exact=password_reset)
        user.set_password(self.cleaned_data["password1"])
        user.save()
        user.message_set.create(message=ugettext(u"Password successfully changed."))
        
        # change all the password reset records to this person to be true.
        for password_reset in PasswordReset.objects.filter(user=user):
            password_reset.reset = True
            password_reset.save()
            

class ChangeTimezoneForm(AccountForm):

    timezone = TimeZoneField(label=_("Timezone"), required=True)

    def __init__(self, *args, **kwargs):
        super(ChangeTimezoneForm, self).__init__(*args, **kwargs)
        self.initial.update({"timezone": self.account.timezone})

    def save(self):
        self.account.timezone = self.cleaned_data["timezone"]
        self.account.save()
        self.user.message_set.create(message=ugettext(u"Timezone successfully updated."))

class ChangeLanguageForm(AccountForm):

    language = forms.ChoiceField(label=_("Language"), required=True, choices=settings.LANGUAGES)

    def __init__(self, *args, **kwargs):
        super(ChangeLanguageForm, self).__init__(*args, **kwargs)
        self.initial.update({"language": self.account.language})

    def save(self):
        self.account.language = self.cleaned_data["language"]
        self.account.save()
        self.user.message_set.create(message=ugettext(u"Language successfully updated."))




# @@@ these should somehow be moved out of account or at least out of this module

from account.models import OtherServiceInfo, other_service, update_other_services

class TwitterForm(UserForm):
    username = forms.CharField(label=_("Username"), required=True)
    password = forms.CharField(label=_("Password"), required=True,
                               widget=forms.PasswordInput(render_value=False))

    def __init__(self, *args, **kwargs):
        super(TwitterForm, self).__init__(*args, **kwargs)
        self.initial.update({"username": other_service(self.user, "twitter_user")})

    def save(self):
        from microblogging.utils import get_twitter_password
        update_other_services(self.user,
            twitter_user = self.cleaned_data['username'],
            twitter_password = get_twitter_password(settings.SECRET_KEY, self.cleaned_data['password']),
        )
        self.user.message_set.create(message=ugettext(u"Successfully authenticated."))


# hubplus alternatives
from apps.plus_permissions.default_agents import get_all_members_group
from apps.plus_lib.countryfield import COUNTRIES
class HubPlusApplicationForm(forms.Form):

    #username = forms.RegexField(regex=ascii_re, label=_("Username"), max_length=30, widget=forms.TextInput(), error_messages={'invalid': 'Username must only contain a-z, 0-9 and "."'})
    first_name = forms.RegexField(regex=alnum_re, label=_("First Name"), max_length=30, widget=forms.TextInput(), error_messages={'invalid': 'Name must only contain alphabetic character'})
    last_name = forms.RegexField(regex=alnum_re, label=_("Last Name"), max_length=30, widget=forms.TextInput(), error_messages={'invalid': 'Name must only contain alphabetic character'})
    email_address = forms.EmailField(label=_("Email (required)"), required=True, widget=forms.TextInput())

    organisation = forms.CharField(label=_("Organisation"), required=False, widget=forms.TextInput())
    address = forms.CharField(label=_("Address"), required=True, widget=forms.TextInput())
    country = forms.ChoiceField(label=_("Country"), required=True, widget=forms.Select(), choices=COUNTRIES)
    post_or_zip = forms.CharField(label=_("Zip/Postcode"), required=False, widget=forms.TextInput())
    about_and_why = forms.CharField(
        label=_("Tell us a bit about yourself what you do and why you're interested in the Hub?"),
        required=True, widget=forms.TextInput()
        )
    find_out = forms.CharField(label=_("How did you find out about the Hub?"), required=True, widget=forms.TextInput())
    group = forms.CharField(label=_("A group you'd like to join (Optional)"), required=False, widget=forms.TextInput())

    #def clean_username(self):
    #    username = self.cleaned_data["username"].lower()
    #    users = User.objects.filter(username__iexact=username)
    #    contacts = Contact.objects.filter(username__iexact=username)
    #    if users or contacts:
    #        raise forms.ValidationError(_("This username is already taken. Please choose another."))
    #    else :
    #        return self.cleaned_data["username"]


    def clean_group(self) :
        if self.cleaned_data['group'] == '' :
            return None
        groups = TgGroup.objects.filter(group_name=self.cleaned_data['group'])
        if groups :
            return groups[0]
        else :
            raise forms.ValidationError(_("There is no group called %s"%self.cleaned_data['group']))
                

    def clean_email_address(self) :
        email = self.cleaned_data['email_address']
        users = User.objects.filter(email_address=email)
        if users:
            raise forms.ValidationError(_("There is already a user with that email address. Please choose another."))
        return email

    def clean(self):
        return self.cleaned_data

    def save(self, user):
        site = get_site(get_admin_user())
        about_and_why = self.cleaned_data.pop("about_and_why")
 
        group = self.cleaned_data.pop('group')
        members_group = get_all_members_group()

        had_group = True
        if not group:
            had_group = False
            group = members_group

        contact = group.create_Contact(user, **self.cleaned_data)
        site_application = members_group.apply(user, 
                                               applicant=contact,
                                               about_and_why=about_and_why)

        if had_group: 
            group.apply(user, 
                        applicant=contact,
                        about_and_why=about_and_why)

        return group
        


class InviteForm(forms.Form):
    first_name = forms.RegexField(regex=alnum_re, label=_("First Name"), max_length=30, widget=forms.TextInput(), error_messages={'invalid': 'Name must only contain alphabetic character'})
    last_name = forms.RegexField(regex=alnum_re, label=_("Last Name"), max_length=30, widget=forms.TextInput(), error_messages={'invalid': 'Name must only contain alphabetic character'})
    email_address = forms.EmailField(label=_("Email (required)"), required=True, widget=forms.TextInput())
    message = forms.CharField(label=_("Invite Message"), required=True, widget=forms.TextInput())

    group = forms.CharField(label=_("A group you'd like to join (Optional)"), required=False, widget=forms.TextInput())

    def clean_group(self) :
        if self.cleaned_data['group'] == '' :
            return None
        groups = TgGroup.objects.filter(group_name=self.cleaned_data['group'])
        if groups :
            return groups[0]
        else :
            raise forms.ValidationError(_("There is no group called %s"%self.cleaned_data['group']))

    def clean_email_address(self) :
        email = self.cleaned_data['email_address']
        users = User.objects.filter(email_address=email)
        if users:
            raise forms.ValidationError(_("There is already a user with that email address. Please choose another."))
        return email

    def clean(self):
        return self.cleaned_data

    def save(self, user):
        group = self.cleaned_data.pop('group')
        members_group = get_all_members_group()
        if not group:
            group = members_group
        invitee = group.create_Contact(user, 
                                       email_address = self.cleaned_data['email_address'], 
                                       first_name=self.cleaned_data['first_name'],
                                       last_name=self.cleaned_data['last_name'])

        group.invite_member(user, 
                            invitee,
                            message=self.cleaned_data['message'])
        if not group:
            group = members_group
        return group
    

class SettingsForm(forms.Form) :
    cc_email = forms.BooleanField(required=False)
    email = forms.EmailField(required=False)

    first_name = forms.RegexField(regex=alnum_re, label=_("First Name"), max_length=30, widget=forms.TextInput(), 
                                  error_messages={'invalid': 'Name must only contain alphabetic character'})
    last_name = forms.RegexField(regex=alnum_re, label=_("Last Name"), max_length=30, widget=forms.TextInput(), 
                                 error_messages={'invalid': 'Name must only contain alphabetic character'})


    def clean_email(self) :
        email = self.cleaned_data['email']
        if not email :
            raise forms.ValidationError(_("Email address is empty."))

        try :
            self.user
            # someone has injected a user in from outside,
            # so we can validate whether the email address belongs to this user
            user = self.user
        except :
            user = None

        if user :
            users = User.objects.filter(email_address=email)
            if users:
                if users[0].username == self.user.username :
                    return email
                raise forms.ValidationError(_("There is already a user with that email address. Please choose another."))


        return email
