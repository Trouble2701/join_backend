# models.py

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

# contacts
class Contacts(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='contact_profile')
    name = models.CharField(max_length=255, blank=False, null=False)
    email = models.EmailField(max_length=255, blank=False, null=False, unique=True)
    color = models.CharField(max_length=255, blank=False, null=False, default='blue')
    online = models.BooleanField(default=False)
    phone = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Contacts"
    
    # NEU: Eine Property, um im Code leicht zu prüfen, ob es ein registrierter Benutzer ist
    @property
    def is_registered_user(self):
        return self.user is not None and self.user.has_usable_password()

# tasks (bleiben unverändert in models.py)
class Subtask(models.Model):
    subtasktext = models.CharField(max_length=255)
    done = models.BooleanField(default=False)
    task = models.ForeignKey(
        'Task', 
        related_name='subtasks', 
        on_delete=models.CASCADE 
    ) 

    def __str__(self):
        return self.subtasktext
    
    class Meta:
        verbose_name_plural = "Subtasks"


class Task(models.Model):
    task_id = models.IntegerField(unique=True, null=True, blank=True)
    category = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateField()
    
    PRIO_CHOICES = [
        ('low', 'Niedrig'),
        ('medium', 'Mittel'),
        ('urgent', 'Hoch'),
    ]
    prio = models.CharField(max_length=20, choices=PRIO_CHOICES, default='medium')
    
    STATUS_CHOICES = [
        ('toDos', 'To Do\'s'),
        ('inProgress', 'In Progress'),
        ('awaitFeedback', 'Awaiting Feedback'),
        ('done', 'Done'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='toDos')
    
    title = models.CharField(max_length=255)

    assignee_infos = models.ManyToManyField(
        Contacts, 
        related_name='assigned_tasks', 
        blank=True 
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Tasks"

@receiver(post_save, sender=Task)
def set_task_id(sender, instance, created, **kwargs):
    if created and instance.task_id is None:
        instance.task_id = instance.id
        instance.save(update_fields=['task_id'])