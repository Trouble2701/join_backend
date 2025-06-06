from django.urls import path, include
from .views import ContactsView, TaskView, SubTaskView, LoginView, LogoutView, RegisterView, DeleteMyAccountView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'contacts', ContactsView, basename='contact')
router.register(r'tasks', TaskView, basename='tasks')
router.register(r'subtasks', SubTaskView, basename='subtasks')

urlpatterns = [
     path('', include(router.urls)),
     path('login/', LoginView.as_view(), name='login'),
     path('logout/', LogoutView.as_view(), name='logout'),
     path('register/', RegisterView.as_view(), name='register'),
     path('delete-my-account/', DeleteMyAccountView.as_view(), name='delete-my-account'),
]
