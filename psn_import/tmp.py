from apps.plus_resources.models import Resource
from apps.plus_groups.models import TgGroup
from apps.plus_tags.models import Tag, get_tags

import ipdb
res = Resource.objects.all()[0]

ipdb.set_trace()

res =  Resource.objects.all()
print res
counts = {'true':0, 'false':0}
for r in res : 
    print r, r.title.encode('utf-8'), r.created_by, r.stub
    if r.stub == False :
        counts['false']=counts['false']+1
    else :
        counts['true'] = counts['true']+1

print counts
