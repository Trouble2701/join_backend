from django.urls import path, include
from .views import ContactsView, TaskView, SubTaskView, LoginView, LogoutView, RegisterView
from rest_framework.routers import DefaultRouter
from rest_framework import routers

router = DefaultRouter()
router.register(r'contacts', ContactsView, basename='contact')
router.register(r'tasks', TaskView, basename='tasks')
router.register(r'subtasks', SubTaskView, basename='subtasks')

urlpatterns = [
     path('', include(router.urls)),
     path('login/', LoginView.as_view(), name='login'), # Neuer Login-Endpunkt
     path('logout/', LogoutView.as_view(), name='logout'), # Neuer Logout-Endpunkt
     path('register/', RegisterView.as_view(), name='register'), # <-- NEUER REGISTRIERUNGS-ENDPUNKT
]
