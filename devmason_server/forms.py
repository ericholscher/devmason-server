from django import forms

class ProjectForm(forms.Form):
    """
    Form to accept a new project submission.
    """
    name = forms.CharField(max_length=100)
    source_repo = forms.CharField()
