from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from import_export import resources
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from simple_history.admin import SimpleHistoryAdmin



class PlanningYearMonthAdmin(GuardedModelAdmin):
    pass
class ContentProjectAdmin(GuardedModelAdmin):
    pass
class ContentTypeAdmin(GuardedModelAdmin):
    pass
class ContentChannelAdmin(GuardedModelAdmin):
    pass
class WriterAdmin(GuardedModelAdmin):
    pass
class ContentCommentsAdmin(GuardedModelAdmin):
    pass
class OrganizationRequirementsAdmin(GuardedModelAdmin):
    pass
class ParentKeywordAdmin(GuardedModelAdmin):
    pass
class KeywordAdmin(GuardedModelAdmin):
    pass
class KeywordMetaAdmin(GuardedModelAdmin):
    pass
class ContentRequirementAdmin(GuardedModelAdmin):
    pass

class ArticleTemplateResource(resources.ModelResource):

    class Meta:
        model = ArticleTemplate
        fields = (
            'title',
            'milestone',
            'production_notes',
            'min_word_count',
        )


# class ContentArticleResource(resources.ModelResource):
#     id = Field()
#     planning_year_month = Field()

#     class Meta:
#         model = ContentArticle

#     last_article_id = ContentArticle.objects.all().last().id

#     def dehydrate_id(self, book):
#         article_id = last_article_id + 1
#         last_article_id + 1
#         return article_id
    
#     def dehydrate_planning_year_month():
#         planning_year_month = PlanningYearMonth.objects.get_or_create(year=2019, month=10)
#         return planning_year_month


class ArticleTemplateAdmin(GuardedModelAdmin, ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ["title", "content_type", "client"]

    class Meta:
        resource_class = ArticleTemplateResource

class ContentStatusAdmin(GuardedModelAdmin):
    list_display = ["name", "uid", "status_type", "order", "color"]
    
class ContentArticleAdmin(GuardedModelAdmin, SimpleHistoryAdmin):
    list_display = ["title", "client", "writer", "editor", "final_approver"]
    history_list_display = ["status"]

class FeedbackAdmin(GuardedModelAdmin):
    list_display = ["article", "satisfaction", "given_by", "date_created", "approved"]
    search_fields = ['article__title', 'given_by__name']

class ContentArticleHistorySetAdmin(GuardedModelAdmin):
    list_display = ["id", "year", "month", "day", "as_of_date", "status", "incomplete_count", "complete_count", "late_count"]
    search_fields = ['as_of_date', 'status__name']

admin.site.register(PlanningYearMonth, PlanningYearMonthAdmin)
admin.site.register(ContentProject, ContentProjectAdmin)
admin.site.register(ContentStatus, ContentStatusAdmin)
admin.site.register(ContentType, ContentTypeAdmin)
admin.site.register(ContentChannel, ContentChannelAdmin)
admin.site.register(ParentKeyword, ParentKeywordAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(KeywordMeta, KeywordMetaAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(Writer, WriterAdmin)
admin.site.register(ContentArticle, ContentArticleAdmin)
admin.site.register(ContentComments, ContentCommentsAdmin)
admin.site.register(ArticleTemplate, ArticleTemplateAdmin)
admin.site.register(OrganizationRequirements, OrganizationRequirementsAdmin)
admin.site.register(ContentRequirement, ContentRequirementAdmin)
admin.site.register(ContentArticleHistorySet, ContentArticleHistorySetAdmin)
