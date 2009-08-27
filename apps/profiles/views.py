from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.db import transaction
from django.utils import simplejson

from friends.forms import InviteFriendForm
from friends.models import FriendshipInvitation, Friendship

from microblogging.models import Following

from profiles.models import Profile, HostInfo
from profiles.forms import ProfileForm, HostInfoForm

from avatar.templatetags.avatar_tags import avatar

from apps.plus_lib.models import DisplayStatus, add_edit_key

from apps.plus_permissions.models import SecurityTag, has_access
from apps.plus_permissions.interfaces import PlusPermissionsNoAccessException, PlusPermissionsReadOnlyException, secure_wrap, TemplateSecureWrapper
from apps.plus_permissions.default_agents import get_anon_user

from django.contrib.auth.decorators import login_required

from apps.plus_tags.models import  tag_add, tag_delete, get_tags, tag_autocomplete

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


# need 
add_edit_key(User)
add_edit_key(Profile)

add_edit_key(HostInfo)

#from gravatar.templatetags.gravatar import gravatar as avatar

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

def profiles(request, template_name="profiles/profiles.html"):
    users = User.objects.all().order_by("-date_joined")

    users = users.filter(~Q(username='admin')).filter(~Q(username='anon'))

    search_terms = request.GET.get('search', '')
    order = request.GET.get('order')
    if not order:
        order = 'date'
    if search_terms:
        users = users.filter(username__icontains=search_terms)
    if order == 'date':
        users = users.order_by("-date_joined")
    elif order == 'name':
        users = users.order_by("username")
    return render_to_response(template_name, {
        'users':users,
        'order' : order,
        'search_terms' : search_terms
    }, context_instance=RequestContext(request))

def profile(request, username, template_name="profiles/profile.html"):
    other_user = get_object_or_404(User, username=username)
    other_user.save()
    
    p = other_user.get_profile()
    p.save()

    request.user.message_set.create(message="this is a test message")

    if request.user.is_authenticated():

        is_friend = Friendship.objects.are_friends(request.user, other_user)
        is_following = Following.objects.is_following(request.user, other_user)
        other_friends = Friendship.objects.friends_for_user(other_user)
        if request.user == other_user:
            is_me = True
        else:
            is_me = False
    else:
        other_friends = []
        is_friend = False
        is_me = False
        is_following = False
    
    if is_friend:
        invite_form = None
        previous_invitations_to = None
        previous_invitations_from = None
    else:
        if request.user.is_authenticated() and request.method == "POST":
            if request.POST["action"] == "invite":
                invite_form = InviteFriendForm(request.user, request.POST)
                if invite_form.is_valid():
                    invite_form.save()
            else:
                invite_form = InviteFriendForm(request.user, {
                    'to_user': username,
                    'message': ugettext("Let's be friends!"),
                })
                if request.POST["action"] == "accept": # @@@ perhaps the form should just post to friends and be redirected here
                    invitation_id = request.POST["invitation"]
                    try:
                        invitation = FriendshipInvitation.objects.get(id=invitation_id)
                        if invitation.to_user == request.user:
                            invitation.accept()
                            request.user.message_set.create(message=_("You have accepted the friendship request from %(from_user)s") % {'from_user': invitation.from_user})
                            is_friend = True
                            other_friends = Friendship.objects.friends_for_user(other_user)
                    except FriendshipInvitation.DoesNotExist:
                        pass
        else:
            invite_form = InviteFriendForm(request.user, {
                'to_user': username,
                'message': ugettext("Let's be friends!"),
            })
    previous_invitations_to = FriendshipInvitation.objects.filter(to_user=other_user, from_user=request.user)
    previous_invitations_from = FriendshipInvitation.objects.filter(to_user=request.user, from_user=other_user)
    
    if is_me:
        if request.method == "POST":
            if request.POST["action"] == "update":
                profile_form = ProfileForm(request.POST, instance=other_user.get_profile())
                if profile_form.is_valid():
                    profile = profile_form.save(commit=False)
                    profile.user = other_user
                    profile.save()
            else:
                profile_form = ProfileForm(instance=other_user.get_profile())
        else:
            profile_form = ProfileForm(instance=other_user.get_profile())
    else:
        profile_form = None

    interests = get_tags(tagged = other_user.get_profile(), tagger = other_user, tag_type = 'interest')
    skills = get_tags(tagged = other_user.get_profile(), tagger = other_user, tag_type = 'skill')
    needs = get_tags(tagged = other_user.get_profile(), tagger = other_user, tag_type = 'need')

    profile = other_user.get_profile()
    user = request.user

    if not user.is_authenticated():
        user = get_anon_user()

    profile = secure_wrap(profile, user)

    dummy_status = DisplayStatus("Dummy Status"," about 3 hours ago")
    
    profile = TemplateSecureWrapper(secure_wrap(profile, user))

    return render_to_response(template_name, {
            "profile_form": profile_form,
            "is_me": is_me,
            "is_friend": is_friend,
            "is_following": is_following,
            "other_user": other_user,
            "profile":profile,
            "other_friends": other_friends,
            "invite_form": invite_form,
            "previous_invitations_to": previous_invitations_to,
            "previous_invitations_from": previous_invitations_from,
            "head_title" : "%s" % other_user.get_profile().name,
            "head_title_status" : dummy_status,
            "host_info" : other_user.get_profile().get_host_info(),
            "skills" : skills,
            "needs" : needs,
            "interests" : interests,
            }, context_instance=RequestContext(request))



def our_profile_permission_test(fn) :
    """ Trying to put our permission testing into a decorator """
    def our_fn(request,username,*args,**kwargs) :
        other_user = get_object_or_404(User,username=username)
        profile = other_user.get_profile()
        if not has_access(request.user,profile,'Profile.Viewer') :
            return HttpResponse("You don't have permission to do that to %s, you are %s" % (username,request.user),status=401)
        else :
            return fn(request, username, *args, **kwargs)
    return our_fn

def name_to_profile(fn):
    def our_fn(request,username,*args,**kwargs):
        other_user = get_object_or_404(User,username=username)
        return fn(request, other_user.get_profile(), *args, **kwargs)
    return our_fn
    
    

@login_required
@transaction.commit_on_success
def update_profile_form(request,username) :
    """ Get a prefilled basic form for the profile """
    other_user = get_object_or_404(User,username=username)
    p = other_user.get_profile()
    if not has_access(request.user,p,'Profile.Viewer') :
        raise PlusPermissionsNoAccessException(Profile,p.pk,'update_profile_form')
    else :
        profile_form = ProfileForm(request.POST, p)


from apps.plus_permissions.permissionable import create_reference
from apps.plus_permissions.types.User import setup_user_security

@login_required
def patch_in_profiles(request):
    """create profiles for all users who don't have them
    """
    users = User.objects.filter(profile__isnull=True)
    no_of_users = users.count()

    for user in users:
        create_reference(User, user)
        setup_user_security(user)
        user.create_Profile(user, user=user)
        
    return HttpResponse("patched %s users to have profiles" % str(no_of_users))


@login_required
@transaction.commit_on_success
def profile_field(request,username,classname,fieldname,*args,**kwargs) :
    """ Get the value of one field from the user profile, so we can write an ajaxy editor """
    print "In profile_field"
    print "username %s, classname %s, fieldname %s" % (username,classname,fieldname)
    other_user = get_object_or_404(User,username=username)
    p = other_user.get_profile()
    if not has_access(request.user,p,'Profile.Viewer') :
        return HttpResponse("You aren't authorized to access %s in %s for %s. You are %s" % (fieldname,classname,username,request.user),status=401)
    else :
        if classname == 'Profile' :
            return one_model_field(request,p,ProfileForm,fieldname, kwargs.get('default', ''),[p.user])
        elif classname == 'HostInfo' :
            return one_model_field(request,p.get_host_info(),HostInfoForm,fieldname, kwargs.get('default', ''),[p.user])


def one_model_field(request, object, formClass, fieldname, default, other_objects=None) :
    val = getattr(object, fieldname)
    if not request.POST:
        return HttpResponse("%s" % val, mimetype="text/plain")

    field_validator = formClass.base_fields[fieldname]
    new_val = request.POST['value']
    try:
        field_validator.clean(new_val)
    except ValidationError, e:
        return HttpResponse('%s' % e, status=500)

    try:
        setattr(object, fieldname, new_val)
        object.save()
        if other_objects :
            for o in other_objects :
                o.save()
    except Exception, e :
        return HttpResponse('%s' % e, status=500)
    new_val = new_val and new_val or default
    return HttpResponse("%s" % new_val, mimetype='text/plain')

@login_required
def get_main_permission_sliders(request,username):
    """XXX NEEDS REWRITING"""
    return HttpResponse(MAKE_MY_JSON_FOR_THIS, mimetype='text/plain')

def content_object(c_type, c_id) :
    a_type = ContentType.objects.get_for_id(c_type)
    return a_type.get_object_for_this_type(pk=c_id)



@login_required
def update_main_permission_sliders(request,username) :
    """XXX REWRITE"""
    pass


