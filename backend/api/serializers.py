# backend/serializers.py (oder backend/serializers/tasks_serializers.py, je nach deiner Struktur)

from rest_framework import serializers
from backend.models import Contacts, Subtask, Task
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# Contacts Serializer
class ContactsSerializer(serializers.ModelSerializer):
    has_password_set = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Contacts
        fields = '__all__'

    def get_has_password_set(self, obj):
        return obj.user is not None and obj.user.has_usable_password()

# SubTask Serializer
class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ['id', 'subtasktext', 'done', 'task_id']


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
        assignee_ids = validated_data.pop('assignee_infos', [])

        task = super().create(validated_data)

        for subtask_data in subtasks_data:
            Subtask.objects.create(task=task, **subtask_data)

        task.assignee_infos.set(assignee_ids)

        return task

    def update(self, instance, validated_data):
        
        subtasks_data = validated_data.pop('subtasks', None)
        assignee_ids = validated_data.pop('assignee_infos', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if subtasks_data is not None:
            existing_subtasks = {subtask.id: subtask for subtask in instance.subtasks.all()}
            subtasks_to_keep_ids = []

            for subtask_data in subtasks_data:
                subtask_id = subtask_data.get('id')

                if subtask_id:
                    subtask = existing_subtasks.get(subtask_id)
                    if subtask:

                        for attr, value in subtask_data.items():
                            setattr(subtask, attr, value)
                        subtask.save()
                        subtasks_to_keep_ids.append(subtask_id)
                    else:
                        Subtask.objects.create(task=instance, **subtask_data)
                else:
                    Subtask.objects.create(task=instance, **subtask_data)

            for subtask_id, subtask_instance in existing_subtasks.items():
                if subtask_id not in subtasks_to_keep_ids:
                    subtask_instance.delete()

        if assignee_ids is not None: 
            instance.assignee_infos.set(assignee_ids)

        return instance

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


# Login Serializer
class LoginSerializer(serializers.Serializer):
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
    

# Register Serializer
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    name = serializers.CharField(required=True, max_length=255)

    def validate_email(self, value):
        email_lower = value.lower()
        if User.objects.filter(email=email_lower, password__isnull=False).exists():
             raise serializers.ValidationError("Ein Benutzer mit dieser E-Mail-Adresse ist bereits registriert.")
        return email_lower

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        name = validated_data['name']

        user_instance = None
        contact_instance = None

        potential_contacts = Contacts.objects.filter(email__iexact=email).first()

        if potential_contacts:
            if potential_contacts.user is None or not potential_contacts.user.has_usable_password():
                contact_instance = potential_contacts
                print(f"DEBUG: Bestehender UNREGISTRIERTER Kontakt mit E-Mail '{email}' gefunden.")
            else:
                raise serializers.ValidationError("Ein Benutzer mit dieser E-Mail-Adresse ist bereits registriert.")
        
        if contact_instance:
            if not contact_instance.user:
                user_instance = User.objects.create_user(username=email, email=email, password=password)
                contact_instance.user = user_instance
                contact_instance.save()
                print(f"DEBUG: Neuer Benutzer für bestehenden Kontakt '{email}' erstellt und verknüpft.")
            else:
                user_instance = contact_instance.user
                user_instance.set_password(password)
                user_instance.save()
                print(f"DEBUG: Passwort für bestehenden Benutzer '{email}' gesetzt.")
        else:
            print(f"DEBUG: Kein unregistrierter Kontakt mit E-Mail '{email}' gefunden. Erstelle neuen Benutzer und Kontakt.")
            user_instance = User.objects.create_user(username=email, email=email, password=password)
            contact_instance = Contacts.objects.create(
                name=name,
                email=email,
                user=user_instance
            )
            print(f"DEBUG: Neuer Benutzer und Kontakt für '{email}' erstellt und verknüpft.")

        self._user_instance_for_view = user_instance
        return contact_instance
