import os
import environ
import json
import requests
from django.utils import timezone

env = environ.Env()
google_api_key = env('GOOGLE_API_KEY')

def get_page_speed_insights(domain, strategy='desktop', categories=['performance', 'seo', 'best-practices', 'accessibility']):
    categories_output = ''
    for i, category in enumerate(categories):
        if i == 0:
            categories_output += f'category={category}'
        else:
            categories_output += f'&category={category}'

    url = f'https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={domain}&key={google_api_key}&strategy={strategy}&{categories_output}'
    response = requests.get(url)
    data = json.loads(response.text)

    if data:
        return data 

    else:
        print('No data was found')
        return None


def parse_page_speed_insights(domain, strategy='desktop', categories=['performance', 'seo', 'best-practices', 'accessibility']):
    now = timezone.now()
    insight_data = get_page_speed_insights(domain, strategy, categories)

    if insight_data:
        page_speed_data = {}
        domain = insight_data.get('id')
        loading_experience = insight_data.get('loadingExperience')
        lighthouse_result = insight_data.get('lighthouseResult')
        timestamp = insight_data.get('analysisUTCTimestamp')

        page_speed_data['domain'] = domain

        if lighthouse_result:
            config_settings = lighthouse_result.get('configSettings')
            audits = lighthouse_result.get('audits')
            categories = lighthouse_result.get('categories')

            if config_settings:
                audit_type = config_settings.get('emulatedFormFactor')
                if audit_type:
                    page_speed_data['audit_type'] = audit_type

            if categories:
                category_scores = {}
                category_scores['aggregate_score'] = 0
                for key in categories.keys():
                    category = categories.get(key)
                    if category:
                        score = category.get('score')
                        if score:
                            category_scores[key] = score
                            category_scores['aggregate_score'] += score
                            
                category_scores['average_score'] = round(category_scores['aggregate_score'] / len(categories.keys()), 2)
                page_speed_data['scores'] = category_scores

            if audits:
                audit_parameters = ['speed-index', 'first-contentful-paint', 'first-meaningful-paint', 'interactive']
                page_speed_audits = {}
                for parameter in audit_parameters:
                    parameter_key = audits.get(parameter)
                    if parameter_key:
                        score = parameter_key.get('score')
                        if score:
                            page_speed_audits[parameter] = score

                page_speed_data['audits'] = page_speed_audits
            

            page_speed_data['timestamp'] = now.strftime("%d-%m-%Y %H:%M:%S")

            print('page_speed_data is: ', page_speed_data)
            return page_speed_data
        
        else:
            print('Could not get light house result')
            return None

    else:
        print('Could not fetch page speed data')
        return None