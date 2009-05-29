
from django.db import models

from django.contrib.auth.models import User, UserManager, check_password

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

import hashlib

def getHubspaceUser(username) :
    """ Returns the hubspace user. None if doesn't exist"""
    try :
        tu = User.objects.filter(username=username)[0]
        return  tu
    except Exception,e:
        print "Error in getHubspaceUser %s" % e
        return None


def to_db_encoding(s, encoding):
    if isinstance(s, str):
        pass
    elif hasattr(s, '__unicode__'):
        s = unicode(s)
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return s


def encrypt_password(password) :
    return hashlib.md5(password).hexdigest()

# The following will be patched into the User object in the 
def set_password(self,raw) :
    self.password = encrypt_password(raw)

def check_password(self,raw) :
    return self.password == encrypt_password(raw)

# 
class HubspaceCompatibilityNotToBeSavedException(Exception) : 
    def __init__(self,cls,extra) :
        self.cls = cls
        self.extra = extra

class TgUser(models.Model):
    user_name = models.CharField(unique=True, max_length=255)
    email_address = models.CharField(unique=True, max_length=255)
    password = models.CharField(max_length=40)

    class Meta:
        db_table = u'tg_user'

    def save(self) :
        raise HubspaceCompatibilityNotToBeSavedException(TgUser,'User_name:%s'%self.user_name)


class HubspaceAuthenticationBackend :
    """
    Authenticate against HubSpace database for user login and 
    """

    def getUserClass(self) : return User
    def createUser(self,username,password,email='') :
        self.getUserClass()(username=username,password=password,email=email)
    def findUser(self,username) :
        return self.getUserClass().objects.filter(username=username)[0]
    def getOrCreateUser(self,username,password='',email='') :
        try :
            u = self.findUser(username)
        except Exception, e:
            try :
                u = self.createUser(username,password,email)
            except Exception, e:
                u = None
        return u


    def authenticate(self, username=None, password=None):
        login_valid = True
        pwd_valid = True

        UserClass = self.getUserClass()

        try:
            hubspaceUser = getHubspaceUser(username)
            if  hubspaceUser == None : 
                print "there is no hubspace user called '%s'" % username
                return None # Doesn't exist in Hubspace database

            print "user password %s :: encrypt %s" % (hubspaceUser.password,encrypt_password(password))
            if not (hubspaceUser.password == encrypt_password(password)) : return None # Password doesn't match
            djangoUser = self.getOrCreateUser(username,hubspaceUser.password)
            self.refresh(hubspaceUser,djangoUser)  # allow subclasses to over-ride the refresh 
            print "got %s" % djangoUser
            return djangoUser
        except Exception, e:
            print 'Error3 %s' % e
            # What went wrong here? Needs handling
            pass
        return None

    def refresh(self,hubspaceUser,djangoUser) :
        #djangoUser.password = hubspaceUser.password
        #djangoUser.save()
        pass

    def get_user(self, user_id):
        UserClass = self.getUserClass()
        try:
            return UserClass.objects.get(pk=user_id)
        except UserClass.DoesNotExist:
            return None

class Location(models.Model):

    name = models.CharField(unique=True, max_length=200)
    class Meta:
        db_table = u'location'

try :
  class TgGroup(models.Model):
    #id = models.IntegerField(primary_key=True)
    group_name = models.CharField(unique=True, max_length=40)
    display_name = models.CharField(max_length=255)
    created = models.DateTimeField()
    place = models.ForeignKey(Location)
    level = models.CharField(max_length=9)

    class Meta:
        db_table = u'tg_group'

    def isGroup(self) : return True

    def addMember(self,x) :
        if not self.hasMember(x) :
            map = HCGroupMapping()
            map.child=x
            map.parent=self
            map.save()

    def getMembers(self) : 
        return (x.child for x in HCGroupMapping.objects.filter(parent=self))

    def hasMember(self,x) :
        return (x in self.getMembers())

    def getNoMembers(self) :
        return HCGroupMapping.objects.filter(parent=self).count()


  class HCGroupMapping(models.Model) :
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    child = generic.GenericForeignKey('content_type', 'object_id')
    parent = models.ForeignKey(TgGroup)

except Exception, e:
  print "##### %s" % e

# We're going to add the following method to User class
def isMemberOf(self,group) : 
    if not group.isGroup() : return False
    if group.hasMember(self) : return True
    # not a direct member, but perhaps somewhere up the tree of (enclosures / parents)
    for x in self.getEnclosures() :
        if x.isMemberOf(group) : 
            return True
    return False
    
# add it to TgGroup too
TgGroup.isMemberOf= isMemberOf

def getEnclosures(self) :
    return (x.parent for x in HCGroupMapping.objects.all() if x.child == self)

TgGroup.getEnclosures = getEnclosures

def isDirectMemberOf(self, group) :
    return group.hasMember(self)

TgGroup.isDirectMemberOf = isDirectMemberOf
