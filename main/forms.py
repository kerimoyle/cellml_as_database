from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.contenttypes.models import ContentType

from main.models import (Math)


# TODO make levels for copy/importing ...
class CopyForm(forms.Form):
    class Meta:
        fields = ['item_type', 'item_id', 'options']

    def __init__(self, *args, **kwargs):
        super(CopyForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-copy_form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        # self.helper.add_input(Submit('submit', 'Copy'))

        self.fields['options'] = forms.ChoiceField(
            widget=forms.RadioSelect(),
            choices=[('base', 'Local fields only'),
                     ('link', 'Link to related items'),
                     ('deep', 'Duplicate related items'), ],
        )


class PrivacyForm(forms.Form):
    class Meta:
        fields = ['privacy']

    def __init__(self, *args, **kwargs):
        super(PrivacyForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-privacy_form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        # self.helper.add_input(Submit('submit', 'Save'))

        self.fields['options'] = forms.ChoiceField(
            widget=forms.RadioSelect(),
            choices=[('private', 'private'),
                     ('public', 'public'), ],
        )


class DeleteForm(forms.Form):
    class Meta:
        fields = ['item_type', 'item_id', 'options']

    def __init__(self, *args, **kwargs):
        super(DeleteForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-delete_form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        # self.helper.add_input(Submit('submit', 'Delete'))  # Removing submit button from forms which have a modal

        self.fields['options'] = forms.ChoiceField(
            widget=forms.RadioSelect(),
            choices=[('base', 'Delete item only'),
                     ('deep', 'Delete related items'), ],
        )


class LoginForm(forms.Form):
    class Meta:
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-login_form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        # self.helper.add_input(Submit('login_view', 'Login'))

        self.fields['username'] = forms.CharField(
            widget=forms.TextInput()
        )
        self.fields['password'] = forms.CharField(
            widget=forms.PasswordInput()
        )


class RegistrationForm(forms.Form):
    class Meta:
        fields = ['first_name', 'last_name', 'email', 'username', 'password', 'repeat_password']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-registration_form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        # self.helper.add_input(Submit('register', 'Register'))

        self.fields['first_name'] = forms.CharField(
            widget=forms.TextInput()
        )
        self.fields['last_name'] = forms.CharField(
            widget=forms.TextInput()
        )
        self.fields['email'] = forms.EmailField(
            widget=forms.EmailInput
        )
        self.fields['username'] = forms.CharField(
            widget=forms.TextInput()
        )
        self.fields['password'] = forms.CharField(
            widget=forms.PasswordInput()
        )
        self.fields['repeat_password'] = forms.CharField(
            widget=forms.PasswordInput()
        )


class MathCreateForm(forms.ModelForm):
    class Meta:
        model = Math
        fields = ['name', 'math_ml', 'cellml_id', 'notes']

    def __init__(self, *args, **kwargs):
        super(MathCreateForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-math_create_form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        # self.helper.add_input(Submit('math_create', 'Save'))


class DownstreamLinkForm(forms.Form):
    class Meta:
        fields = ['link_to_id']

    def __init__(self, *args, **kwargs):
        item_type = kwargs.pop('item_type')
        item_id = kwargs.pop('item_id')
        parent_type = kwargs.pop('parent_type')
        parent_model = ContentType.objects.get(app_label='main', model=parent_type)

        queryset = parent_model.get_all_objects_for_this_type()

        super(DownstreamLinkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-reverse_link_form'
        self.helper.form_class = 'blueForms'

        self.fields['link_to_id'] = forms.ModelMultipleChoiceField(
            queryset=queryset,
            widget=forms.CheckboxSelectMultiple()
        )


class UnlinkForm(forms.Form):
    class Meta:
        fields = ['unlink_item_type', 'unlink_item_id', 'unlink_related_name', 'unlink_related_id']

    def __init__(self, *args, **kwargs):
        super(UnlinkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-unlink_form'
        self.helper.form_class = 'blueForms'
