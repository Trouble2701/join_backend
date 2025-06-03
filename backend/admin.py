from django.contrib import admin
from .models import Contacts, Subtask, Task

# 1. Inline-Klasse für Subtasks
class SubtaskInline(admin.TabularInline): # Oder admin.StackedInline, je nach gewünschter Darstellung
    model = Subtask
    extra = 1 # Zeigt standardmäßig 1 leeres Formular für eine neue Subtask an
    fields = ['subtasktext', 'done'] # Welche Felder der Subtask angezeigt/bearbeitet werden sollen


# 2. Den TaskAdmin anpassen, um die Subtask Inlines zu verwenden
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'prio', 'due_date')
    list_filter = ('status', 'prio', 'category')
    search_fields = ('title', 'description')
    
    # Nur die SubtaskInline wird hier hinzugefügt
    inlines = [SubtaskInline] 

# Registriere jetzt deinen angepassten TaskAdmin für das Task-Model
admin.site.register(Task, TaskAdmin)

# Registriere die anderen Models wie gehabt (oder unregistriert lassen, wenn sie nur über Tasks verwaltet werden)
admin.site.register(Contacts) 
# Subtask NICHT direkt registrieren, wenn es ausschließlich inline über TaskAdmin verwaltet werden soll.
# admin.site.register(Subtask) 