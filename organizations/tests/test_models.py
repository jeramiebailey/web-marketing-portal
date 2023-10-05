from test_plus.test import TestCase, RequestFactory
import unittest
from organizations.models import Organization
from django.utils import timezone

class OrganizationTest(TestCase):
    def setUp(self):
        self.rq = RequestFactory()

    def test_create_organization(
        self, 
        legal_name='Test Business, LLC',
        dba_name='Test Business',
        slug='test-business',
        business_email='info@testbusiness.com',
        street_address_1='1234 Main Street',
        street_address_2='Suite 201',
        city='Fairfax',
        state='VA',
        zipcode ='22030',
        ):

        return Organization.objects.create(
            legal_name=legal_name,
            dba_name=dba_name,
            slug=slug,
            business_email=business_email,
            street_address_1=street_address_1,
            street_address_2=street_address_2,
            city=city,
            state=state,
            zipcode=zipcode,
            created_at=timezone.now()
            )
    
    def test_organization(self):
        w = self.test_create_organization()
        self.assertTrue(isinstance(w, Organization))
        self.assertEqual(w.__str__(), w.dba_name)
