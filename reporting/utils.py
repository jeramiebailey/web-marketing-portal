#!/usr/bin/env python
#!/bin/sh
from selenium import webdriver
import os
import environ
import os.path
import sys
import shutil
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common import keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from io import BytesIO
import time
from organizations.models import Organization
from config.settings.base import ROOT_DIR
from django.core.files import File
from tempfile import NamedTemporaryFile
from django.apps import apps
from docker_drf_backend.taskapp.celery import app
from reporting.clients import DataForSEORestClient
from random import Random
import traceback

env = environ.Env()

AHREFS_EMAIL = env('AHREFS_EMAIL')
AHREFS_PASSWORD = env('AHREFS_PASSWORD')
module_dir = os.path.dirname(__file__)

class AhrefsReportScraper(object):

    def __init__(self, report=None, reports=None, organization=None, account_urls=None, month=None, year=None):
        self.chrome_exe_path = '/usr/lib/chromium/chromedriver'
        self.ahrefs_email = AHREFS_EMAIL
        self.ahrefs_password = AHREFS_PASSWORD
        self.report = report
        self.reports = reports
        self.organization = organization
        self.account_urls = account_urls
        self.month = month
        self.year = year
        self.screenshot_dir_path = os.path.join(module_dir, 'screenshots')
        self.report_index = None

        if self.report is None and self.organization is None and self.account_urls is None:
            raise 'Please provide a MonthlyReport instance, an Organization instance or a list of account URLs'

    def setup(self):
        chrome_options = Options()  
        chrome_options.binary_location = '/usr/lib/chromium/chrome'
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("window-size=1400,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--shm-size=2g")
        chrome_options.add_argument("--remote-debugging-port=9222")

        chrome = webdriver.Chrome(options=chrome_options)
        self.chrome = chrome
        self.chrome.implicitly_wait(20)
        wait = WebDriverWait(chrome, 20)
        self.wait = wait

    def clean_account_url(self, account_url):
        if account_url.startswith('http'):
            if account_url[4] == 's':
                cleaned_account_url = account_url[8:]
            else:
                cleaned_account_url = account_url[7:]
        else:
            cleaned_account_url = account_url

        return cleaned_account_url


    # NOTE Old login method which navigates to the login url by finding the login button

    # def login(self):
    #     self.chrome.get('https://ahrefs.com/')
    #     time.sleep(2)
        
    #     try:
    #         signin_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/user/login/']")))
    #     except:
    #         signin_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/user/login']")))

    #     try:
    #         signin_button = self.chrome.find_element_by_xpath('//a[@href="/user/login/"]')
    #     except:
    #         signin_button = self.chrome.find_element_by_xpath('//a[@href="/user/login"]')

    #     time.sleep(1)

    #     # perform actual login
    #     if signin_button:
    #         signin_button.click()
    #         time.sleep(2)

    #         email_input = self.chrome.find_element_by_name('email')
    #         password_input = self.chrome.find_element_by_name('password')
    #         submit_button = self.chrome.find_element(By.XPATH, "//button[@type='submit']")
            
    #         email_input.send_keys(self.ahrefs_email)
    #         password_input.send_keys(self.ahrefs_password)
    #         time.sleep(1)
    #         submit_button.click()

    #         # wait for page to fully load
    #         time.sleep(3)

    def login(self):
        self.chrome.get('https://ahrefs.com/user/login')
        time.sleep(4)

        # perform actual login
        try:
            email_input = self.chrome.find_element_by_name('email')
        except:
            time.sleep(4)
            email_input = self.chrome.find_element_by_name('email')
        password_input = self.chrome.find_element_by_name('password')
        submit_button = self.chrome.find_element(By.XPATH, "//button[@type='submit']")
        
        email_input.send_keys(self.ahrefs_email)
        password_input.send_keys(self.ahrefs_password)
        time.sleep(1)
        submit_button.click()

        # wait for page to fully load
        time.sleep(3)

        print('performed login')


    def navigate_to_account_page(self, account_url):
        overview_url = f'https://app.ahrefs.com/site-explorer/overview/v2/subdomains/live?target={account_url}'
        self.chrome.get(overview_url)

    def create_screenshot_directory(self, dir_name):  
        if not os.path.exists(self.screenshot_dir_path):
            try:
                os.mkdir(self.screenshot_dir_path)
            except:
                pass

        new_dir_path = f'{self.screenshot_dir_path}/{dir_name}'

        if not os.path.exists(new_dir_path):
            try:
                os.mkdir(new_dir_path)
            except:
                pass

        return new_dir_path

    def get_chart(self, elementID):
        try:
            action = ActionChains(self.chrome)
            print("action is: ", action)
            # find and parse element dimensions
            element = self.wait.until(EC.element_to_be_clickable((By.ID, f'{elementID}')))
            print('get_chart element should be: ', element)
            if element:
                print('get_chart found element with ID of: ', elementID)
                time.sleep(3)
                element_size = element.size
                x_offset = element_size['width'] - 35
                y_offset = 50
                time.sleep(2)

                try:
                    self.chrome.execute_script(f"var element = document.getElementById('{elementID}').firstElementChild.firstElementChild; element.style.padding = '0 5px';")
                    print('get_chart successfully executed js script')
                except:
                    print('get_chart failed while trying to execute js script')
                    # return False

                # Hover to chart, click to make sure we're focused and then move all the way to the right to spawn tooltip
                action.move_to_element(element).perform()
                element.click()
                action.move_to_element_with_offset(element, x_offset, y_offset).perform()
                action.move_by_offset(0, -1).perform()
                print('get_chart should of returned element here')
                return element

            else:
                print('get_chart could not find element')
                return False

        except Exception:
            print('get_chart failed on try block with error: ', traceback.print_exc())
            return False

    def take_screenshots(self, report, account_url):
        dir_path = self.create_screenshot_directory(account_url)
        print('take_screenshots dir_path is', dir_path)
        try:
            self.navigate_to_account_page(account_url)
            print('take_screenshots account_url is', account_url)
            action = ActionChains(self.chrome)

            ### Referring Domains
            referring_domains_chart = self.get_chart('chartReferringDomains')
            print('referring_domains_chart is: ', referring_domains_chart)
            if referring_domains_chart:
                print("found referring_domains_chart")
                time.sleep(1)
                referring_domains_screenshot_path = f'{dir_path}/referring-domains-screenshot.png'
                referring_domains_chart_screenshot = referring_domains_chart.screenshot(referring_domains_screenshot_path)

                ### Referring Pages 
                referring_pages_chart = self.get_chart('chartReferringPages')
                print("found referring_pages_chart")
                time.sleep(1)
                referring_pages_screenshot_path = f'{dir_path}/referring-pages-screenshot.png'
                referring_pages_chart_chart_screenshot = referring_pages_chart.screenshot(referring_pages_screenshot_path)

                # switch view to organic search
                organic_search_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@data-target='organicSearch']/a")))
                organic_search_link.click()

                ### Organic Keywords Initial
                organic_keywords_chart = self.get_chart('organic_chart_keywords')
                time.sleep(1)
                print("found organic_keywords_chart")
                organic_keywords_screenshot_path = f'{dir_path}/initial-organic-keyword-screenshot.png'
                initial_organic_keyword_screenshot = organic_keywords_chart.screenshot(organic_keywords_screenshot_path)

                # find and click detailed checkbox
                detailed_checkbox = self.chrome.find_element(By.XPATH, "//input[@data-seria-index='0']")
                detailed_checkbox.click()

                detailed_organic_keywords_chart = self.get_chart('organic_chart_keywords')
                time.sleep(1)
                print("found detailed_organic_keywords_chart")
                detailed_organic_keywords_screenshot_path = f'{dir_path}/detailed-organic-keyword-screenshot.png'
                detailed_organic_keyword_screenshot = detailed_organic_keywords_chart.screenshot(detailed_organic_keywords_screenshot_path)
                
                saved_screenshots = [
                    referring_domains_screenshot_path,
                    referring_pages_screenshot_path,
                    organic_keywords_screenshot_path,
                    detailed_organic_keywords_screenshot_path
                ]

                if self.report or self.reports:
                    print("should save here")
                    self.save_screenshot_to_report(report, screenshot_path=referring_domains_screenshot_path, screenshot_type='referring_domains_screenshot')
                    self.save_screenshot_to_report(report, screenshot_path=referring_pages_screenshot_path, screenshot_type='referring_pages_screenshot')
                    self.save_screenshot_to_report(report, screenshot_path=organic_keywords_screenshot_path, screenshot_type='organic_keywords_screenshot')
                    self.save_screenshot_to_report(report, screenshot_path=detailed_organic_keywords_screenshot_path, screenshot_type='detailed_organic_keywords_screenshot')

        except:
            print('something went wrong with take_screenshots')
            pass

    def save_screenshot_to_report(self, target_report, screenshot_type, screenshot_path):
        report = self.report
        reports = self.reports
        print('save_screenshot_to_report target_report is: ', target_report)
        if target_report:
            print('save_screenshot_to_report evaled correctly as reports')

            cleaned_org_url = self.clean_account_url(target_report.organization.domain)
            print('save_screenshot_to_report cleaned_org_url is: ', cleaned_org_url)
            screenshot_base_name = f'{cleaned_org_url}__{target_report.month.year}__{target_report.month.month}'
            print('save_screenshot_to_report screenshot_base_name is: ', screenshot_base_name)
            try:
                valid_screenshot_field = target_report._meta.get_field(screenshot_type)
            except:
                valid_screenshot_field = None

            if valid_screenshot_field:
                print('save_screenshot_to_report valid_screenshot_field evaled and is: ', valid_screenshot_field)
                screenshot_field = getattr(target_report, screenshot_type)
                screenshot = File(open(screenshot_path, 'rb'))
                print('save_screenshot_to_report screenshot_path is: ', screenshot_path)
                new_screenshot_name = f'{screenshot_base_name}__{screenshot_type}.png'
                print('save_screenshot_to_report new_screenshot_name is: ', new_screenshot_name)
                screenshot_field.save(new_screenshot_name, screenshot)
            else:
                print(f'screenshot type of {screenshot_type} does not exist.')
        elif report:
            cleaned_org_url = self.clean_account_url(report.organization.domain)
            screenshot_base_name = f'{cleaned_org_url}__{report.month.year}__{report.month.month}'
            try:
                valid_screenshot_field = report._meta.get_field(screenshot_type)
            except:
                valid_screenshot_field = None

            if valid_screenshot_field:
                screenshot_field = getattr(report, screenshot_type)
                screenshot = File(open(screenshot_path, 'rb'))
                new_screenshot_name = f'{screenshot_base_name}__{screenshot_type}.png'
                screenshot_field.save(new_screenshot_name, screenshot)
            else:
                print(f'screenshot type of {screenshot_type} does not exist.')

    def restart(self):
        self.chrome.quit()
        self.login()

    def clean_up(self):
        self.chrome.quit()
        if os.path.exists(self.screenshot_dir_path):
            try:
                shutil.rmtree(self.screenshot_dir_path)
            except:
                pass

    def get_reports(self):
        MonthlyReport = apps.get_model(app_label='reporting', model_name='MonthlyReport')

        try:
            self.clean_up()
        except:
            pass

        self.setup()
        self.login()

        if self.report is not None:
            is_report = isinstance(self.report, MonthlyReport)

            if not is_report:
                try:
                    report_instance = MonthlyReport.objects.get(id=self.report)
                except:
                    report_instance = None

            if report_instance:
                self.report = report_instance

            if is_report or report_instance:
                try:
                    organization_url = self.report.organization.domain
                except:
                    organization_url = None

                if organization_url:
                    print(f'organization_url is: {organization_url}')
                    cleaned_organization_url = self.clean_account_url(organization_url)
                    print(f'cleaned_organization_url is: {cleaned_organization_url}')
                    if cleaned_organization_url:
                        self.take_screenshots(self.report, cleaned_organization_url)
                    else:
                        self.take_screenshots(self.report, organization_url)
                else:
                    raise 'Organization does not have a domain. Please add one.'
            else:
                raise 'report argument passed is not an MonthlyReport instance.'

        elif self.organization is not None:
            is_organization = isinstance(self.organization, Organization)

            if is_organization:
                organization_url = self.organization.domain
                if organization_url:
                    cleaned_organization_url = self.clean_account_url(organization_url)
                    self.take_screenshots(cleaned_organization_url)
                else:
                    raise 'Organization does not have a domain. Please add one.'
            else:
                raise 'organization argument passed is not an Organization instance.'

        elif self.account_urls is not None:
            is_list = isinstance(self.account_urls, list)
            PlanningYearMonth = apps.get_model(app_label='content_management', model_name='PlanningYearMonth')
            if is_list:
                if self.month and self.year:
                    try:
                        planning_month = PlanningYearMonth.objects.get(month=self.month, year=self.year)
                    except:
                        planning_month = None
                    
                    if planning_month:
                        reports = MonthlyReport.objects.filter(organization__domain__in=self.account_urls, month=planning_month)
                else:
                    reports = MonthlyReport.objects.filter(organization__domain__in=self.account_urls)

                self.reports = reports
                # print('evaling as reports')
                for i, report in enumerate(reports):
                    self.report_index = i
                    if report and report.organization:
                        if report.organization.domain:
                            cleaned_url = self.clean_account_url(report.organization.domain)
                            # print('account_urls loop report cleaned_url is: ', cleaned_url)
                            try:
                                self.take_screenshots(report, cleaned_url)
                            except TimeoutException as ex:
                                print(f"Timeout Exception has been thrown on {report.organization.domain} as: " + str(ex))
                                self.restart()
            else:
                return 'account_list must be a list.'
        
        else:
            return 'Please provide either an organization instance or a list of account URLs.'

    
        self.clean_up()

@app.task
def scrape_ahrefs_screenshots(report_id=None, account_urls=None, month=None, year=None):
    if account_urls:
        AhrefsReportScraper(account_urls=account_urls, month=month, year=year).get_reports()
    elif report_id:
        AhrefsReportScraper(report=report_id).get_reports()


@app.task
def get_ranked_keywords(report_id=None, domain=None, month=None, year=None):
    client = DataForSEORestClient()
    MonthlyReport = apps.get_model(app_label='reporting', model_name='MonthlyReport')
    rnd = Random()
    post_data = dict()

    if domain:
        target_domain = domain

    elif report_id:
        try:
            report_instance = MonthlyReport.objects.get(id=self.report)
        except:
            report_instance = None

        if report_instance and report_instance.organization.domain:
            target_domain = report_instance.organization.domain

    if target_domain:
        post_data[rnd.randint(1, 30000000)] = dict(
            domain="dataforseo.com",
            country_code="US",
            language="en",
            limit=1,
            offset=0,
            orderby="position,asc",
            filters=[
                ["cpc", ">", 0],
                "and", 
                ["search_volume", ">=", 1000]
            ]
        )
        response = client.post("/v2/kwrd_finder_ranked_keywords_get", dict(data=post_data))
        if response["status"] == "error":
            print("error. Code: %d Message: %s" % (response["error"]["code"], response["error"]["message"]))
        else:
            print(response["results"])
