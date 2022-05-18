from operator import inv
import random
from client import WaveClient


class CampaignService:
    """
    The service is concerned with business implementation for Campaigns and Tabs
    """
    
    def __init__(self):
        self.wave = WaveClient()
    
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
        email: str = '',
        name: str = '',
        comment: str = '',
        yes_to_updates: bool = False,
    ):
        # Get template Invoice
        try:
            template_invoice = [i['node'] for i in self.wave.get_invoices_for_slug(campaign_slug) if i['node']['invoiceNumber'].lower().endswith('template')][0]
        except IndexError:
            template_invoice = {
                'title': 'Donation',
                'subhead': "",
                'footer': '',
                'itemTitle': "Campaign",
                'unitTitle': "Quantity",
                'priceTitle': "Price",
                'amountTitle': "Donation Amount",
                'hideName': True,
                'hideDescription': False,
                'hideUnit': True,
                'hidePrice': True,
                'hideAmount': False,
                'requireTermsOfServiceAgreement': False,
                'items': [
                    {
                        "description": "GET DEFENCE SUPPLIES TO UKRAINE.",
                        "quantity": "1",
                        "unitPrice": str(int(amount) / 100),
                        "product": {
                            "id": "QnVzaW5lc3M6M2E1NDQxZjYtMWVhYS00OTcwLThhYmQtYTk0MDM4M2E1NGVjO1Byb2R1Y3Q6NzY4NTczNjI="  # TODO
                        }
                    }
                ]
            }
        
        customer = None
        if email or name:
            # Lookup customer by email and name
            customer = self.wave.get_customer(email, name)
        if customer is None and (name or email):
            # If lookup failed, create with given email and name
            customer = self.wave.create_customer(email, name)
        if customer is None and template_invoice.get('customer', {}).get('id'):
            # If email or name not given, then use the customer from the template
            customer = template_invoice['customer']
        if customer is None:
            # If template does not exist, then create a new customer with generic name
            customer = self.wave.create_customer('', 'Good Samarithan')
        
        # Create Invoice
        create_invoice_input = {
            'customer_id': customer['id'],
            'title': template_invoice['title'],
            'subhead': template_invoice['subhead'],
            'invoice_number': campaign_slug + '-' + str(random.randint(10000, 999999)),
            'memo': comment,
            'footer': template_invoice['footer'],
            'item_title': template_invoice['itemTitle'],
            'unit_title': template_invoice['unitTitle'],
            'price_title': template_invoice['priceTitle'],
            'amount_title': template_invoice['amountTitle'],
            'hide_name': template_invoice['hideName'],
            'hide_description': template_invoice['hideDescription'],
            'hide_unit': template_invoice['hideUnit'],
            'hide_price': template_invoice['hidePrice'],
            'hide_amount': template_invoice['hideAmount'],
            'require_tos': template_invoice['requireTermsOfServiceAgreement'],
            'items': [{
                'productId': template_invoice['items'][0]['product']['id'],
                'description': template_invoice['items'][0]['description'],
                'quantity': "1",
                'unitPrice': str(int(amount) / 100),
            }]
        }
        invoice = self.wave.create_invoice(**create_invoice_input)

        if invoice:
            return {
                'tab_id': invoice['id'],
                'url': invoice['viewUrl'],
                'paid': False,
            }
    
    def get_tab(self, tab_id):
        invoice = self.wave.get_invoice(tab_id)

        return {
            'tab_id': invoice['id'],
            'url': invoice['viewUrl'],
            'paid': invoice['status'] == 'PAID'
        }


