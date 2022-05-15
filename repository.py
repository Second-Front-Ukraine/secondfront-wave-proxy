import os
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

WAVE_TOKEN = os.environ['WAVE_TOKEN']
WAVE_URL = "https://gql.waveapps.com/graphql/public"
WAVE_BUSINESS_ID = os.environ.get("WAVE_BUSUNESS_ID", "QnVzaW5lc3M6M2E1NDQxZjYtMWVhYS00OTcwLThhYmQtYTk0MDM4M2E1NGVj")

BUSINESS_QEURY = gql("""query($businessId: ID!) {
  business(id: $businessId) {
    id
    name
    isPersonal
  }
}""")

INVOICES_QUERY = gql("""query($businessId: ID!, $page: Int!, $slug: String!) {
  business(id: $businessId) {
    id
    invoices(
      page: $page,
      invoiceNumber: $slug
    ) {
      edges {
        node {
          id
          title
          amountDue {
            raw
            value
          }
          amountPaid {
            raw
            value
          }
          total {
            raw
            value
          }
        }
      }
      pageInfo {
        totalPages
        currentPage
        totalCount
      }
    }
  }
}""")


class WaveRepository:
    """
    Repository for Wave GraphQL API.

    API Playgound - https://developer.waveapps.com/hc/en-us/articles/360018937431-API-Playground
    """

    def __init__(self, business_id=WAVE_BUSINESS_ID):
        self.business_id = business_id
        headers = {"Authorization": f"Bearer {WAVE_TOKEN}"}
        transport = AIOHTTPTransport(url=WAVE_URL, headers=headers)
        self.client = Client(transport=transport)
    
    def get_business_details(self):
        return self.client.execute(BUSINESS_QEURY, variable_values={'businessId': self.business_id})
    
    def get_invoices_for_slug(self, slug: str):
        invoices = []
        page = 1
        while True:
            response = self.client.execute(INVOICES_QUERY, variable_values={
                'businessId': self.business_id,
                'page': page,
                'slug': slug.upper(),
            })
            invoices.extend(response['business']['invoices']['edges'])

            # Check for next page
            total_pages = response['business']['invoices']['pageInfo']['totalPages']
            if total_pages >= page:
                break
            page += 1
        
        return invoices

    
    def create_customer(self):
        """
        type CustomerCreateInput {
            businessId: ID!
            name: String!
            firstName: String
            lastName: String
            address: AddressInput
            displayId: String
            email: String
            mobile: String
            phone: String
            fax: String
            tollFree: String
            website: String
            internalNotes: String
            currency: CurrencyCode
            shippingDetails: CustomerShippingDetailsInput
        }
        """
        customer_create_input = {
            'businessId': self.busienss_id,
            'name': '',
            'firstName': '',
            'lastName': '',
            'internalNotes': "Auto-created using wave-proxy",
        }
