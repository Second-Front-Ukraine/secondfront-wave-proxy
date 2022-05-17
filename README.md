# User flow

1. Pick campaign(s). The interface shows available campaigns (interface is not part of this repository)
2. Create Donation with: campaign(s), email. name, amount per campaign, a note, and whether or not to receive updates
3. Store donation ID in cookies, then open donation in a new tab or window (?). Keep polling for payment.
4. Once donation is paid, it'll show as paid. The window/tab can be closed.
5. Original tab will receive an update that donation was paid and update the widget state to reflect new donated amount and show how much was donated by you.
6. Enjoy donation page that has your name and $ you contributed (it'll vanish when cookies are cleared)

# Data model
There's no database, the modelling is around Wave data structures: Invoice, Customer, Product, Account.
These structures are mapped to internal entities: Campaign, Tab 

*Account* represents a specific campaign.
*Invoice* represents a Tab for one or more campaigns.
*Product* is assigned an account.
*Invoice* is created for a specific *customer* and *product*(s).

