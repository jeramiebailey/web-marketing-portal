from rest_framework.response import Response
from rest_framework import mixins, status, viewsets
from rest_framework.views import APIView
from .serializers import InitializeWPBuildSerializer, ConfirmCompleteWPBuildSerializer, WebAppSerializer, ChildThemeSerializer, GenerateS3DownloadSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from client_onboarding.models import WebsiteBuild
from .utils import create_github_repo, create_backup_directory, initialize_wp_project, create_subdomain, create_mail_records
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from .models import ChildTheme, WebApp
from rest_framework.decorators import action
from rest_framework_guardian import filters
from api.permissions import CustomObjectPermissions
from .utils import generate_s3_download_link, execute_remote_command
from django.db.models import Max
import environ
import re
import uuid

env = environ.Env()
staging_domain = env('STAGING_DOMAIN')
bucket_name = env('WP_STAGING_BUCKET')
staging_secret_key = env('STAGING_SERVER_SECRET_KEY')

def generate_wp_password(length=32):
    random = str(uuid.uuid4())
    random = random.upper()
    random = random.replace("-","")
    return random[0:length]

class ChildThemeViewSet(viewsets.ModelViewSet):
    queryset = ChildTheme.objects.all()
    serializer_class = ChildThemeSerializer
    permission_classes = (IsAuthenticated,)

class WebAppViewSet(viewsets.ModelViewSet):
    queryset = WebApp.objects.select_related('organization', 'new_build').filter(scheduled_for_deletion=False)
    serializer_class = WebAppSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    @action(detail=True, methods=['get'])
    def status_check(self, request, pk=None):
        web_app = self.get_object()
        try:
            #webserver_status = web_app.check_webserver_status()
            wordpress_status = web_app.check_wordpress_status()
            website_status = web_app.check_website_status()
            errors = None
        except Exception as e:
            errors = f'{e.message}, {e.type}'

        if errors is None:
            if website_status == 0:
                website_status = True
            else:
                website_status = False
            status_response = {
                #'webserver_status': webserver_status,
                'wordpress_status': wordpress_status,
                'website_status': website_status,
            }
            return Response(status_response, status=status.HTTP_200_OK)
        else:
            return Response({'errors': errors},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def backup(self, request, pk=None):
        web_app = self.get_object()
        invoke_backup = web_app.backup()
        if invoke_backup is True:
            serializer = self.get_serializer(web_app, many=False)
            return Response({'status': 'Backup Successful', 'application': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'errors': 'Backup Failed'},
                            status=status.HTTP_409_CONFLICT)

    @action(detail=True, methods=['post'])
    def start_server(self, request, pk=None):
        web_app = self.get_object()
        invoke_start_app = web_app.start_app()
        if invoke_start_app is True:
            return Response({'status': 'Application Successfully Started'}, status=status.HTTP_200_OK)
        else:
            return Response({'errors': 'Failed to start application'},
                            status=status.HTTP_409_CONFLICT)
    
    @action(detail=True, methods=['post'])
    def stop_server(self, request, pk=None):
        web_app = self.get_object()
        invoke_stop_app = web_app.stop_app()
        if invoke_stop_app is True:
            return Response({'status': 'Application Successfully Stopped'}, status=status.HTTP_200_OK)
        else:
            return Response({'errors': 'Failed to stop application'},
                            status=status.HTTP_409_CONFLICT)
        
    @action(detail=True, methods=['get'])
    def list_db_backups(self, request, pk=None):
        web_app = self.get_object()
        db_backups = web_app.get_db_backups()
        if db_backups:
            try:
                found_backups = db_backups[::-1]
            except:
                found_backups = None

            if found_backups:
                return Response(db_backups[::-1], status=status.HTTP_200_OK)
            else:
                # return Response({
                #     'message': 'There are no current database backups.',
                #     'noBackups': True
                # }, status=status.HTTP_200_OK)
                return Response({'errors': 'Failed to fetch DB backups'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'errors': 'Failed to fetch DB backups'},
                            status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def list_codebase_backups(self, request, pk=None):
        web_app = self.get_object()
        codebase_backups = web_app.get_code_backups()
        if codebase_backups:
            try:
                found_backups = codebase_backups[::-1]
            except:
                found_backups = None
            if found_backups:
                return Response(codebase_backups[::-1], status=status.HTTP_200_OK)
            else:
                # return Response({
                #     'message': 'There are no current codebase backups.',
                #     'noBackups': True
                # }, status=status.HTTP_200_OK)
                return Response({'errors': 'Failed to fetch DB backups'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'errors': 'Failed to fetch codebase backups'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def delete_and_clean(self, request, pk=None):
        web_app = self.get_object()
        deleted_app = web_app.clean_app()
        if deleted_app:
            web_app.scheduled_for_deletion = True
            web_app.active = False
            web_app.save()
            return Response(WebAppSerializer(web_app).data, status=status.HTTP_200_OK)
        else:
            return Response({'errors': 'Failed to delete application'},
                            status=status.HTTP_400_BAD_REQUEST)

class GenerateS3Download(APIView):
    serializer_class = GenerateS3DownloadSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        serializer = GenerateS3DownloadSerializer(data=request.data)

        if serializer.is_valid():
            file_key = serializer.data.get('file_key')

            if file_key:
                try:
                    file_download = generate_s3_download_link(key=file_key, expiration=600)
                except:
                    file_download = None
            
            if file_download:
                return Response(
                                {
                                    "response": file_download,
                                }, status=status.HTTP_200_OK)
            else:
                return Response(
                                {
                                    "response": "Key not valid",
                                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(
                                {
                                    "response": "Missing Key",
                                    "errors": serializer.errors,
                                }, status=status.HTTP_400_BAD_REQUEST)

            
class InitializeWPBuild(APIView):
    serializer_class = InitializeWPBuildSerializer

    def get(self, request, format=None):
        return Response({"message": "Endpoint successfully hit"})

    def post(self, request, format=None):
        serializer = InitializeWPBuildSerializer(data=request.data)
        if request.user.has_perm('client_onboarding.initialize_websitebuild') or request.user.is_staff:

            if serializer.is_valid():
                website_build = serializer.data.get('website_build')
                child_theme = serializer.data.get('child_theme')
                # repo_name = serializer.data.get('repo_name')
                # site_url = serializer.data.get('site_url')

                # if the website build parameter was passed
                if website_build:
                    try:
                        build = WebsiteBuild.objects.get(id=website_build)
                    except:
                        build = None
                
                # if there is a valid website build object
                if build:
                    if build.organization.domain:
                        # format the repo name depending on http or https
                        if build.organization.domain[4] == 's':
                            new_repo = build.organization.domain[8:]
                        else:
                            new_repo = build.organization.domain[7:]  
                        # if the domain contains a backslash remove it
                        if new_repo[-1] == '/':
                            new_repo = new_repo[:-1]

                        new_url = build.organization.domain
                        build_alias = new_repo
                        if 'www.' in build_alias:
                            build_alias = build_alias[4:]
                        if '.com' in build_alias or '.net' in build_alias or '.org' in build_alias:
                            build_alias = build_alias[:-4]
                        new_description = build.label
                        child_theme_object = ChildTheme.objects.get(id=child_theme)
                        formatted_build_alias = re.sub(r"[^a-zA-Z0-9]+", '', build_alias)
                        new_db_name = f'{formatted_build_alias}_db'

                        # Create new WebApp instance
                        new_application = WebApp.objects.create(
                            organization=build.organization,
                            new_build=build,
                            alias=build_alias,
                            site_name=new_repo,
                            staging_url=f'http://{build_alias}.{staging_domain}',
                            production_url=new_url,
                            staging_db_name=f'{formatted_build_alias}_db',
                            staging_wordpress_db_user=f'{formatted_build_alias}_mysql_admin',
                            staging_wordpress_db_password=generate_wp_password(),
                        )
                        new_application.save()

                        data = {
                            'name': new_repo,
                            'description': new_description,
                            'private': 'true',
                        }

                        # create github repo
                        create_repo_response = create_github_repo(data=data)
                        # create new s3 bucket for backups
                        create_directory_response = create_backup_directory(new_repo)
                        # create new subdomain in Route 53
                        create_subdomain_response = create_subdomain(new_repo, build_alias)
                        # create new Mailgun domain and add records in Route 53
                        create_mail_records_response = create_mail_records(new_repo, build_alias)

                        # check if github errors, if not save github repo to Web App instance
                        try:
                            github_errors = create_repo_response["errors"]
                        except:
                            github_errors = None

                        try:
                            # new_github_repo = create_repo_response["ssh_url"]
                            new_github_repo = create_repo_response
                        except:
                            new_github_repo = None

                        if new_github_repo:
                            new_application.github_repo = new_github_repo
                            new_application.save()

                        # check if CNAME record and save github repo to Web App instance
                        try:
                            subdomain_response_code = create_subdomain_response['ResponseMetadata']['HTTPStatusCode']
                        except:
                            subdomain_response_code = None
                        if subdomain_response_code == 200:
                            new_application.s3_directory = f'{bucket_name}/{new_repo}_backups/'
                            new_application.save()

                        # if no errors initialize wordpress build
                        if not github_errors and subdomain_response_code == 200:
                            initialize_remote = initialize_wp_project(
                                virtual_host=f'{build_alias}.{staging_domain}',
                                app_id=new_application.uuid,
                                build_name=new_repo,
                                site_url=f'http://{build_alias}.{staging_domain}',
                                site_url_no_http=f'{build_alias}.{staging_domain}',
                                # alias=build.label,
                                alias=build.organization.dba_name,
                                site_alias=build_alias,
                                child_theme_verbose=child_theme_object.theme_name,
                                child_theme_file=child_theme_object.zip_file,
                                child_theme_name=child_theme_object.zip_filename,
                                # github_repo=create_repo_response["ssh_url"],
                                github_repo=create_repo_response,
                                s3_directory=new_application.s3_directory,
                                staging_db_name=new_application.staging_db_name,
                                staging_wordpress_db_user=new_application.staging_wordpress_db_user,
                                staging_wordpress_db_password=new_application.staging_wordpress_db_password
                            )

                            try:
                                build.staging_url = f'http://{build_alias}.{staging_domain}'
                                build.save()
                            except:
                                print('There was an error saving build staging URL')

                        if github_errors:
                            return Response(
                                {"response": "Bad request", "errors": github_errors}, 
                                status=status.HTTP_400_BAD_REQUEST)
                        elif not subdomain_response_code == 200:
                            try:
                                error_message = create_subdomain_response['ResponseMetadata'].message
                            except:
                                error_message = "There was a problem creating the Route53 domain"
                            return Response(
                                {"response": "Bad request", "errors": error_message}, 
                                status=status.HTTP_400_BAD_REQUEST)
                        else:
                            # change_perms = execute_remote_command(new_application.site_name, 'sudo chmod -R 777 wordpress/wp-content/')
                            return Response(
                                {
                                    "response": "Website Build Initialization Started", 
                                    "new_application": WebAppSerializer(new_application).data,
                                    "github_response": create_repo_response,
                                    "s3_response": create_directory_response,
                                    "route53_response": create_subdomain_response,
                                }, status=status.HTTP_201_CREATED)
                    else:
                        new_repo = None
                        return Response({"response": "Organization does not have a domain yet. Please specify the organization\'s domain name before initializing"}, status=status.HTTP_400_BAD_REQUEST)

                else:
                    return Response({"response": "Website Build Not Found"}, status=status.HTTP_404_NOT_FOUND)
            
            else:   
                return Response({"response": "Not valid", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({'Unauthorized': "You do not have permissions to do that."},
                        status=status.HTTP_401_UNAUTHORIZED)

class ConfirmCompleteWPBuild(APIView):
    serializer_class = ConfirmCompleteWPBuildSerializer
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response({"message": "To confirm this application has been successfuly initialized please pass the application_uuid and secret_key"})

    def post(self, request, format=None):
        serializer = ConfirmCompleteWPBuildSerializer(data=request.data)

        if serializer.is_valid():
            application_uuid = serializer.data.get('application_uuid')
            secret_key = serializer.data.get('secret_key')

            if staging_secret_key == secret_key:
                try:
                    application = WebApp.objects.get(uuid=application_uuid)
                except:
                    application = None
            
                if application:
                    application.initialization_complete = True
                    application.save()

                    return Response(
                                {
                                    "response": "Website Build Initialization Success",
                                }, status=status.HTTP_200_OK)
                
                return Response(
                                {
                                    "response": "Application Not Found",
                                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response(
                                {
                                    "response": "Unauthorized",
                                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(
                                {
                                    "response": "Invalid Request",
                                    "errors": serializer.errors,
                                }, status=status.HTTP_400_BAD_REQUEST)

