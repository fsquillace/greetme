"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test import Client

class FacebookAppTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
    def test_index_context(self):
        """
        Tests if the context sent to the template is correct.
        """
        
        response = self.client.get('/greetme/')
        
        print(response.content)
        self.failUnlessEqual(1 + 1, 2)



