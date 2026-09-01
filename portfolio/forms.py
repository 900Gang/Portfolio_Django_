from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """
    Form for handling contact message submissions.
    """
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
                'placeholder': 'Your message...',
                'rows': 5,
            }),
        }

    def clean_message(self):
        """Validate that message is not just whitespace."""
        message = self.cleaned_data.get('message', '')
        if not message.strip():
            raise forms.ValidationError('Please enter a message.')
        return message
