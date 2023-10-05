from docker_drf_backend.users.models import User
from content_management.models import ArticleTemplate, ContentArticle
from organizations.models import Organization

def import_orgs():
    all_temps = ArticleTemplate.objects.all()

    for temp in all_temps:
        print('working')
        try:
            org_name = temp.production_notes
            print(org_name)
        except:
            org_name = None
            print(org_name)
        if org_name:
            try:
                org = Organization.objects.get(dba_name__icontains=org_name)
            except:
                org = None
        if org:
            temp.client = org
            temp.save()
            print('success')
