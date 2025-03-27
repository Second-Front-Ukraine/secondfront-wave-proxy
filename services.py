import re
import random
from collections import defaultdict
import base64

import boto3

from client import WaveClient


class CampaignService:
    """
    The service is concerned with business implementation for Campaigns and Tabs
    """
    
    def __init__(self):
        self.wave = WaveClient()
        self.dynamodb = boto3.resource('dynamodb')
        self.tracking_table = self.dynamodb.Table('donation-tracking')
    
    def get_campaign(self, campaign_slug, detailed=False):
        business_details = self.wave.get_business_details()
        invoices = self.wave.get_invoices_for_slug(campaign_slug, status="PAID")

        amount_paid = 0
        amount_unpaid = 0

        breakdown = defaultdict(int)

        for invoice in invoices:
            amount_paid += invoice['node']['amountPaid']['raw']
            amount_unpaid += invoice['node']['amountDue']['raw']
            if detailed:
                invoice_number = invoice['node']['invoiceNumber']
                m = re.match(r'^({})-?(.+)-\d+$'.format(campaign_slug), invoice_number)
                if m:
                    a, b = m.groups()
                    breakdown[f"{a.strip('-')}-{b.strip('-')}"] += invoice['node']['amountPaid']['raw']
                else:
                    breakdown[campaign_slug] += invoice['node']['amountPaid']['raw']

        result = {
            'business': business_details,
            'campaign': {
                'slug': campaign_slug,
                'collected': amount_paid,
                'unpaid': amount_unpaid,
            }
        }
        if detailed:
            result['campaign']['breakdown'] = breakdown

        return result
    
    def create_tab(
        self,
        campaign_slug: str,
        amount: int = 0,
        email: str = '',
        name: str = '',
        comment: str = '',
        yes_to_updates: bool = False,
        shipping_details: dict[str, str] = None,
        products: dict[str, dict[str, str]] = None,
        referrer: str = None,
        user_agent: str = None,
        ip_address: str = None,
    ):
        # Get template Invoice
        template_invoice = None
        try:
            template_invoice = [i['node'] for i in self.wave.get_invoices_for_slug(campaign_slug, status="DRAFT") if i['node']['invoiceNumber'].lower().endswith('template')][0]
            print("FOUND TEMPLATE INVOICE for ", campaign_slug)
        except IndexError:
            if campaign_slug.startswith("IH"):
                print("FETCHING DEFAULT TEMPLATE FOR IRON HEARTS...")
                try:
                    template_invoice = [i['node'] for i in self.wave.get_invoices_for_slug("IRON-HEARTS", status="DRAFT") if i['node']['invoiceNumber'].lower().endswith('template')][0]
                    print("FOUND IRON HEARTS TEMPLATE INVOICE for IRON-HEARTS, specifically: ", campaign_slug)
                except Exception as e:
                    print("ERROR", e)
        if template_invoice is None:
            print("FALLING BACK TO DEFAULT HARD-CODED TEMPLATE")
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
        if (email or name) and shipping_details is None:  # Looking up by address as well is asking for so many assertions, best to create new customer from the get go.
            # Lookup customer by email and name
            customer = self.wave.get_customer(email, name)
        if customer is None and (name or email):
            # If lookup failed, create with given email and name
            customer = self.wave.create_customer(email, name, shipping_details=shipping_details)
        if customer is None and template_invoice.get('customer', {}).get('id'):
            # If email or name not given, then use the customer from the template
            customer = template_invoice['customer']
        if customer is None:
            # If template does not exist, then create a new customer with generic name
            customer = self.wave.create_customer('', 'Good Samarithan', shipping_details=shipping_details)
        
        # Create Invoice
        items = [{
            'productId': template_invoice['items'][0]['product']['id'],
            'description': template_invoice['items'][0]['description'],
            'quantity': "1",
            'unitPrice': str(int(amount) / 100),
        }] if products is None else [{
            'productId': p_id,
            'quantity': str(p.get('quantity', 1)),
            'unitPrice': str(int(p['unitPrice']) / 100)
        } for p_id, p in products.items() if p.get('quantity', 1) > 0]

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
            'items': items,
        }
        try:
            invoice = self.wave.create_invoice(**create_invoice_input)
        except Exception as e:
            print("ERROR", e)
            raise

        if referrer:
            try:
                def decode_invoice_id(value):
                    try:
                        s = base64.b64decode(value).decode()
                        parts = s.split(';')

                        business_id = parts[0].split(':')[1].strip()
                        invoice_id = parts[1].split(':')[1].strip()
                    except Exception:
                        return 'unknown', value

                    return business_id, invoice_id
                b_id, d_id = decode_invoice_id(invoice['id'])
                self.tracking_table.put_item(
                    Item={
                            'business_id': b_id,
                            'donation_id': d_id,
                            'donation_url': invoice['viewUrl'],
                            'campaign_slug': campaign_slug,
                            'referrer': referrer,
                            'user_agent': user_agent,
                            'ip_address': ip_address,
                        }
                    )
            except Exception as e:
                print(e)
                # pass the error to unblock the request. Note, hanging dynamodb puts may still fail the request.

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
