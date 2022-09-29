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

GET_INVOICE_QUERY = gql("""query($businessId: ID!, $invoiceId: ID!) {
  business(id: $businessId) {
    id
    invoice(id: $invoiceId) {
      id
      viewUrl
      status
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
          subhead
          invoiceNumber
          footer
          itemTitle
          unitTitle
          priceTitle
          amountTitle
          hideName
          hideDescription
          hideUnit
          hidePrice
          hideAmount
          requireTermsOfServiceAgreement
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
          customer {
            id
            name
            email
          }
          items {
            description
            quantity
            unitPrice
            product {
              id
            }
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

LOOKUP_CUSTOMER_BY_EMAIL = gql("""query($businessId: ID!, $email: String!) {
  business(id: $businessId) {
    customers(email: $email) {
      edges {
        node {
          id
          name
          email
        }
      }
    }
  }
}""")

ALL_CUSTOMERS = gql("""query($businessId: ID!, $page: Int!) {
  business(id: $businessId) {
    customers(page: $page) {
      edges {
        node {
          id
          name
          email
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

MUTATION_CUSTOMER_CREATE = gql("""mutation CreateCustomer(
  $businessId: ID!,
  $email: String,
  $name: String!,
  $notes: String,
) {
  customerCreate(
    input: {
      businessId: $businessId,
      name: $name,
      email: $email,
      internalNotes: $notes,
    }
  ) {
    customer {
      id
    }
    didSucceed
    inputErrors {
      path
      message
      code
    }
  }
}""")


MUTATION_CUSTOMER_CREATE_WITH_ADDRESS = gql("""mutation CreateCustomer(
  $businessId: ID!,
  $email: String,
  $name: String!,
  $notes: String,
  $addressLine1: String,
  $addressLine2: String,
  $city: String,
  $provinceCode: String,
  $countryCode: CountryCode,
  $postalCode: String,
  $phone: String
) {
  customerCreate(
    input: {
      businessId: $businessId,
      name: $name,
      email: $email,
      phone: $phone,
      internalNotes: $notes,
      address: {
        addressLine1: $addressLine1,
        addressLine2: $addressLine2,
        city: $city,
        provinceCode: $provinceCode,
        countryCode: $countryCode,
        postalCode: $postalCode
      },
      shippingDetails: {
        name: $name,
        address: {
          addressLine1: $addressLine1,
          addressLine2: $addressLine2,
          city: $city,
          provinceCode: $provinceCode,
          countryCode: $countryCode,
          postalCode: $postalCode
        },
        phone: $phone
      }
    }
  ) {
    customer {
      id
    }
    didSucceed
    inputErrors {
      path
      message
      code
    }
  }
}""")

MUTATION_INVOICE_CREATE = gql("""mutation CreateInvoice(
  $businessId: ID!,
  $customerId: ID!,
  $title: String!,
  $subhead: String!,
  $invoiceNumber: String!,
  $memo: String,
  $footer: String,
  $itemTitle: String,
  $unitTitle: String,
  $priceTitle: String,
  $amountTitle: String,
  $hideName: Boolean,
  $hideDescription: Boolean,
  $hideUnit: Boolean,
  $hidePrice: Boolean,
  $hideAmount: Boolean,
  $requireTOS: Boolean,
  $items: [InvoiceCreateItemInput!]
) {
  invoiceCreate(
    input: {
      businessId: $businessId,
      customerId: $customerId,
      status: SAVED,
      title: $title,
    	subhead: $subhead,
      invoiceNumber: $invoiceNumber,
      items: $items,
      memo: $memo,
      footer: $footer,
      itemTitle: $itemTitle,
      unitTitle: $unitTitle,
      priceTitle: $priceTitle,
      amountTitle: $amountTitle,
      hideName: $hideName,
      hideDescription: $hideDescription,
      hideUnit: $hideUnit,
      hidePrice: $hidePrice,
      hideAmount: $hideAmount,
      requireTermsOfServiceAgreement: $requireTOS,
    }
  ) {
    invoice {
      id
      viewUrl
    }
    didSucceed
    inputErrors {
      path
      message
      code
    }
  }
}""")


class CustomerCreateException(Exception):
    pass


class WaveClient:
    """
    Client for Wave GraphQL API.

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
      
    def get_invoice(self, invoice_id):
      response = self.client.execute(GET_INVOICE_QUERY, variable_values={
        'businessId': self.business_id,
        'invoiceId': invoice_id
      })
      if 'errors' in response:
        return None
      
      return response['business']['invoice']
      
    def get_customer(self, email, name):
        """ Get customer by email and name. Must match exactly or none at all. """
        if email:
            # Query for customeres with given email.
            def iterator():
                response = self.client.execute(LOOKUP_CUSTOMER_BY_EMAIL, variable_values={
                  'businessId': self.business_id,
                  'email': email,
                })
                for customer in response['business']['customers']['edges']:
                    yield customer['node']
        else:
            # If email is not available, iterate all.
            def iterator():
                current_page = 1
                while True:
                    response = self.client.execute(ALL_CUSTOMERS, variable_values={
                      'businessId': self.business_id,
                      'page': current_page,
                    })
                    for customer in response['business']['customers']['edges']:
                        yield customer['node']
                    if current_page >= response['business']['customers']['pageInfo']['totalPages']:
                        break
                    current_page += 1
        for customer in iterator():
            if customer['name'] == name and customer['email'] == email:
                return customer

    def create_customer(self, email, name, shipping_details=None):
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
        shipping_details = shipping_details or {}
        customer_create_input = {
            'businessId': self.business_id,
            'name': name or email,
            'email': email or '',
            'internalNotes': "Auto-created using wave-proxy",
        }
        mut = MUTATION_CUSTOMER_CREATE
        if shipping_details:
          customer_create_input.update({
              'addressLine1': shipping_details['addressLine1'],
              'addressLine2': shipping_details['addressLine2'],
              'city': shipping_details['city'],
              'provinceCode': shipping_details['provinceCode'],
              'countryCode': shipping_details['countryCode'],
              'postalCode': shipping_details['postalCode'],
          })
          customer_create_input['phone'] = shipping_details.get('phone', '')
          mut = MUTATION_CUSTOMER_CREATE_WITH_ADDRESS

        response = self.client.execute(mut, variable_values=customer_create_input)
        if response['customerCreate']['didSucceed']:
            return response['customerCreate']['customer']
        else:
          raise CustomerCreateException(response['customerCreate']['inputErrors'][0]['message'])
    
    def create_invoice(
        self,
        customer_id: str,
        title: str,
        subhead: str,
        invoice_number: str,
        memo: str,
        footer: str,
        item_title: str,
        unit_title: str,
        price_title: str,
        amount_title: str,
        hide_name: bool,
        hide_description: bool,
        hide_unit: bool,
        hide_price: bool,
        hide_amount: bool,
        require_tos: bool,
        items: list[dict[str, str]]
    ):

        invoice_create_input = {
            'businessId': self.business_id,
            'customerId': customer_id,
            'title': title,
            'subhead': subhead,
            'invoiceNumber': invoice_number,
            'memo': memo,
            'footer': footer,
            'itemTitle': item_title,
            'unitTitle': unit_title,
            'priceTitle': price_title,
            'amountTitle': amount_title,
            'hideName': hide_name,
            'hideDescription': hide_description,
            'hideUnit': hide_unit,
            'hidePrice': hide_price,
            'hideAmount': hide_amount,
            'requireTOS': require_tos,
            'items': items
        }
        response = self.client.execute(MUTATION_INVOICE_CREATE, variable_values=invoice_create_input)
        if response['invoiceCreate']['didSucceed']:
            return response['invoiceCreate']['invoice']
