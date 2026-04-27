import unittest
from unittest.mock import MagicMock, patch
from fastapi import Request
from datetime import datetime
import sys

# Mock Supabase
mock_supabase = MagicMock()
sys.modules['app.supabase_client'] = MagicMock(supabase=mock_supabase)

class TestJobAllocation(unittest.TestCase):
    @patch('app.routers.scheduler.supabase')
    @patch('app.routers.scheduler.templates.TemplateResponse')
    def test_job_allocation_page_data(self, mock_template, mock_supabase_local):
        from app.routers.scheduler import job_allocation_page
        from app import models
        
        # Setup mocks
        mock_request = MagicMock(spec=Request)
        mock_user = models.User(username="admin", email="admin@example.com", password="hash", role="Admin")
        
        # Mock Supabase responses to match actual chainable calls:
        # 1. brands: .table("brands").select("*").execute()
        # 2. clients: .table("clients").select("*").eq("archived", False).order("client_name").execute()
        # 3. engineers: .table("engineers").select("*").order("contact_name").execute()
        # 4. site_contacts: .table("site_contacts").select("*").order("contact_name").execute()
        
        mock_execute = MagicMock()
        mock_execute.side_effect = [
            MagicMock(data=[{"id": 1, "brand_name": "Test Brand"}]), # brands
            MagicMock(data=[{"client_name": "Test Client"}]),        # clients
            MagicMock(data=[{"contact_name": "Test Engineer"}]),    # engineers
            MagicMock(data=[{"contact_name": "Test Contact"}])      # site_contacts
        ]
        
        # Mock the chain
        mock_supabase_local.table.return_value.select.return_value.execute = mock_execute
        mock_supabase_local.table.return_value.select.return_value.eq.return_value.order.return_value.execute = mock_execute
        mock_supabase_local.table.return_value.select.return_value.order.return_value.execute = mock_execute

        # Call the function
        job_allocation_page(mock_request, mock_user)
        
        # Verify TemplateResponse was called with the correct data
        args, kwargs = mock_template.call_args
        context = args[1]
        
        self.assertEqual(context["brands"], [{"id": 1, "brand_name": "Test Brand"}])
        self.assertEqual(context["clients"], [{"client_name": "Test Client"}])
        self.assertEqual(context["engineers"], [{"contact_name": "Test Engineer"}])
        self.assertEqual(context["site_contacts"], [{"contact_name": "Test Contact"}])
        self.assertEqual(context["today"], datetime.now().strftime('%Y-%m-%d'))

if __name__ == "__main__":
    unittest.main()
