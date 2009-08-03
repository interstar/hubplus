from django.db import models

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django.contrib.auth.models import User
from apps.hubspace_compatibility.models import TgGroup, Location

import pickle
import simplejson

import datetime
import ipdb

class PlusPermissionsNoAccessException(Exception):
    def __init__(self,cls,id,msg) :
        self.cls=cls
        self.id=id
        self.msg=msg
        self.silent_variable_failure = True

class PlusPermissionsReadOnlyException(Exception) : 
    def __init__(self,cls,msg) :
        self.cls = cls
        self.msg = msg

class Interface :

    @classmethod
    def delete(self) :
        return False

    @classmethod
    def has_property_name_and_class(self,name,cls) :
        """Does this object have a property of name 'name' and class 'cls'?"""
        for k,v in self.__dict__.iteritems() :
            if k == name and v.__class__ == cls :
                return True
        return False

    @classmethod
    def has_write(self,name) :
        return self.has_property_name_and_class(name,InterfaceWriteProperty)

    @classmethod
    def has_read(self,name) :
        return self.has_property_name_and_class(name,InterfaceReadProperty)
        
    @classmethod
    def get_id(cls) : 
        raise UseSubclassException(Interface,'You need a subclass of Interface that implements its get_id')
        
    @classmethod
    def make_slider_for(cls,resource,options,default_agent,selected,creator) :
        s = Slider(
            tag_name='%s slider'%cls.__name__,
            resource=resource,
            interface_id=cls.get_id(),
            default_agent=default_agent,
            creator=creator,
            options=options
        )
        s.set_current_option(selected)
        return s



class NullInterface :
    """
    Empty interface, wraps models in a shell, which only lets explicitly named properties through
    """
    def __init__(self, inner) :
        self.__dict__['_inner'] = inner
        self.__dict__['_interfaces'] = []
        
        self.__dict__['_exceptions'] = [ # these always go through
            lambda x : x[0]=='_', # starts with _
            lambda x : x=='id',
        ]

    def get_inner(self) :
        return self.__dict__['_inner']

    def get_inner_class(self) :
        return self.get_inner().__class__

    def get_interfaces(self) :
        return self.__dict__['_interfaces']

    def load_interfaces_for(self,agent) :
        """Load interfaces for the wrapped inner content that are available to the agent"""
        ps = get_permission_system()
        resource = self.get_inner()
        cls = resource.__class__
        tif = ps.get_interface_factory()
        try :
            types = tif.get_type(cls)
        except :
            pm = ps.get_permission_manager(cls)
            pm.register_with_interface_factory(tif)
            types = tif.get_type(cls)
        for k,v in types.iteritems() :
            if ps.has_access(agent=agent,resource=resource,interface=ps.get_interface_id(self.get_inner().__class__,k)) :
                self.add_interface(v)


    def fold_interfaces(self, f,init) :
        for i in self.get_interfaces() :
            init = f(init,i)
        return init

    def delete(self) :
        """If any interface provides a delete method which returns True, we can delete the object"""
        if self.fold_interfaces(lambda a, i : a or i.delete(), False) :
            self.get_inner().delete()
        else :
            raise PlusPermissionsNoAccessException(self.get_inner_class(),'delete','trying to delete')

    def __getattr__(self,name) :
        for rule in self.__dict__['_exceptions'] :
            if rule(name) :
                return self.get_inner().__getattribute__(name)
        if self.fold_interfaces(lambda a, i : a or i.has_read(name),False) :
            return self.get_inner().__getattribute__(name)
        raise PlusPermissionsNoAccessException(self.get_inner_class(),name,'from __getattr__')

    def __setattr__(self,name,val) :
        if self.fold_interfaces(lambda a,i : a or i.has_write(name),False) :
            self.get_inner().__setattr__(name,val)
            return None      
        raise PlusPermissionsReadOnlyException(self.get_inner_class(),name)        

    def add_interface(self,interface) :
        self.get_interfaces().append(interface)

    def remove_interface(self,cls) :
        ifs = [i for i in self.get_interfaces() if i != cls]
        self.__dict__['_interfaces'] = ifs

    def save(self) :
        self.get_inner().save()

    def edit_key(self) :
        print "In edit key %s" % self.get_inner().edit_key()
        return self.get_inner().edit_key()


    def __str__(self) :
        return self.get_inner()
        
class InterfacePropertyBase(object) :
    def can_read(self) :
        return True
    def is_empty(self):
        return False

class InterfaceReadProperty(InterfacePropertyBase) :
    """ Add this to a NullInterface to allow a property to be readable"""
    def __init__(self,name) :
        self.name = name

    def can_write(self) :
        return False


class InterfaceWriteProperty(InterfacePropertyBase) :
    """ Add this to a NullInterface to allow a property to be writable """
    def __init__(self,name) :
        self.name = name

    def can_write(self) :
        return True


def strip(x) :
    """If x is really a Null interface, return the inner value, otherwise, return itself"""
    try : 
        return x.get_inner()
    except :
        return x

class InterfaceFactory :

    def __init__(self) :
        self.all = {}
        self.permission_managers = {}

    def add_type(self,cls) :
        if not self.all.has_key(cls.__name__) :
            self.all[cls.__name__] = {}

    def get_type(self,cls) :
        return self.all[cls.__name__]


    def add_interface(self,cls,name,interfaceClass) :
        self.add_type(cls)
        self.get_type(cls)[name] = interfaceClass


    def get_interface(self,cls,name) :
        return self.get_type(cls)[name]        

    def get_id(self,cls,name) : 
        return '%s.%s' % (cls.__name__,name)

    def add_permission_manager(self,cls,pm) :
        self.permission_managers[cls.__name__] = pm
        pm.register_with_interface_factory(self)

    def get_permission_manager(self,cls) : 
        return self.permission_managers[cls.__name__]


class DefaultAdmin(models.Model) :
    agent_content_type = models.ForeignKey(ContentType,related_name='default_admin_agent')
    agent_object_id = models.PositiveIntegerField()
    agent = generic.GenericForeignKey('agent_content_type', 'agent_object_id')

    resource_content_type = models.ForeignKey(ContentType,related_name='default_admin_resource')
    resource_object_id = models.PositiveIntegerField(null=True)
    resource = generic.GenericForeignKey('resource_content_type', 'resource_object_id')

def default_admin_for(resource) :
    ds = [x for x in DefaultAdmin.objects.all() if x.resource == resource]
    if len(ds) < 1 : 
        return None
    else :
        return ds[0].agentContentType.objects.get_for_model


class SecurityTagManager(models.Manager):
    def get_by_agent_and_resource_type_and_id(self, agent_type, agent_id, resource_type, resource_id) :
        return self.filter(agent_content_type=agent_type,
                           agent_object_id=agent_id,
                           resource_content_type=resource_type,
                           resource_object_id=resource_id)

 

    def is_in(self,options,agent) :
        a_type = ContentType.objects.get_for_model(agent)
        for (typ,id) in options :
            if typ == a_type and agent.id==id :
                return True

    def agent_list_filter(self,options,**kwargs) :
        return (t for t in self.filter(**kwargs) if self.is_in(options, t.agent))


    def kill_list(self,kill_list,resource_type, resource_id,interface) :
        for t in self.filter(interface=interface,resource_content_type=resource_type,resource_object_id=resource_id) :
            for (typ,id) in kill_list :
                if t.agent_content_type == typ and t.agent_object_id == id :
                    t.delete()


class SecurityTag(models.Model) :
    name = models.CharField(max_length='50') 
    agent_content_type = models.ForeignKey(ContentType,related_name='security_tag_agent')
    agent_object_id = models.PositiveIntegerField()
    agent = generic.GenericForeignKey('agent_content_type', 'agent_object_id')
 
    interface = models.CharField(max_length='50')

    resource_content_type = models.ForeignKey(ContentType,related_name='security_tag_resource')
    resource_object_id = models.PositiveIntegerField()
    resource = generic.GenericForeignKey('resource_content_type', 'resource_object_id')

    creator_content_type = models.ForeignKey(ContentType,related_name='security_tag_creator')
    creator_object_id = models.PositiveIntegerField()
    creator = generic.GenericForeignKey('creator_content_type', 'creator_object_id')


    objects = SecurityTagManager()

    def all_named(self) : 
        return (x for x in SecurityTag.objects.all() if x.name == self.name)

    def has_access(self,agent,resource,interface) :
        # NB : we have to loop through this explicitly rather than use some kind of ORM filter
        # because we're going to test our SecurityTag not just against THIS agent but 
        # the groups which the agent belongs to.
        for x in (x for x in SecurityTag.objects.all() if x.resource == resource and x.interface == interface) :
            if x.agent == get_permission_system().get_anon_group() : 
                # in other words, if this resource is matched with anyone, we don't have to test that user is in the "anyone" group
                return True
            if x.agent == agent : 
                return True
            if agent.is_member_of(x.agent) : 
                return True
        return False


    def get_resource_type(self) :
        return ContentType.objects.get_for_model(self.resource)

    def get_resource_id(self) :
        return self.resource.id

    def get_agent_type(self) :
        return ContentType.objects.get_for_model(self.agent)
    
    def get_agent_id(self) :
        return self.agent.id

    def __str__(self) :
        return """Agent : %s, Resource : %s, Interface : %s""" % (self.agent,self.resource,self.interface)




_ONLY_INTERFACE_FACTORY = InterfaceFactory()


class PermissionSystem :
    """ This is a high-level interface to the permission system. Can answer questions about permissions without involving 
    the user creating a lot of other objects. Also you can ask it to give you some default groups such as 'anon' (the group 
    to which anyone is a member)"""

    def get_or_create_group(self,group_name,display_name,place) :
        # note : we can't use get_or_create for TgGroup, because the created date clause won't match on a different day                                     
        # from the day the record was created.                                                                                                              
        xs = TgGroup.objects.filter(group_name=group_name)
        if len(xs) > 0 :
            g = xs[0]
        else :
            g = TgGroup(
                group_name=group_name, display_name=display_name, level='member',
                place=place,created=datetime.date.today()
                )
            g.save()
        return g

    def __init__(self) :
        self.root_location, created = Location.objects.get_or_create(name='root_location')
        if created :
            self.root_location.save()

        self.root_group = self.get_or_create_group('root','root',self.root_location)
        self.all_members_group = self.get_or_create_group('all_members','all members',self.root_location)


    def get_permissions_for(self,resource) :
        return (x for x in SecurityTag.objects.filter(resource_object_id=resource.id) if x.resource == strip(resource))

    def has_permissions(self,resource) :
        return len(set(self.get_permissions_for(resource))) > 0 

    def get_anon_group(self) : 
        """ The anon_group is the root of all groups, representing permissions given even to non members; plus everyone else"""
        return TgGroup.objects.filter(group_name='root')[0]

    def get_all_members_group(self) :
        """ The group to which all account-holding "hub-members" belong"""
        return TgGroup.objects.filter(group_name='all_members')[0]

    def has_access(self,agent,resource,interface) :
        t = SecurityTag()
        return t.has_access(agent,resource,interface)

    def delete_access(self,agent,resource,interface) :
        for tag in SecurityTag.objects.filter(interface=interface) :
            if tag.agent == agent and tag.resource==strip(resource) : 
                tag.delete()

    def get_interface_factory(self) : 
        return _ONLY_INTERFACE_FACTORY

    def get_interface_id(self,cls,name) :
        return self.get_interface_factory().get_id(cls,name)

    def get_permission_manager(self,cls) :
        return self.get_interface_factory().get_permission_manager(cls)

    def add_permission_manager(self,cls,pm) :
        self.get_interface_factory().add_permission_manager(cls,pm)
        

_ONLY_PERMISSION_SYSTEM = None


def get_permission_system() :
    global _ONLY_PERMISSION_SYSTEM
    if not _ONLY_PERMISSION_SYSTEM :
        _ONLY_PERMISSION_SYSTEM = PermissionSystem()
    return _ONLY_PERMISSION_SYSTEM


# Sliders and and permission_managers ____________________________________________________________

class UseSubclassException(Exception) :
    def __init__(self,cls,msg) :
        self.cls = cls
        self.msg = msg

class PermissionSliderDefaults(models.Model) :
    # we need to remember for any resource, who the owner and creators are
    # for when we recreate the permission sliders
    resource_content_type = models.ForeignKey(ContentType,related_name='permission_slider_resource')
    resource_object_id = models.PositiveIntegerField()
    resource = generic.GenericForeignKey('resource_content_type', 'resource_object_id')

    owner_content_type = models.ForeignKey(ContentType,related_name='permission_slider_owner')
    owner_object_id = models.PositiveIntegerField()
    owner = generic.GenericForeignKey('owner_content_type', 'owner_object_id')

    creator_content_type = models.ForeignKey(ContentType,related_name='permission_slider_creator')
    creator_object_id = models.PositiveIntegerField()
    creator = generic.GenericForeignKey('creator_content_type', 'creator_object_id')
    
class PermissionSliderDefaultException(Exception) :
    def __init__(self,resource,request,msg) :
        self.resource=resource
        self.msg = msg
    
    def __str__(self):
        return "%s (resource=%s)" % (self.msg,self.resource)

class PermissionManager :
    def __init__(self,target_class) :
        self.target_class = target_class # what class does this manager provide permissions for

    def get_permission_system(self) :
        return get_permission_system()

    def get_interfaces(self) :
        return self.get_permission_system().get_interface_factory().get_type(self.target_class)


    def make_slider_options(self,resource,owner,creator) :
        options = [
            SliderOption('root',get_permission_system().get_anon_group()),
            SliderOption('all_members',get_permission_system().get_all_members_group()),
            SliderOption('%s (owner)' % owner.display_name,owner),
            SliderOption('%s (creator)' % creator.display_name,creator)
        ]

        default_admin = default_admin_for(owner)

        if not default_admin is None :
            options.append( SliderOption(default_admin.display_name,default_admin) )

        return options


    def save_defaults(self, resource, owner, creator) :
        resource_type = ContentType.objects.get_for_model(resource)
        owner_type = ContentType.objects.get_for_model(owner)
        creator_type = ContentType.objects.get_for_model(creator)
        psd,created = PermissionSliderDefaults.objects.get_or_create(
            resource_content_type=resource_type,
            owner_content_type=owner_type,
            creator_content_type=creator_type,
            resource_object_id=resource.id,
            owner_object_id=owner.id,
            creator_object_id=creator.id)
        psd.save()


    def get_defaults(self,resource,interface) :
        resource_type = ContentType.objects.get_for_model(resource)
        try :
            return PermissionSliderDefaults.objects.get(resource_content_type=resource_type,resource_object_id=resource.id)
        except :
            raise PermissionSliderDefaultException(resource,'owner','no defaults could be found for this resource')

    def get_owner(self,resource,interface=None) :
        return self.get_defaults(resource,interface).owner

    def get_creator(self,resource,interface=None) :
        return self.get_defaults(resource,interface).creator


    def json_slider_group(self, title, intro, resource, interfaces, mins, constraints) :
        owner = self.get_owner(resource)
        creator = self.get_creator(resource)
        ps = self.get_permission_system()

        group_type = ContentType.objects.get_for_model(ps.get_anon_group())

        options = self.make_slider_options(resource,owner,creator)

        option_labels = [o.name for o in options]
        option_types = [ContentType.objects.get_for_model(o.agent) for o in options]
        option_ids = [o.agent.id for o in options]

        resource_type = ContentType.objects.get_for_model(resource)
        json = {
          'title':title,
          'intro':intro,
          'resource_id':resource.id,
          'resource_type':resource_type.id,
          'option_labels':option_labels,
          'option_types':[type.id for type in option_types],
          'option_ids':option_ids,
          'sliders':interfaces,
          'interface_ids':[ps.get_interface_id(resource.__class__,i) for i in interfaces],
          'mins':mins,
          'constraints':constraints,
          'extras': {} # use for non-slider permissions
          }


        current=[]
        for i in json['interface_ids'] :
            for s in SecurityTag.objects.filter(interface=i,resource_content_type=resource_type,resource_object_id=resource.id) :
                if s.agent in [o.agent for o in options] :
                    # we've found a SecurityTag which maps one of the agents on the slider, therefore 
                    # it's THIS agent which is the official slider setting
                    # map from this agent to position on the slider
                    j=0
                    agent_type = ContentType.objects.get_for_model(s.agent)
                    for (typ,ids) in zip(option_types,option_ids) :
                        if (typ==agent_type and ids==s.agent.id) :
                            current.append(j)
                            break
                        j=j+1            

        json['current'] = current
        return simplejson.dumps({'sliders':json})

    def update_permissions_from_slider_group(self, group) :
        for interface_id,val in group.iteritems() :
            resource_type,resource_id,agent_type,agent_id = val.split(',')
            #resource = ContentType.objects.get(model=)
            #s = Slider('created by plus_permissions.models.update_permissions_from_slider_group',
            #           resource,interface_id,default_agent,options=[]


class NoSliderException(Exception) :
    def __init__(self,cls,name) :
        self.cls = cls
        self.name = name


class Slider :
    """ A Slider is a specialized view of the underlying PermissionSystem.
    As such, it isn't an entity in the database in it's own right, but is used to manipulate 
    the existence or otherwise of particular SecurityTags ...

    A slider is created when a user needs to manipulate the PermissionSystem, and destroyed 
    when no longer relevant.

    The creation or destruction of a slider object represents no change to the permissions.

    When a slider is created, two pieces of fixed information define it : 
      - the resource to which it refers
      - the interface of the resource by which it refers
    These do not change during its life-time.

    The third dimension of the (agent,resource,interface), the agent, is changed by the slider.
    Changing the agent mapped to the resource / interface involves destroying the existing SecurityTag 
    and creating a new one.

    On creation, the slider may infer its status from the database
    
    """

    def __init__(self, tag_name, resource,interface_id,default_agent,creator,options=[],) :
        self.resource = resource
        self.interface_id = interface_id
        self.options = options
        self.tag_name = tag_name
        self.creator = creator

        # start with the default agent
        try :
            self.current_idx = self.options.index(default_agent)
            self.agent = default_agent
        except : 
            self.current_idx = -1
            self.agent = None

        # and over-ride if there's an existing SecurityTag which references one of the agents in our defaults
        for a in (tag.agent for tag in SecurityTag.objects.filter(interface=interface_id) if tag.resource == resource) :
            try : 
                self.current_idx = self.get_options().index(a)
                self.agent = a
                break
            except :
                pass

        if not self.agent is None : # we found a valid default_agent or current value in the database
            self.set_current_option(self.current_idx) # Warning, updates SecurityTag in database

    def get_relevant_tags(self) :
        return (t for t in SecurityTag.objects.filter(interface=self.interface_id) if t.resource == self.resource)

    def print_relevant_tags(self) :
        for t in self.get_relevant_tags():
            print ">> %s, %s, %s, %s" % (agent.display_name, t.interface, t.resource, t.name)

    def get_options(self) :
        return self.options

    def get_current_option(self) :
        return self.options[self.current_idx]

    def set_current_option(self,idx) :
        # set as index of the slider .... is this right? Probably.
        self.current_idx=idx
        _ONLY_PERMISSION_SYSTEM.delete_access(self.agent,self.resource,self.interface_id)
        self.agent = self.options[self.current_idx].agent
        t = SecurityTag(name=self.tag_name,agent=self.agent,resource=self.resource,interface=self.interface_id, creator=self.creator)
        t.save()


class SliderOption :
    def __init__(self,name,agent) :
        self.name = name
        self.agent = agent


