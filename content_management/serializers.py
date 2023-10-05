from rest_framework import serializers
from docker_drf_backend.users.models import User, Preferences, UserOrgRole
from .models import Feedback
from content_management.models import Writer, ContentArticle, ContentArticleHistorySet
from docker_drf_backend.users.serializers import BriefUserDetailsSerializer, QuickUserDetailsSerializer
from api.serializers import WriterSerializer, ContentTypeSerializer, BriefPlanningYearMonthSerializer, BriefContentProjectSerializer, ContentStatusSerializer

class ArticleSerializer(serializers.ModelSerializer):
    contentComments = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    
    class Meta:
        model = ContentArticle
        fields = ('__all__')
        

    def to_representation(self, instance):
        response = super(ArticleSerializer, self).to_representation(instance)
        # response['is_late'] = instance.is_late
        return response

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related(
            'writer',
            'client',
            'poster',
            'lead',
            'editor',
            'planning_year_month',
            'project',
            'content_type',
            'status',
            'final_approver'
        )

        queryset = queryset.prefetch_related(
            'content_type',
            'contentComments',
            'writer__user',
            # 'keywords',
            'channels',
            )

        return queryset
    
    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        channels = validated_data.pop('channels')
        keywords = validated_data.pop('keywords')
        content_article = ContentArticle.objects.create(**validated_data)
        content_article.channels.set(channels)
        content_article.keywords.set(keywords)
        content_article.save()

        return content_article

    def update(self, instance, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        content_article = ContentArticle.objects.get(id=instance.id)
        channels = validated_data.pop('channels')
        keywords = validated_data.pop('keywords')
        try:
            instance = ContentArticle(date_created=instance.date_created, **validated_data)
        except:
            instance = ContentArticle(id=instance.id, date_created=instance.date_created, **validated_data)
        instance.channels.set(channels)
        instance.keywords.set(keywords)

        if content_article.google_doc:
            new_doc_url = validated_data.get('google_doc')
            if new_doc_url == None:
                instance.google_doc = content_article.google_doc

        if content_article.scheduled_date:
            new_scheduled_date = validated_data.get('scheduled_date')
            if new_scheduled_date == None:
                instance.scheduled_date = content_article.scheduled_date

        if content_article.writer_planned_duedate:
            new_writer_planned_duedate = validated_data.get('writer_planned_duedate')
            if new_writer_planned_duedate == None:
                instance.writer_planned_duedate = content_article.writer_planned_duedate

        instance.save()

        return instance

class FeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = ('__all__')

class DetailedFeedbackSerializer(serializers.ModelSerializer):
    # article = ContentArticleSerializer(read_only=True, many=False)
    given_by = BriefUserDetailsSerializer(read_only=True, many=False)

    class Meta:
        model = Feedback
        fields = ('__all__')


class ReassignArticlesSerializer(serializers.Serializer):
    prevUserId = serializers.IntegerField()
    newUserId = serializers.IntegerField()

class BriefContentArticleSerializer(serializers.ModelSerializer):
    writer = WriterSerializer(read_only=True, many=False)
    editor = QuickUserDetailsSerializer(read_only=True, many=False)
    poster = QuickUserDetailsSerializer(read_only=True, many=False)
    lead = QuickUserDetailsSerializer(read_only=True, many=False)
    final_approver = QuickUserDetailsSerializer(read_only=True, many=False)
    content_type = ContentTypeSerializer(read_only=True, many=False)
    planning_year_month = BriefPlanningYearMonthSerializer(read_only=True, many=False)
    project = BriefContentProjectSerializer(read_only=True, many=False)
    status = ContentStatusSerializer(read_only=True, many=False)

    class Meta:
        model = ContentArticle
        fields = (
            'planning_year_month',
            'project',
            'title',
            'content_type',
            'status',
            'client',
            'writer',
            'editor',
            'poster',
            'final_approver',
            'lead',
            'min_word_count',
            'focus_keyword_plaintext',
            'milestone',
            'duedate_write',
            'duedate_rewrite',
            'duedate_edit',
            'duedate_reedit',
            'duedate_finalreview',
            'duedate_qapost',
            'duedate_schedulepost',
            'duedate_golive',
            'archived',
            'date_created',
            'last_update',
        )

class ContentArticleHistorySetSerializer(serializers.ModelSerializer):
    status = ContentStatusSerializer(read_only=True, many=False)
    class Meta:
        model = ContentArticleHistorySet
        fields = ('__all__')

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('status')

        return queryset