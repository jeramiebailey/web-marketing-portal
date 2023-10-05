from django.test import TestCase
from django.test.client import RequestFactory
from content_management.models import PlanningYearMonth, ContentArticle
import calendar

class PlanningYearMonthTestCase(TestCase):
    def setUp(self):
        self.rq = RequestFactory()

    def test_create_planning_year_month(self):
        return PlanningYearMonth.objects.create(
            year=2020,
            month=1
        )

    def test_planning_year_month(self):
        test_instance = self.test_create_planning_year_month()
        self.assertTrue(isinstance(test_instance, PlanningYearMonth))
        self.assertEqual(test_instance.__str__(), f'{calendar.month_name[test_instance.month]} {test_instance.year}')

class ContentArticleTestCase(TestCase):
    def setUp(self):
        self.rq = RequestFactory()

    def test_create_content_article(self):
        return ContentArticle.objects.create(
            title="Test Title",
        )

    def test_content_article(self):
        test_instance = self.test_create_content_article()
        self.assertTrue(isinstance(test_instance, ContentArticle))