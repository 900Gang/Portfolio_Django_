from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.home, name='home'),
    path('projects/<slug:slug>/', views.ProjectDetailView.as_view(), name='project_detail'),
]