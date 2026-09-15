from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """
    Contact message submission.

    Carries a honeypot field: a real input that is hidden from people with
    CSS and skipped by assistive technology, but that naive form-filling bots
    populate. A non-empty value fails validation like any other error, so the
    bot gets no signal that it was detected.
    """

    # Named plausibly enough that a bot will fill it, and kept out of Meta
    # so it is never written to the model.
    website = forms.CharField(
        required=False,
        label='Website',
        widget=forms.TextInput(attrs={
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true',
        }),
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your name',
                'autocomplete': 'name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
                'autocomplete': 'email',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What is this about?',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tell me about the role, project or question...',
                'rows': 5,
            }),
        }

    def clean_website(self):
        """Reject submissions that filled the honeypot."""
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('This field must be left blank.')
        return ''

    def clean_message(self):
        """Validate that message is not just whitespace."""
        message = self.cleaned_data.get('message', '')
        if not message.strip():
            raise forms.ValidationError('Please enter a message.')
        return message
