In order to use the Microsoft Drive Account module, you need to set following configuration parameters in your Odoo instance:

* microsoft_account.auth_endpoint: The URL of the Microsoft authentication endpoint. This is usually https://login.microsoftonline.com/{your endpoint id}/oauth2/v2.0/authorize.
* microsoft_account.token_endpoint: The URL of the Microsoft token endpoint. This is usually https://login.microsoftonline.com/{your endpoint id}/oauth2/v2.0/token.
* microsoft_drive_client_id: The client ID of your Microsoft application. This is a unique identifier for your application that you can obtain from the Azure portal.
* microsoft_drive_client_secret: The client secret of your Microsoft application. This is a secret key that you can obtain from the Azure portal. It is used to authenticate your application with the Microsoft Graph API.


Optionally, you can set the following parameters:

* microsoft_drive_client_scope: The scope of the Microsoft application.  By default the following scopes are used 
    - offline_access
    - openid
    - Files.ReadWrite.All
    - Sites.ReadWrite.All
    
