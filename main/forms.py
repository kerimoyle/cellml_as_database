from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from main.models import (Math)


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
        self.helper.add_input(Submit('math_create', 'Save'))
