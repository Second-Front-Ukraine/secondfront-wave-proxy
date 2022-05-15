from repository import WaveRepository


class CampaignService:
    """
    The service is concerned with business implementation for Campaigns and Tabs
    """
    
    def __init__(self):
        self.wave = WaveRepository()
    
    def get_campaign(self, campaign_slug):
        business_details = self.wave.get_business_details()
        invoices = self.wave.get_invoices_for_slug(campaign_slug)

        amount_paid = 0
        amount_unpaid = 0

        for invoice in invoices:
            amount_paid += invoice['node']['amountPaid']['raw']
            amount_unpaid += invoice['node']['amountDue']['raw']

        return {
            'business': business_details,
            'campaign': {
                'slug': campaign_slug,
                'collected': amount_paid,
                'unpaid': amount_unpaid,
            }
        }
    
    def create_tab(
        self,
        campaign_slug: str,
        amount: int,
        email: str,
        name: str = '',
        comment: str = '',
        yes_to_updates: bool = False,
    ):
        # Create Customer
        pass
        # Create Invoice
        pass

        return {
            'tab_id': '',
            'url': '',
        }
    
    def get_tab(self):
        pass


