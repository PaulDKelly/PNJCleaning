
import random
import uuid
from datetime import datetime
from . import models

class SageClient:
    """
    Mock Sage 50 Client for Test Environment.
    Simulates invoice creation without external API calls.
    """
    
    def __init__(self):
        self.connected = True
        
    async def create_invoice(self, job: models.Job, items: list = None):
        """
        Simulate creating an invoice in Sage 50.
        Returns a dict with invoice details.
        """
        # Simulate network delay
        # await asyncio.sleep(1) 
        
        # Generate Mock Invoice ID and Number
        invoice_number = f"SI-{random.randint(10000, 99999)}"
        sage_id = str(uuid.uuid4())
        
        print(f"[Sage Mock] Invoice created for Job {job.job_number}")
        print(f"[Sage Mock] Customer: {job.client_name}")
        print(f"[Sage Mock] Invoice #: {invoice_number}")
        
        return {
            "success": True,
            "sage_invoice_id": sage_id,
            "invoice_number": invoice_number,
            "amount": 250.00, # Default mock amount
            "status": "success"
        }

# Global instance
sage_client = SageClient()
