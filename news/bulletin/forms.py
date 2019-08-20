from django import forms
from django.forms import formset_factory, ModelMultipleChoiceField

from django.contrib.auth.forms import UserCreationForm

from django.core.exceptions import ValidationError

from .models import Source, Category, User

import pytz

# Setting some default lists and variables for use in the forms

stockoptions = [("AAPL", "Apple, Inc. (APPL)"),("TSLA", "Tesla, Inc. (TSLA)"),("NKE","Nike, Inc. (NKE)"),("JCP","JC Penney, Inc. (JCP)")]  #total stock list

cityoptions = [("New York, NY","New York, NY"),("Austin, TX","Austin, TX"),("Portland, OR","Portland, OR"),("Chicago, IL","Chicago, IL")]

timeoptions = [('',''),("01:00:00","1 a.m."),("02:00:00","2 a.m."),("03:00:00","3 a.m."),("04:00:00","4 a.m."),("05:00:00","5 a.m."),("06:00:00","6 a.m."),("07:00:00","7 a.m."),("08:00:00","8 a.m."),("09:00:00","9 a.m."),("10:00:00","10 a.m."), ("11:00:00","11 a.m."), ("12:00:00","Noon"),("13:00:00","1 p.m."),("14:00:00","2 p.m."),("15:00:00","3 p.m."), ("16:00:00","4 p.m."), ("17:00:00","5 p.m."), ("18:00:00","6 p.m."), ("19:00:00","7 p.m."), ("20:00:00","8 p.m."), ("21:00:00","9 p.m."), ("22:00:00","10 p.m."), ("23:00:00","11 p.m."), ("00:00:00","Midnight")]

categoryoptions = []

for cat in Category.objects.all():
    selection = (cat.category,cat.category)
    categoryoptions.append(selection)

categoryoptions.append(("Custom alerts","Custom alerts"))

TIMEZONES = []

tzlist = pytz.common_timezones

for timezone in tzlist:
    newtuple = (timezone, timezone)
    TIMEZONES.append(newtuple)

# TIMEZONES = pytz.common_timezones
# (
#     ('US/Eastern','US/Eastern'),
#     ('US/Central','US/Central'),
#     ('US/Mountain','US/Mountain'),
#     ('US/Pacific','US/Pacific')
# )


# Old form for setting categories and sources with checklists - not used anymore

# Field and form for setting sources

class SourceMultipleChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self,obj):
        return obj.source   # So that we can have multiple of the source preference form on the same page

class SourcePreferenceForm(forms.Form):

    def __init__(self, cat, *args, **kwargs):
        super(SourcePreferenceForm, self).__init__(*args, **kwargs)
        self.fields['sources'] = SourceMultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            queryset=Source.objects.filter(category=cat).order_by('source'),
            label=''
        )

# Form to use for processing results

class AllSourceForm(forms.Form):
    sources = forms.ModelMultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            queryset=Source.objects.all(),
            label=''
        )

# Form for users to pick stocks and weather

class StockPreferenceForm(forms.Form):
    stocks = forms.MultipleChoiceField(widget=forms.SelectMultiple(attrs={'id':'stock_select'}), choices=stockoptions, label='')

class WeatherForm(forms.Form):
    cities = forms.MultipleChoiceField(widget=forms.SelectMultiple(attrs={'id':'city_select'}), choices=cityoptions, label='')

class WidgetForm(forms.Form):
    def __init__(self, wname, choicelist, *args, **kwargs):
        super(WidgetForm, self).__init__(*args, **kwargs)
        self.fields[wname] = forms.MultipleChoiceField(
            widget=forms.SelectMultiple(attrs={'id':'' + wname + '_select'}),
            choices=choicelist,
            label=''
        )

# Form for users to create new topics - also used for them to edit old topics

class NewTopicForm(forms.Form):
    title = forms.CharField(label='Name for your custom alert:')
    keywords = forms.CharField(label='Keywords to search for:')
    categories = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=Category.objects.all().order_by('category'), label='Select categories to search in:')


class TopicForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Your Alert Name'}), label='Name for your custom alert:')
    categories = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=Category.objects.all().order_by('category'), label='Select categories to search in:')

class KeywordForm(forms.Form):
    keyword = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Your Alert Keyword'}),label='')

KeywordFormset = formset_factory(KeywordForm, extra = 0, can_delete=True)

# Form to order categories - not used because I couldn't order Model fields with Django

class CategoryOrderForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple(attrs={'id':'cat_order'}), queryset=Category.objects.all().order_by('category'), label="Select the order in which you'd like to see news categories appear:")

# Form to order categories - used because it allows for more flexibility

class SelectForm(forms.Form):
    def __init__(self, choicelist, *args, **kwargs):
        super(SelectForm, self).__init__(*args, **kwargs)
        self.fields['categories'] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            choices=choicelist,
            label=''
        )

# Simple form for users to pick what timezone they are in

class TimezoneForm(forms.Form):
    timezone = forms.ChoiceField(choices=TIMEZONES, label='Timezone:', help_text='This will determine what timezone your custom news bulletins are sent in.', widget=forms.Select(attrs={
            'class': 'form-control prefs-dropdown'}))


# Simple form to set email address

class SetAddressForm(forms.Form):
    email = forms.EmailField(label = 'Email address:', help_text='This is the email address where you will receive your custom news bulletins.', widget=forms.EmailInput(attrs={'class': 'form-control'}))


# Forms to set email time preferences

class EmailTimeForm(forms.Form):
    mailtimes = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(attrs={'id':'mailtime_select'}), choices=timeoptions, label='')

class EmailForm(forms.Form):
    day = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'form-control prefs-dropdown'}),
        choices = [('',''),('Every day', 'Every day'),('Weekdays', 'Weekdays'),('Monday', 'Mondays'),('Tuesday', 'Tuesdays'),('Wednesday', 'Wednesdays'),('Thursday', 'Thursdays'),('Friday', 'Fridays'),('Saturday', 'Saturdays'),('Sunday', 'Sundays')],
        label = 'Send me an email')
    time = forms.ChoiceField(widget=forms.Select(attrs={
            'class': 'form-control prefs-dropdown'}), choices = timeoptions, label = 'at')

EmailFormset = formset_factory(EmailForm, extra = 0, can_delete = True)


# Feedback form

class ContactForm(forms.Form):
    email = forms.EmailField(max_length=254, help_text='Please enter a contact email, so we can follow up if necessary.', label='Your email')
    message = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(),
    )


# Signup form with email

class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=254,label='Email address')

    def clean(self):
       email = self.cleaned_data.get('email')
       if User.objects.filter(email=email).exists():
            raise ValidationError("There is already an account associated with this email address.")
       return self.cleaned_data

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
