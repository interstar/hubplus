# tag add url

# -- side bar clouds and searches a) in group/hubs/members search groups/hubs/members only, b) in group search resources

# tag filtering on group, hub, member, resources
# -- integrate explore_filtered with explore index 
# -- if results set empty, include tag cloud
# group search, hash tag position

# fulltext search b) - write template
#                    - reindex
# 
# ordering



# -- create a form to validate search term and order
# -- re-write load_all to return a sql query object

# Later
# search different sites from one index server using "site" attribute of SearchQuerySet 
# -- listing of members / hosts of a group 
# -- Optimisation - Implement an indexing queuing/batching, to avoid solr "merging" churn when there are a lot of writes
# -- Optimisation - Implement select_related type functionality for GenericForeignKey relationships, and in particular GenericReference's obj attribute

from django.conf.urls.defaults import *

urlpatterns = patterns('',
                       url(r'^$', 'plus_explore.views.index', name='explore'),
                       url(r'^goto_tag/$', 'plus_explore.views.goto_tag', name='goto_tag'),
                       url(r'^(?P<tag_string>[ \w\+\._-]*)/$', 'plus_explore.views.filter', name='explore_filtered'),  
)