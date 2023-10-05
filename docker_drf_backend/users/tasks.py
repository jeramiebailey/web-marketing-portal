from django.contrib.auth import get_user_model
from docker_drf_backend.taskapp.celery import app
from docker_drf_backend.users.utils import remove_user_relationships

User = get_user_model()

@app.task
def logout_user(user_id):
    try:
        user = User.objects.get(id=user_id)
    except:
        user = None
    
    if user:
        try:
            user.auth_token.delete()
            return True
        except:
            return False

@app.task
def perform_user_offboarding_tasks(user_id):
    try:
        removed_relationships = remove_user_relationships(user_id=user_id)
    except:
        removed_relationships = None