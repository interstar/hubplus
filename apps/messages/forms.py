import datetime
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.db.models import get_app
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User

try:
    notification = get_app('notification')
except ImproperlyConfigured:
    notification = None


from messages.models import Message
from messages.fields import CommaSeparatedUserField

class ComposeForm(forms.Form):
    """
    A simple default form for private messages.
    """
    recipient = CommaSeparatedUserField(label=_(u"Recipient"))
    subject = forms.CharField(label=_(u"Subject"))
    body = forms.CharField(label=_(u"Body"),
                           widget=forms.Textarea(attrs={'rows': '12', 'cols':'55'}))
    
        
    def save(self, sender, parent_msg=None):

        recipients = self.cleaned_data['recipient']
        subject = self.cleaned_data['subject']
        body = self.cleaned_data['body']
        message_list = []
        for r in recipients:
            msg = r.message(sender,subject,body)
            if not msg : # r.message returns None if recipient is inactive (and therefore message isn't created)
                continue 

            if parent_msg is not None:
                msg.parent_msg = parent_msg
                parent_msg.replied_at = datetime.datetime.now()
                parent_msg.save()
            msg.save()
            message_list.append(msg)

        return message_list
