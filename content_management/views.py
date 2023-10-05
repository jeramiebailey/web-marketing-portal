from rest_framework import viewsets, permissions
from django.conf import settings
from docker_drf_backend.users.models import User, UserOrgRole, Preferences
from rest_framework.response import Response
from rest_framework import mixins, status, viewsets
from .models import Feedback, ContentArticle, Writer, ContentProject, ArticleTemplate, ContentArticleHistorySet, PlanningYearMonth, ContentProject
from .serializers import ArticleSerializer, FeedbackSerializer, DetailedFeedbackSerializer, ReassignArticlesSerializer, ContentArticleHistorySetSerializer
from api.permissions import CustomObjectPermissions
from organizations.models import Organization
from content_management.utils import reassign_articles
from rest_framework_guardian import filters
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework.views import APIView
from dateutil.relativedelta import *
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from rest_framework.decorators import action

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = ContentArticle.objects.all().order_by('client', 'milestone')
    serializer_class = ArticleSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_queryset(self):
        queryset = super(ArticleViewSet, self).get_queryset()
        queryset = queryset.filter(archived=False)
        queryset = ArticleSerializer.setup_eager_loading(queryset)
        year = self.request.query_params.get('year', None)
        month = self.request.query_params.get('month', None)
        assigned = self.request.query_params.get('assigned', None)
        isLead = self.request.query_params.get('isLead', None)
        client = self.request.query_params.get('client', None)
        archives = self.request.query_params.get('archives', None)
        user = self.request.query_params.get('user', None) 
        project = self.request.query_params.get('project', None)
        organization = self.request.query_params.get('organization', None)
        content_status = self.request.query_params.get('contentStatus', None)
        due_date_status = self.request.query_params.get('dueDateStatus', None)

        if year is not None and month is not None and organization is not None:
            queryset = queryset.filter(planning_year_month__year=year, planning_year_month__month=month, client__id=organization)

        elif year is not None and month is not None:
            queryset = queryset.filter(planning_year_month__year=year, planning_year_month__month=month)
        
        elif project is not None:
            queryset = queryset.filter(project__id=project)
        
        elif organization is not None:
            queryset = queryset.filter(client__id=organization)

        if isLead:
            requesting_user = self.request.user
            applicable_statuses = [2, 3, 4, 5, 6, 7, 8]
            self.permission_classes = (IsAuthenticated,)
            self.filter_backends = ()

            queryset = queryset.filter(
                Q(editor=requesting_user) |
                Q(writer__user=requesting_user) |
                Q(poster=requesting_user) |
                Q(final_approver=requesting_user),
                Q(planning_year_month__isnull=False) |
                Q(project__isnull=False),
                status__order__in=applicable_statuses,
                writer__isnull=False,
                archived=False
            ).distinct().order_by('status__order', 'planning_year_month__year', 'planning_year_month__month', 'milestone', 'writer_planned_duedate')

            # final_review = queryset.filter(final_approver=requesting_user, status__order=7)
            final_review = queryset.filter(final_approver=requesting_user, status__uid='final_review')

            return queryset

        if client:
            self.permission_classes = (IsAuthenticated,)
            self.filter_backends = ()
            user_orgs = Organization.objects.prefetch_related(
                'user_default_organization', 
                'organization_requirements',
                ).filter(user_roles__user=self.request.user)
            last_six_months = PlanningYearMonth.objects.all().order_by('-year', '-month')[:6]
            if archives:
                queryset = queryset.filter(client__in=user_orgs, writer__isnull=False).order_by('status')
            else:
                queryset = queryset.filter(client__in=user_orgs, planning_year_month__in=last_six_months, writer__isnull=False).order_by('status')

            # final_review = queryset.filter(final_approver=self.request.user, status__order=7)
            final_review = queryset.filter(final_approver=self.request.user, status__uid='final_review')
            
            return queryset

        if assigned and not user:
            requesting_user = self.request.user
            applicable_statuses = [2, 3, 4, 5, 6, 7, 8]
            self.permission_classes = (IsAuthenticated,)
            self.filter_backends = ()

            queryset = queryset.filter(
                Q(editor=requesting_user) |
                Q(writer__user=requesting_user) |
                Q(poster=requesting_user) |
                Q(final_approver=requesting_user),
                Q(planning_year_month__isnull=False) |
                Q(project__isnull=False),
                status__order__in=applicable_statuses,
                writer__isnull=False,
                archived=False
            ).distinct().order_by('status__order', 'planning_year_month__year', 'planning_year_month__month', 'milestone', 'writer_planned_duedate')

            # final_review = queryset.filter(final_approver=requesting_user, status__order=7)
            final_review = queryset.filter(final_approver=requesting_user, status__uid='final_review')

            return queryset

        elif assigned and user:
            applicable_statuses = [2, 3, 4, 5, 6, 7, 8]

            queryset = queryset.filter(
                Q(editor=user) |
                Q(writer__user=user) |
                Q(poster=user) |
                Q(final_approver=user),
                Q(planning_year_month__isnull=False) |
                Q(project__isnull=False),
                status__order__in=applicable_statuses,
                writer__isnull=False,
                archived=False
            ).distinct().order_by('status__order', 'planning_year_month__year', 'planning_year_month__month', 'milestone', 'writer_planned_duedate')

            return queryset


        if content_status:
            print(f'content_status is: {content_status}')
            # queryset = queryset.filter(
            #     Q(planning_year_month__isnull=False) | Q(project__isnull=False),
            #     status__order=content_status, archived=False, writer__isnull=False
            # )
            queryset = queryset.filter(
                Q(planning_year_month__isnull=False) | Q(project__isnull=False),
                status__uid=content_status, archived=False, writer__isnull=False
            )
            print(f'queryset count is: {queryset.count()}')

            return queryset

        return queryset

class ContentArticleHistorySetViewSet(viewsets.ModelViewSet):
    queryset = ContentArticleHistorySet.objects.select_related('status').all()
    serializer_class = ContentArticleHistorySetSerializer

    def get_queryset(self):
        queryset = super(ContentArticleHistorySetViewSet, self).get_queryset()
        queryset = ContentArticleHistorySetSerializer.setup_eager_loading(queryset)

        weeks_back = self.request.query_params.get('weeksBack', None)

        if weeks_back:
            try:
                weeks_back_int = int(weeks_back)
            except:
                weeks_back_int = None

            if weeks_back_int:
                now = timezone.now()
                stop_date = now + relativedelta(weeks=-weeks_back_int, days=-1)
                queryset = queryset.filter(as_of_date__gte=stop_date)

        return queryset

    @action(detail=True, methods=['post'])
    def populate_set(self, request, pk=None):
        article_history_set = self.get_object()
        if self.request.user.is_staff:
            if article_history_set:
                try:
                    article_history_set.populate_set(delay=False)
                    did_update = True
                except:
                    did_update = False
            
                if did_update:
                    updated_article_history_set = ContentArticleHistorySet.objects.get(pk=article_history_set.id)
                    response = ContentArticleHistorySetSerializer(updated_article_history_set)

                    return Response(response.data, status=status.HTTP_200_OK)

                else:
                    return Response('There was an error updating the ContentArticleHistorySet', status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response('Could not find the ContentArticleHistorySet', status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response('You are not authorized to make this request', status=status.HTTP_401_UNAUTHORIZED)


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.select_related('article', 'given_by').all()
    serializer_class = FeedbackSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            data = kwargs["data"]
            
            if isinstance(data, list):
                kwargs["many"] = True

        return super(FeedbackViewSet, self).get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        detailed = self.request.query_params.get('detailed', None)

        if detailed:
            serializer = DetailedFeedbackSerializer
            return serializer
        else:
            serializer = FeedbackSerializer
            return serializer

    def get_queryset(self):
        article = self.request.query_params.get('article', None)
        queryset = super(FeedbackViewSet, self).get_queryset()

        if article is not None:
            try:
                article_feedback = queryset.filter(article__id=article)
            except:
                article_feedback = None
        
            if article_feedback:
                queryset = article_feedback
            else:
                queryset = queryset.none()

            return queryset
        
        return queryset

    def perform_create(self, serializer):
        feedback = serializer.save(given_by=self.request.user)
        assign_perm('view_feedback', self.request.user, feedback)
        feedback.save()


class ReassignArticles(APIView):
    serializer_class = ReassignArticlesSerializer

    def post(self, request, format=None):
        serializer = ReassignArticlesSerializer(data=request.data)
        if request.user.has_perm('content_management.delete_contentarticle'):

            if serializer.is_valid():
                prevUserId = serializer.data.get('prevUserId')
                newUserId = serializer.data.get('newUserId')

                try:
                    prevUser = User.objects.get(id=prevUserId)
                except:
                    prevUser = None
                    return Response({"message": "Previous user not found"}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    newUser = User.objects.get(id=newUserId)
                except:
                    newUser = None
                    return Response({"message": "New user not found"}, status=status.HTTP_400_BAD_REQUEST)

                
                if prevUser and newUser:
                    reassign_articles_output = reassign_articles(prevUser.id, newUser.id) 
                    print('reassign_articles_output', reassign_articles_output)
                    return Response(reassign_articles_output, status=status.HTTP_200_OK)

                else:
                    return Response({"message": "Could not find Previous User and/or New User object"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Serializer not valid"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'Unauthorized': "You do not have permissions to do that."},
                    status=status.HTTP_401_UNAUTHORIZED)
