from django import forms
from django.utils.translation import ugettext as _

from greetme.models import Language, Greeting, DefaultLanguage


class GreetForm(forms.ModelForm):
    class Meta:
        model = Greeting
        exclude = ('user')
        widgets = {
            'greeting': forms.Textarea(attrs={'cols': 40, 'rows': 5}),
        }
    
    def __init__(self, user, *args, **kwargs):
        super(GreetForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean_greeting(self):
        greeting = self.cleaned_data['greeting']
        num_words = len(greeting.split())
        if num_words < 4:
            raise forms.ValidationError(_("Not enough words!"))
        greets = Greeting.objects.filter(users=self.user)
        if len(greets)>50:
            raise forms.ValidationError(_('You have too much greetings. Delete some of them.'))
        return greeting

    # Old version
    #choices = ( (lang.id, lang.name ) for lang in Language.objects.all())
    #lang = forms.ChoiceField(choices=choices, required=True,label='Language')
    #greeting = forms.CharField(max_length=512, widget=forms.Textarea)
    
    
class DefaultLanguageForm(forms.ModelForm):
    class Meta:
        model = DefaultLanguage
        exclude = ('user',)
