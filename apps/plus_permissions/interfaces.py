"""
Interfaces are like roles. They group together various Read/Write/Call options for assignment. We should access content objects through an interface, which acts as a mask on the object.

Interfaces are associated with a SecurityContext via a SecurityTag. Agents (users and groups) get access to them by being associated with a security tag via the (Agent object). Agents can acquire interfaces by being a "member of" another agent with access to them.  

Interfaces are namespaced by the type they apply to e.g. "Wiki.Editor" allowing us to assign permissions on a type.  The syntax ".Editor" refers to the Editor Interface on the SecurityContext target object. The syntax *.Editor refers to the Editor interface on any objects in the security context.
"""

__all__ = ['secure_wrap', 'PlusPermissionsNoAccessException', 'PlusPermissionsReadOnlyException', 'add_type_to_interface_map', 'add_interfaces_to_type', 'strip', 'TemplateSecureWrapper', 'get_interface_map']

from apps.plus_permissions.exceptions import PlusPermissionsReadOnlyException, PlusPermissionsNoAccessException, NonExistentPermission

def secure_wrap(content_obj, user, interface_names=None, diagnose=None):
    if content_obj.__class__ == SecureWrapper:
        content_obj = content_obj.get_inner()
    access_obj = SecureWrapper(content_obj)
    access_obj.load_interfaces_for(user, interface_names=interface_names,diagnose=diagnose)
    return access_obj




class TemplateSecureWrapper:

    def __init__(self, SecureWrapper):
        self.SecureWrapper = SecureWrapper

    def __getattr__(self, name):
        if name.startswith("has_write_"):
            write_attr = name.split('has_write_')[1]
            return self.can_write(write_attr)

        if name.startswith("should_show_"):
            # YES we do need this because the criteria is not simply permission
            # it's the OR of edit permission and having a displayable value
            # which can't be tested in the template
            show_attr = name.split('should_show_')[1]
            if self.can_write(show_attr) :
                return True

            val = self.__getattr__(show_attr)
            if val == NotViewable :
                # need a separate test because the *class* NotViewable evaluates to True, 
                # even though an instance of it, evaluates to false
                return False
            if val :
                return True
            return False

        try:
            return getattr(self.SecureWrapper, name)
        except:
            return NotViewable

    def obj(self):
        return self.SecureWrapper._inner


    def can_write(self, name):
        return self.SecureWrapper.has_permission(name, InterfaceReadWriteProperty) or self.SecureWrapper.has_permission(name, InterfaceWriteProperty)



def strip(x) :
    """If x is really a Null interface, return the inner value, otherwise, return itself"""
    try : 
        return x.get_inner()
    except :
        return x




class InterfaceReadProperty:
    """ Add this to a SecureWrapper to allow a property to be readable"""
    pass

class InterfaceWriteProperty:
    """ Add this to a SecureWrapper to allow a property to be writable """
    pass

class InterfaceReadWriteProperty:
    """ Add this to a SecureWrapper to allow a property to be writable """
    pass

class InterfaceCallProperty:
    """ Add this to a SecureWrapper to allow a property to be called """
    pass



class EmptyString(type):
    def __str__(cls):
        return ""
    def __unicode__(cls):
        return u""
    def __repr__(cls):
        return u""
    def __nonzero__(cls) :
        return False

class NotViewable(object):
    __metaclass__= EmptyString
    @classmethod
    def __str__(cls):
        return ""
    #@classmethod
    #def __unicode__(cls):
    #    return u""
    @classmethod
    def __repr__(cls):
        return u""
    def __nonzero__(self) :
        return False

def is_not_viewable(obj,attr_name) :
    x = getattr(obj,attr_name) 
    if x == NotViewable :
        return True
    else : 
        return False

from apps.plus_permissions.models import type_interfaces_map, has_access

class SecureWrapper:
    """
    Empty interface, wraps models in a shell, which only lets explicitly named properties through
    """
    def __init__(self, inner) :
        self.__dict__['_inner'] = inner
        self.__dict__['_exceptions'] = [ 
            lambda x : x[0] == '_',
            lambda x : x == 'id',
            lambda x : x == 'pk',
            lambda x : x == 'object_id',
            lambda x : x == 'save',
            lambda x : x == 'get_ref',
            lambda x : x == 'edit_key',
            lambda x : x == 'can_write', # Added by phil, otherwise we can't test can_write in the editable_attribute templatetag
        ]
        self.__dict__['_permissions'] = {InterfaceReadProperty: set(),
                                         InterfaceCallProperty: set(),
                                         InterfaceWriteProperty: set(),
                                         InterfaceReadWriteProperty: set()}
        self.__dict__['_interfaces'] = set()

    def depth(self) :
        if self._inner.__class__ != SecureWrapper:
            return 0
        return self._inner.depth() + 1

    def get_inner(self) :
        return self._inner

    def get_inner_class(self) :
        return self.get_inner().__class__

    def has_interface(self,i_str) :
        # string representation of interface e.g. "Profile.Viewer"
        return i_str in self._interfaces

    def load_interfaces_for(self, agent, interface_names=None, diagnose=None) :
        """Load interfaces for the wrapped inner content that are available to the agent"""
        resource = self.get_inner()
        cls = resource.__class__
        interface_map = type_interfaces_map[cls.__name__]
        if not interface_names:
            interface_names = interface_map.keys()
        for iname in interface_names:
            interface = interface_map[iname]
            iface_name = self.get_inner().__class__.__name__ + '.' + iname
            #XXX we certainly shouldn't do an individual has access check for each interface but rather process them all at the same time
            if has_access(agent=agent, resource=resource, interface=iface_name, diagnose=diagnose):
                self._interfaces.add(iface_name)
                self.add_permissions(interface)
    
    def add_permissions(self, interface):
        for attr, perm in interface.__dict__.iteritems():
            try:
                permitted = self._permissions[perm]
            except KeyError:
                if attr.startswith('_'):
                    pass
                else:
                    raise NonExistentPermission
            else:
                if attr not in permitted:
                    permitted.add(attr)

    def has_permission(self, name, perm) :
        """The moment of truth!"""
        try: 
            perms = self._permissions[perm]
        except KeyError:
            raise NonExistentPermission
        else:
            if name in perms:
                return True
            return False
                        
    def __getattr__(self, name):
        for rule in self.__dict__['_exceptions']:
            if rule(name) :
                return self.get_inner().__getattribute__(name)

        # new notation
        # we'll test if something has permission on an attribute by testing obj.p_att_name
        # WHY? Because a) we want something that we can test in a template
        #              b) when we've received it from a result_set which we haven't had a chance to filter
        #              

        if name[:2] == 'p_' :
            try :
                val = self.__getattr__(name[2:])
                return True
            except PlusPermissionsNoAccessException, e :
                return False

        # OK, if we're here, this isn't a permission test, so try to actually return the value of the attribute

        if self.has_permission(name, InterfaceReadProperty) or self.has_permission(name, InterfaceReadWriteProperty):
            return self.get_inner().__getattribute__(name)

        elif self.has_permission(name, InterfaceCallProperty):
            return self.get_inner().__getattribute__(name)

        raise PlusPermissionsNoAccessException(self.get_inner_class(),name,'from __getattr__')

    def __setattr__(self, name, val):
        for rule in self.__dict__['_exceptions']:
            if rule(name) :
                setattr(self, name, val)

        if self.has_permission(name, InterfaceWriteProperty) or self.has_permission(name, InterfaceReadWriteProperty):
            self.get_inner().__setattr__(name,val)
            return None      
        raise PlusPermissionsReadOnlyException(self.get_inner_class(),name)        


    def s_eq(self, other):
        """Secure Equality : compares self and other directly and the _inner of each with each."""
        inner = self.get_inner()
        if inner == other : return True
        try :
            if inner == other.get_inner() : return True
        except :
            return False
        return False



def add_creator_interface(type):
    class CanCreate:
        pk = InterfaceReadProperty
    setattr(CanCreate, 'create_%s'%type.__name__, InterfaceCallProperty)
    return CanCreate

def add_manage_permissions_interface():
    class ManagePermissions:
        pk = InterfaceReadProperty
        create_custom_security_context = InterfaceCallProperty
        use_acquired_security_context = InterfaceCallProperty
        move_sliders = InterfaceCallProperty  #use explicit 
        add_arbitrary_agent = InterfaceCallProperty
        remove_arbitrary_agent = InterfaceCallProperty
        get_all_sliders = InterfaceCallProperty
        get_type_slider = InterfaceCallProperty
        get_slider_level = InterfaceCallProperty

    return ManagePermissions



