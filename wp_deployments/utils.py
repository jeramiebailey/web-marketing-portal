import requests
import environ
import json
import boto3
from botocore.exceptions import ClientError
import logging
from fabric import Connection
from django.core.files import File
import subprocess
from django.conf import settings
import tempfile 
import requests 
import os
import errno
import shutil
from github import Github

env = environ.Env()
github_token = env('GITHUB_TOKEN')
aws_access_key_id = env('AWS_ACCESS_KEY_ID')
aws_secret_access_key = env('AWS_SECRET_ACCESS_KEY')
bucket_name = env('WP_STAGING_BUCKET')
staging_ip = env('STAGING_SERVER_IP')
staging_username = env('STAGING_SERVER_USER')
staging_ssh_key = env('STAGING_SERVER_SSH_KEY')
hosted_zone_id = env('STAGING_HOSTED_ZONE_ID')
staging_domain = env('STAGING_DOMAIN')
current_env = os.environ.get('DJANGO_SETTINGS_MODULE') 
secure_mail_hosted_zone_id = env('SECURE_MAIL_HOSTED_ZONE_ID')
mailgun_api_key = env('MAILGUN_API_KEY')
root_directory = settings.ROOT_DIR
debug = settings.DEBUG

def create_github_repo(data):
    # url = f'https://api.github.com/orgs/321webmarketing/repos?access_token={github_token}'

    # r = requests.post(url=url, json=data)

    # response = r.json()
    
    # return response
    
    repo_name = data["name"]
    repo_description = data["description"]
    
    github = Github(github_token)
    org = github.get_organization("321webmarketing")
    org_repo = org.create_repo(repo_name, description=repo_description, private=True)

    new_repo = org.get_repo(repo_name)
    
    ssh_url = f'git@github.com:{new_repo.full_name}.git'
    
    return ssh_url
    


def delete_github_repo(repo_name):
    # url = f'https://api.github.com/repos/321webmarketing/{repo_name}?access_token={github_token}'

    # r = requests.delete(url=url)

    # return r
    
    github = Github(github_token)
    org = github.get_organization("321webmarketing")
    repo_to_be_deleted = org.get_repo(repo_name)
    
    repo_to_be_deleted.delete()
    
    return True

def create_backup_directory(build_name):
    s3 = boto3.client('s3')
    directory_name = f'{build_name}_backups/'
    db_directory = f'{directory_name}db/'
    codebase_directory = f'{directory_name}codebase/'

    try:
        created_directory = s3.put_object(Bucket=bucket_name, Key=(directory_name))
        created_backup_directory = s3.put_object(Bucket=bucket_name, Key=(db_directory))
        created_codebase_directory = s3.put_object(Bucket=bucket_name, Key=(codebase_directory))
        return created_directory
    except ClientError as e:
        error = logging.error(e)
        return error

def delete_backup_object(key):
    s3 = boto3.client('s3')

    try:
        deleted_backup = s3.delete_object(Bucket=bucket_name, Key=key)
        return deleted_backup
    except ClientError as e:
        error = logging.error(e)
        return error

def get_app_db_backups(build_name):
    s3 = boto3.client('s3')
    directory_name = f'{build_name}_backups/'
    db_directory = f'{directory_name}db/'

    try:
        db_backups = s3.list_objects_v2(Bucket=bucket_name, Prefix=db_directory, StartAfter=db_directory)
        try:
            contents = db_backups['Contents']
        except:
            contents = {"No Current Database Backups"}
        return contents
    except ClientError as e:
        error = logging.error(e)
        return error

def get_app_codebase_backups(build_name, app_id):
    s3 = boto3.client('s3')
    directory_name = f'{build_name}_backups/'
    codebase_directory = f'{directory_name}codebase/'
    dir_length = len(codebase_directory) - 1

    try:
        codebase_backups = s3.list_objects_v2(Bucket=bucket_name, Prefix=codebase_directory, StartAfter=codebase_directory)
        try:
            contents = codebase_backups['Contents']
        except:
            contents = {"No Current Codebase Backups"}
        return contents
    except ClientError as e:
        error = logging.error(e)
        return error


def generate_s3_download_link(key, expiration):
    s3 = boto3.client('s3')
    try:
        response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': key},
                                                    ExpiresIn=expiration)
        print(response)
    except ClientError as e:
        logging.error(e)
        return None

    return response

def create_subdomain(build_name, subdomain_name):
    client = boto3.client('route53')
    zone_id = hosted_zone_id
    subdomain = f'{subdomain_name}.{staging_domain}'
    try:
        response = client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch= {
						'Comment': f'Adding subdomain for {build_name}',
						'Changes': [
							{
                                'Action': 'UPSERT',
                                'ResourceRecordSet': {
                                    'Name': subdomain,
                                    'Type': 'A',
                                    'TTL': 300,
                                    'ResourceRecords': [{'Value': staging_ip}]
                                }
                            }
                        ]
		            })
        try:
            subdomain_response_code = response['ResponseMetadata']['HTTPStatusCode']
        except:
            subdomain_response_code = response['ResponseMetadata']
        return response
    except Exception as e:
        return e

def create_mailgun_domain(subdomain_name):
    mailgun_url = 'https://api.mailgun.net/v3/domains'
    domain_name = f'{subdomain_name}.secure-formsend.com'
    auth = ("api", mailgun_api_key)
    data = {
       "name":  domain_name
    }
    r = requests.post(url=mailgun_url, auth=auth, params=data)

    response = r.json()

    return response

def create_mail_records(build_name, subdomain_name):
    client = boto3.client('route53')
    zone_id = secure_mail_hosted_zone_id
    subdomain = f'{subdomain_name}.secure-formsend.com'

    try:
        new_domain = create_mailgun_domain(subdomain_name)
    except:
        new_domain = None

    if new_domain:
        try:
            receiving_dns_records = new_domain["receiving_dns_records"]
            sending_dns_records = new_domain["sending_dns_records"]
        except:
            receiving_dns_records = None
            sending_dns_records = None

        if receiving_dns_records and sending_dns_records:
            dns_changes = []

            ## Receiving Records
            receiving_changes = {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': subdomain,
                    'Type': 'MX',
                    "TTL": 300,
                    'ResourceRecords': []
                }
            }

            for receiving_record in receiving_dns_records:
                value = {
                    'Value': f'10 {receiving_record["value"]}'
                }
                receiving_changes["ResourceRecordSet"]["ResourceRecords"].append(value)

            dns_changes.append(receiving_changes)

            ## Sending Records
            for sending_record in sending_dns_records:
                if sending_record["record_type"] == 'CNAME':
                    sending_record_value = f"{sending_record['value']}"
                else:
                    sending_record_value = f"\"{sending_record['value']}\""
                sending_record_change = {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': f"{sending_record['name']}",
                        'Type': f"{sending_record['record_type']}",
                        "TTL": 300,
                        'ResourceRecords': [{'Value': sending_record_value}]
                    }
                }
                dns_changes.append(sending_record_change)
            

            try:
                response = client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch= {
                                'Comment': f'Adding mail records for {build_name}',
                                'Changes': dns_changes
                            })
                try:
                    mail_record_response_code = response['ResponseMetadata']['HTTPStatusCode']
                except:
                    mail_record_response_code = response['ResponseMetadata']
                return response
            except Exception as e:
                return e

def initialize_wp_project(
    virtual_host,
    build_name, 
    site_url, 
    site_url_no_http,
    alias,
    site_alias,
    child_theme_verbose,
    child_theme_file, 
    child_theme_name, 
    staging_db_name,
    staging_wordpress_db_user,
    staging_wordpress_db_password,
    github_repo, 
    s3_directory,
    app_id
    ):
    c = Connection(host=staging_ip, user=staging_username, connect_kwargs={
        "key_filename": f"./{staging_ssh_key}",
    })
    run = c.run
    sites_directory = "~/sites"
    site_url_non_https = site_url_no_http
    f = open('staging.env', 'r')
    staging_env_content = f.read()
    nl = '\n'
    wp_create_github_repo = 'git@github.com:321webmarketing/wp_docker_create.git'
    if not debug:
        wp_create_github_repo_branch = 'master'
    else:
        wp_create_github_repo_branch = 'development'

    print('wp_create_github_repo_branch is: ', wp_create_github_repo_branch)

    run(f"cd {sites_directory}; \
        mkdir {build_name} && cd {build_name}; git init; git pull {wp_create_github_repo} {wp_create_github_repo_branch}; \
        touch .env; \
        mkdir .envs; mkdir .envs/.staging; touch .envs/.staging/.aws.env; \
        touch .envs/.staging/.mysql.env; touch .envs/.staging/.wordpress.env; \
        echo '{staging_env_content}' >> .env; \
        echo 'APPLICATION_ID={app_id}{nl} \
        VIRTUAL_HOST={virtual_host}{nl} \
        WORDPRESS_WEBSITE_TITLE={build_name}{nl} \
        WORDPRESS_WEBSITE_URL={site_url}{nl} \
        WORDPRESS_WEBSITE_URL_WITHOUT_HTTP={site_url_non_https}{nl} \
        ALIAS={alias}{nl} \
        SITE_ALIAS={site_alias}{nl} \
        CHILD_THEME_NAME={child_theme_verbose}{nl} \
        CHILD_THEME={child_theme_name[:-4]}{nl} \
        CHILD_THEME_ZIP={child_theme_name}{nl} \
        GIT_REPO={github_repo}{nl} \
        S3_BUCKET_DIRECTORY={s3_directory}{nl} \
        PROD_DB_WORDPRESS_USER={staging_wordpress_db_user}{nl} \
        PROD_DB_WORDPRESS_PASSWORD={staging_wordpress_db_password}{nl} \
        PROD_DB_NAME={staging_db_name}' >> .env")
    
    # inject child theme into remote directory
    # NOTE changed child_theme_file.file to child_theme_file.url. Might need to add if/else block for local/production
    # c.put(f"{child_theme_file.file}", remote=f"sites/{build_name}/compose/staging/toolbox/themes/")

    # logic to download remote file and store temporarily in system
    new_dir = tempfile.mkdtemp(dir=root_directory) 

    if current_env == 'config.settings.local':
        zip_file_url = f'http://localhost:8000{child_theme_file.url}'
    elif current_env == 'config.settings.production':
        zip_file_url = child_theme_file.url
    else:
        zip_file_url = None

    if zip_file_url:
        r = requests.get(zip_file_url)
        try:
            with open(f'{new_dir}/{child_theme_name[:-4]}', 'wb') as f:
                f.write(r.content)
            file_path = f'{new_dir}/{child_theme_name[:-4]}'
        except:
            file_path = None

        if file_path:
            c.put(file_path, remote=f"sites/{build_name}/compose/staging/toolbox/themes/")

            try:
                shutil.rmtree(new_dir)
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    raise
        else:
            print('error has occured')

    # inject boilerplate wordpress database into remote directory
    c.put(f"wp_boilerplate_v0.2.2.sql", remote=f"sites/{build_name}/compose/staging/toolbox/assets/")

    run(f"cd {sites_directory} && cd {build_name}; \
        make initialize")
 
    f.close()

def execute_local_command(command):
    try:
        executed_command = subprocess.call(command, shell=True)
    except:
        executed_command = None
    
    if executed_command is not None:
        return executed_command
    else:
        return False

def execute_remote_command(build_name, command):
    c = Connection(host=staging_ip, user=staging_username, connect_kwargs={
        "key_filename": f"./{staging_ssh_key}",
    })
    run = c.run
    sites_directory = "~/sites"

    try:
        executed_command = run(f"cd {sites_directory}/{build_name}; {command}")
    except:
        executed_command = None
    if executed_command:
        return True
    else:
        return False