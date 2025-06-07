from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

class RegisterUserForm(UserCreationForm):
    # Define additional fields specific to students
    studentId = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=20)
    studentName = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=50)
    studentPhone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=50)
    studentCourse = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=50)
    studentEmail = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=50)
    studentAddress = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=50)

    class Meta:
        model = User
        fields = ('username', 'studentName', 'studentPhone', 'studentId', 'studentEmail', 'studentAddress', 'studentCourse', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(RegisterUserForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


'''
from django.db import models  
from django.forms import fields  
from .models import UploadImage  
from django import forms  


  
  
class UserImage(forms.ModelForm):  
    class meta:  
        # To specify the model to be used to create form  
        models = UploadImage  
        # It includes all the fields of model  
        fields = '__all__'  
'''