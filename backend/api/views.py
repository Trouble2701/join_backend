# views.py

from .serializers import ContactsSerializer, TaskSerializer, SubTaskSerializer, LoginSerializer, RegisterSerializer
from backend.models import Contacts, Task, Subtask

from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout 

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, serializers, mixins, generics, viewsets
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAdminUser 



class ContactsView(viewsets.ModelViewSet):
    queryset = Contacts.objects.all()
    serializer_class = ContactsSerializer

    # Die create-Methode ist so wie du sie hattest, und sie ist jetzt passender,
    # da der ContactsSerializer sich nicht mehr um das User-Modell kümmert.
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # perform_create ruft den create des Serializers auf,
        # der jetzt nur den Contact erstellt (ohne User-Verknüpfung).
        self.perform_create(serializer)

        response_data = serializer.data
        print("DEBUG: Response Data from ContactsSerializer (DURING POST):", response_data)

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    # Die destroy-Methode habe ich minimal angepasst, um die Klarheit zu erhöhen,
    # aber deine Logik ist im Kern dieselbe und funktioniert gut für die Trennung.
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object() # Holt den zu löschenden Contact

        # Wenn der Contact mit einem registrierten User verknüpft ist
        # (d.h. User existiert und hat ein nutzbares Passwort).
        if instance.user and instance.user.has_usable_password():
            return Response(
                {"detail": "Dieser Kontakt kann nicht gelöscht werden, da ein registrierter Benutzer mit diesem Konto existiert. Löschen Sie zuerst den Benutzer im Admin-Panel, falls gewünscht, oder entfernen Sie das Passwort des Benutzers."},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            # Fall 1: Contact hat einen User, aber dieser User hat KEIN nutzbares Passwort.
            # In diesem Fall wollen wir den (unregistrierten) User auch löschen.
            # CASCADE in models.py wird dann den Contact auch löschen.
            if instance.user:
                print(f"DEBUG: Lösche zugehörigen Benutzer '{instance.user.email}' (hat kein Passwort) über Contact-Löschung.")
                instance.user.delete() # Löscht User, was über CASCADE auch Contact löscht

            # Fall 2: Contact hat KEINEN verknüpften User.
            # Dann löschen wir nur den Contact selbst.
            else:
                print(f"DEBUG: Lösche Kontakt '{instance.email}' (hat keinen verknüpften Benutzer).")
                self.perform_destroy(instance) # Ruft den Standard-Destroy auf

            return Response(status=status.HTTP_204_NO_CONTENT)


class TaskView (viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class SubTaskView (viewsets.ModelViewSet):
    queryset = Subtask.objects.all()
    serializer_class = SubTaskSerializer

class LoginView(APIView):
    """
    API-Endpunkt für den Benutzer-Login.
    """
    permission_classes = [AllowAny] # Jeder darf versuchen sich einzuloggen

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user) # Django's eingebaute Login-Funktion
        response_data = {'message': 'Erfolgreich angemeldet', 'user_id': user.id, 'email': user.email}
        print(f"DEBUG: LoginView sendet Antwort: {response_data}")
        return Response(response_data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    """
    API-Endpunkt für den Benutzer-Logout.
    """
    def post(self, request, format=None):
        logout(request) # Django's eingebaute Logout-Funktion
        return Response({'message': 'Erfolgreich abgemeldet'}, status=status.HTTP_200_OK)

class RegisterView(CreateAPIView):
    """
    API-Endpunkt für die Benutzerregistrierung.
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny] # Jeder darf sich registrieren

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # perform_create ruft die create-Methode des RegisterSerializers auf.
        # Dort wird der User und der Contact erstellt/verknüpft.
        self.perform_create(serializer)

        # Holen des User-Objekts, das im RegisterSerializer.create() gespeichert wurde.
        user = serializer._user_instance_for_view
        
        # Nach erfolgreicher Registrierung den Benutzer direkt einloggen.
        login(request, user)

        response_data = {
            'message': 'Erfolgreich registriert und angemeldet',
            'user_id': user.id,
            'email': user.email,
            'contact_id': serializer.instance.id # Die ID des (neu erstellten oder verknüpften) Kontakts
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
