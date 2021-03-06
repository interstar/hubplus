
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # XXX the following autocomplete is deprecated, need to get rid of it for upgrading to later django
    url(r'^username_autocomplete/$', 'misc.views.username_autocomplete_friends', name='profile_username_autocomplete'),

    url(r'^ajax_hub_list/(?P<username>[\w\._-]+)/$', 'plus_groups.views.ajax_hub_list', name='ajax_hub_list_for_user'),
    url(r'^ajax_hub_list/$', 'plus_groups.views.ajax_hub_list', name='ajax_hub_list'),

    url(r'^$', 'profiles.views.profiles', name='profile_list'),
    url(r'^tags/(?P<tag_string>[\w\+\. _-]+)/$', 'profiles.views.profiles', name='profile_list_tag'),

    url(r'^(?P<username>[\w\._-]+)/$', 'profiles.views.profile', name='profile_detail'),

    url(r'^(?P<username>[\w\._-]+)/rss/$', 'plus_feed.views.rss_of_user', name='profile_feed'),

    url(r'^(?P<resource_id>[\w\._-]+)/field/(?P<classname>[\w_]+)/(?P<fieldname>[\w_]+)/(?P<default>[\w_]*)$','profiles.views.profile_field',{},name='profile_field'),
    url(r'^(?P<username>[\w\._-]+)/get_main_permission_sliders/','profiles.views.get_main_permission_sliders',name='[profile_get_main_permission_sliders'),
    url(r'^(?P<username>[\w\._-]+)/update_main_permission_sliders/','profiles.views.update_main_permission_sliders',name='[profile_get_main_permission_sliders'),
    url(r'^autocomplete_user_or_full_name', 'profiles.views.autocomplete_user_or_full_name', name='autocomplete_user_or_full_name'),


)
