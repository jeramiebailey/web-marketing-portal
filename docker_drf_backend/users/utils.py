from django.contrib.auth import get_user_model
from content_management.models import Writer

User = get_user_model()

def remove_user_relationships(user_id):
    user = User.objects.get(id=user_id)
    if user:
        output = {}
        writer_obj = Writer.objects.get(user=user)

        articles_to_edit = user.contentEditor.all()
        if articles_to_edit:
            for article in articles_to_edit:
                article.editor = None
                article.save()
            output['articles_to_edit'] = articles_to_edit.count()
        articles_to_post = user.contentPoster.all()
        if articles_to_post:
            for article in articles_to_post:
                article.poster = None
                article.save()
            output['articles_to_post'] = articles_to_post.count()
        articles_to_approve = user.contentApprover.all()
        if articles_to_approve:
            for article in articles_to_approve:
                article.final_approver = None
                article.save()
            output['articles_to_approve'] = articles_to_approve.count()
        articles_to_lead = user.contentLead.all()
        if articles_to_lead:
            for article in articles_to_lead:
                article.lead = None
                article.save()
            output['articles_to_lead'] = articles_to_lead.count()
        templates_to_edit = user.defaultEditor.all()
        if templates_to_edit:
            for template in templates_to_edit:
                template.editor = None
                template.save()
            output['templates_to_edit'] = templates_to_edit.count()
        templates_to_post = user.defaultPoster.all()
        if templates_to_post:
            for template in templates_to_post:
                template.poster = None
                template.save()
            output['templates_to_post'] = templates_to_post.count()
        templates_to_approve = user.defaultApprover.all()
        if templates_to_approve:
            for template in templates_to_approve:
                template.final_approver = None
                template.save()
            output['templates_to_approve'] = templates_to_approve.count()
        templates_to_lead = user.defaultLead.all()
        if templates_to_lead:
            for template in templates_to_lead:
                template.lead = None
                template.save()
            output['templates_to_lead'] = templates_to_lead.count()

        if writer_obj:
            articles_to_write = writer_obj.contentWriter.all()
            if articles_to_write:
                for article in articles_to_write:
                    article.writer = None
                    article.save()
                output['articles_to_write'] = articles_to_write.count()
            templates_to_write = writer_obj.defaultWriter.all()
            if templates_to_write:
                for template in templates_to_write:
                    template.writer = None
                    template.save()
                output['templates_to_write'] = templates_to_write.count()
        
        return output
    else:
        return None