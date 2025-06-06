# views.py

from .serializers import ContactsSerializer, TaskSerializer, SubTaskSerializer, LoginSerializer, RegisterSerializer
from backend.models import Contacts, Task, Subtask

from django.contrib.auth import login, logout 

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated



class ContactsView(viewsets.ModelViewSet):
    queryset = Contacts.objects.all()
    serializer_class = ContactsSerializer


    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_create(serializer)

        response_data = serializer.data
        print("DEBUG: Response Data from ContactsSerializer (DURING POST):", response_data)

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    
    def destroy(self):
        instance = self.get_object()

        if instance.user and instance.user.has_usable_password():
            return Response(
                {"detail": "Dieser Kontakt kann nicht gelöscht werden, da ein registrierter Benutzer mit diesem Konto existiert. Löschen Sie zuerst den Benutzer im Admin-Panel, falls gewünscht, oder entfernen Sie das Passwort des Benutzers."},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            if instance.user:
                print(f"DEBUG: Lösche zugehörigen Benutzer '{instance.user.email}' (hat kein Passwort) über Contact-Löschung.")
                instance.user.delete()

            else:
                print(f"DEBUG: Lösche Kontakt '{instance.email}' (hat keinen verknüpften Benutzer).")
                self.perform_destroy(instance)

            return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteMyAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, format=None):
        user = request.user
        if user.is_authenticated:
            user.delete()
            return Response({'message': 'Dein Konto und alle zugehörigen Daten wurden erfolgreich gelöscht.'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'detail': 'Nicht authentifiziert.'}, status=status.HTTP_401_UNAUTHORIZED)


class TaskView (viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class SubTaskView (viewsets.ModelViewSet):
    queryset = Subtask.objects.all()
    serializer_class = SubTaskSerializer


class LoginView(APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        response_data = {'message': 'Erfolgreich angemeldet', 'user_id': user.id, 'email': user.email}
        print(f"DEBUG: LoginView sendet Antwort: {response_data}")
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):

    def post(self, request):
        logout(request)
        return Response({'message': 'Erfolgreich abgemeldet'}, status=status.HTTP_200_OK)


class RegisterView(CreateAPIView):
    
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_create(serializer)

        user = serializer._user_instance_for_view
        
        login(request, user)

        response_data = {
            'message': 'Erfolgreich registriert und angemeldet',
            'user_id': user.id,
            'email': user.email,
            'contact_id': serializer.instance.id
        }
        return Response(response_data, status=status.HTTP_201_CREATED)