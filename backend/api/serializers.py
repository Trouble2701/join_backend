# backend/serializers.py
from rest_framework import serializers
from backend.models import Contacts, Subtask, Task
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate # Wird für den LoginSerializer benötigt
from backend.models import Contacts # Das Contacts-Modell hier importieren
from django.db.models import Q # Für komplexe Lookups im create/validate 

#Contacts
class ContactsSerializer(serializers.ModelSerializer):
    # has_password_set kann optional hinzugefügt werden, wenn du es im Frontend brauchst,
    # um den Status eines Kontakts (registriert/unregistriert) anzuzeigen.
    # Hier ist es nur für die Lesbarkeit (read_only).
    has_password_set = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Contacts
        fields = '__all__' # Oder eine explizite Liste von Feldern, die du zurückgeben möchtest

    def get_has_password_set(self, obj):
        # Diese Methode wird nur aufgerufen, wenn 'has_password_set' in den fields ist.
        # Prüft, ob der verknüpfte User existiert und ein nutzbares Passwort hat.
        return obj.user is not None and obj.user.has_usable_password()
    

# Tasks
class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ['subtasktext', 'done']


class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubTaskSerializer(many=True, required=False)

    assignee_infos = serializers.PrimaryKeyRelatedField(
        queryset=Contacts.objects.all(),
        many=True,
        required=False,
        write_only=True
    )

    task_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'

    def create(self, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        task = super().create(validated_data)

        for subtask_data in subtasks_data:
            Subtask.objects.create(task=task, **subtask_data)

        return task

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if 'task_id' in ret:
            ret['task-id'] = ret['task_id']
            del ret['task_id']

        if 'due_date' in ret:
            ret['due-date'] = ret['due_date']
            del ret['due_date']

        detailed_assignees = []
        for contact in instance.assignee_infos.all():
            detailed_assignees.append({
                'id': contact.id,
                'name': contact.name,
                'color': contact.color
            })

        ret['assignee-infos'] = detailed_assignees

        return ret

    def get_assignee_infos(self, obj):

        return [
            {'id': contact.id, 'name': contact.name, 'color': contact.color}
            for contact in obj.assignee_infos.all()
        ]


class LoginSerializer(serializers.Serializer):
    """
    Serializer für den Login-Vorgang.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        email = data.get('email').lower()
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError('E-Mail und Passwort sind erforderlich.')

        user = authenticate(request=self.context.get('request'), username=email, password=password)

        if not user:
            raise serializers.ValidationError('Ungültige Anmeldeinformationen.')
        if not user.is_active:
            raise serializers.ValidationError('Benutzerkonto ist inaktiv.')

        data['user'] = user
        return data



class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    name = serializers.CharField(required=True, max_length=255)

    def validate_email(self, value):
        email_lower = value.lower()
        # Diese Prüfung bleibt bestehen, da User.objects.filter direkt auf das Passwortfeld zugreifen kann.
        # Es prüft, ob ein User mit dieser E-Mail existiert UND ein Passwort gesetzt hat.
        if User.objects.filter(email=email_lower, password__isnull=False).exists():
             raise serializers.ValidationError("Ein Benutzer mit dieser E-Mail-Adresse ist bereits registriert.")
        return email_lower

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        name = validated_data['name']

        user_instance = None
        contact_instance = None

        # --- NEUE LOGIK FÜR DIE SUCHE NACH BESTEHENDEM KONTAKT ---
        # 1. Versuche, einen Kontakt mit der E-Mail zu finden.
        #    Wir können hier nur auf 'user__isnull' prüfen, nicht auf 'has_usable_password'.
        potential_contacts = Contacts.objects.filter(email__iexact=email).first()

        # Jetzt prüfen wir die Bedingung in Python
        if potential_contacts:
            # Ein Kontakt mit dieser E-Mail existiert. Jetzt prüfen wir den User-Status.
            # Ein Contact ist "unregistriert", wenn:
            # a) Er keinen verknüpften User hat (contact_instance.user is None) ODER
            # b) Er einen verknüpften User hat, ABER DIESER USER KEIN nutzbares Passwort hat.
            if potential_contacts.user is None or not potential_contacts.user.has_usable_password():
                contact_instance = potential_contacts
                print(f"DEBUG: Bestehender UNREGISTRIERTER Kontakt mit E-Mail '{email}' gefunden.")
            else:
                # Dieser Kontakt ist bereits mit einem registrierten Benutzer verknüpft.
                # Das sollte durch validate_email() bereits abgefangen worden sein,
                # aber zur Sicherheit könnte man hier auch einen Fehler werfen.
                # In diesem Fall gehen wir davon aus, dass validate_email() seinen Job gemacht hat.
                # Wenn wir hier ankommen, dann bedeutet es, dass der Benutzer bereits registriert ist.
                raise serializers.ValidationError("Ein Benutzer mit dieser E-Mail-Adresse ist bereits registriert.")
        
        # --- ENDE NEUE LOGIK ---


        if contact_instance: # Wenn ein passender unregistrierter Kontakt gefunden wurde
            if not contact_instance.user:
                # Fall a): Kontakt hat keinen User, erstelle einen neuen User und verknüpfe ihn.
                user_instance = User.objects.create_user(username=email, email=email, password=password)
                contact_instance.user = user_instance  # <-- HIER WIRD VERKNÜPFT!
                contact_instance.save()
                print(f"DEBUG: Neuer Benutzer für bestehenden Kontakt '{email}' erstellt und verknüpft.")
            else:
                # Fall b): Kontakt hat einen User ohne Passwort, setze das Passwort.
                user_instance = contact_instance.user
                user_instance.set_password(password)
                user_instance.save()
                print(f"DEBUG: Passwort für bestehenden Benutzer '{email}' gesetzt.")
        else: # Wenn kein passender unregistrierter Kontakt gefunden wurde
            print(f"DEBUG: Kein unregistrierter Kontakt mit E-Mail '{email}' gefunden. Erstelle neuen Benutzer und Kontakt.")
            user_instance = User.objects.create_user(username=email, email=email, password=password)
            contact_instance = Contacts.objects.create(
                name=name,
                email=email,
                user=user_instance # <-- HIER WIRD VERKNÜPFT!
            )
            print(f"DEBUG: Neuer Benutzer und Kontakt für '{email}' erstellt und verknüpft.")

        self._user_instance_for_view = user_instance
        return contact_instance