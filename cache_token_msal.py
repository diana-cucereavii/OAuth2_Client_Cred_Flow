import msal
import jwt
import json
import sys
import requests
from datetime import datetime

global accessToken
global requestHeaders
global tokenExpiry

accessToken = None
requestHeaders = None
tokenExpiry = None

apiURI = '{Resource API URL}'
tenantID = '{Tenant ID}'
authority = 'https://login.microsoftonline.com/{TenantID}'
clientID = '{Azure ADD Client ID}'
scope = ['api://{Resource API ID}/.default']
thumbprint = '{SSL Certificate Thumpprint}'
certfile = '{SSL certificate in .pem or .key format}'
subscription_key = '{Subscription ID}' #If your API resources are behind APIM and require a Subscription Key

def cert_auth(clientID, scope, authority, thumbprint, certfile):      
    app = msal.ConfidentialClientApplication(clientID, authority=authority, client_credential={"thumbprint": thumbprint, "private_key": open(certfile).read()}) 
    result = app.acquire_token_for_client(scopes=scope)
    return result 

def swapi_request(resource, requestHeaders):
    # Resource API Request
    results = requests.get(resource, headers=requestHeaders).json()
    return results

def jwt_expiry(accessToken): 
    decodedAccessToken = jwt.decode(accessToken, verify=False) 
    accessTokenFormatted = json.dumps(decodedAccessToken, indent=2) 

    # Token Expiry 
    tokenExpiry = datetime.fromtimestamp(int(decodedAccessToken['exp'])) 
    print("Token Expires at: " + str(tokenExpiry)) 
    return tokenExpiry 

# Authorization 
try:
    if not accessToken:
        try:
            # Get a new Access Token using Client Credentials Flow and a Self Signed Certificate
            accessToken = cert_auth(clientID, scope, authority, thumbprint, certfile)
            requestHeaders = {
                'Authorization': 'Bearer ' + accessToken['access_token'],
                'Ocp-Apim-Subscription-Key': subscription_key   
            }   
        except Exception as err:
            print('Error acquiring authorization token. Check your credentials.')
            print(err)
    if accessToken:
        # Checking token expiry time to expire in the next 10 minutes
        decodedAccessToken = jwt.decode(accessToken['access_token'], verify=False)
        accessTokenFormatted = json.dumps(decodedAccessToken, indent=2)
        print("Decoded Access Token")
        print(accessTokenFormatted)

        # Token Expiration time
        tokenExpiry = jwt_expiry(accessToken['access_token'])  
        now = datetime.now() 
        time_to_expiry = tokenExpiry - now

        if time_to_expiry.seconds < 600:
            print("Access Token Will Expiring Soon. Renewing Access Token.")
            accessToken = cert_auth(clientID, scope, authority, thumbprint, certfile)
            requestHeaders = {'Authorization': 'Bearer ' + accessToken['access_token']}
        else:
            minutesToExpiry = time_to_expiry.seconds / 60
            print("Access Token Expires in '" + str(minutesToExpiry) +" minutes'")

except Exception as err:
    print(err)

# Query
if requestHeaders and accessToken:
    queryResults = swapi_request(apiURI ,requestHeaders)
    try:
        print(json.dumps(queryResults, indent=2))
    except Exception as err:
        print(err)