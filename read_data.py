from flask import Flask , render_template 
from cfenv import AppEnv
import sys
import os
import requests
import base64
import json
import time
#create an app using flask lib and also get the port info for later use
app = Flask(__name__)
app.config["DEBUG"] = True
cf_port = os.getenv("PORT")
######################################################################
############### Step 1: Read the environment variables ###############
######################################################################
env = AppEnv()
#read all the xsuaa service key values from the env variables
uaa_service = env.get_service(name='xsuaa-demo')
#read all the connectivity service key values from the env variables
conn_service = env.get_service(name='instance1')
## read the client ID and secret for the connectivity service
conn_sUaaCredentials = conn_service.credentials["clientid"] + ':' + conn_service.credentials["clientsecret"]
## read the On premise proxy host and on premise proxy port for the connectivity service
proxy_url = conn_service.credentials["onpremise_proxy_host"] + ':' + conn_service.credentials["onpremise_proxy_port"]
print(proxy_url,flush=True)
#######################################################################
####### Step 2: Request a JWT token to access the connectivity service##
#######################################################################
##create authorization with basic authentication using connectivity credentials as base64 format
headers = {'Authorization': 'Basic '+ base64.b64encode(bytes(conn_sUaaCredentials ,'utf-8')).decode(), 'content-type': 'application/x-www-form-urlencoded'}
#create formdata with client ID and grant type
formdata = [('client_id', conn_service.credentials["clientid"] ), ('grant_type', 'client_credentials')]
##call the xsuaa service to retrieve JWT
response_conn = requests.post(uaa_service.credentials["url"] + '/oauth/token', data=formdata, headers=headers)
##convert the response to a proper format which can be reused again
jwt_conn = response_conn.json()["access_token"]

#######################################################################
###### Step 3: Make a call to backend system via SAP CC to read data ##
#######################################################################
##Set up basic auth for SAP System - Username and Password
onpremise_auth = requests.auth.HTTPBasicAuth('admin' , 'password!')
##Enter the exact path to your OData service in the SAP System using the virtual host:port details mentioned in the SAP Cloud Connector
url_cc =  'http://virtualhost3:8000'

##create a dict with proxy relevant information
proxyDict = { 'http' : proxy_url }
##create a header with authorization to the proxy server with the JWT retrieved in Step 2
headers = {
'content-type': 'application/json',
'Proxy-Authorization': 'Bearer ' + jwt_conn,
'cache-control': 'no-cache'
}
##make a get request using the Virtual ODATA url using the proxy details , header and basic authorization for Onpremise system
def call_url():
  response = requests.get( url_cc, proxies=proxyDict, headers=headers, auth = onpremise_auth)
  print( "response.status_code",flush=True)
  print( response.status_code,flush=True)
  print(  response,flush=True)
  data_response = response.text
  print( data_response,flush=True)
  ##conver the data 
  deb=url_cc 
  ##manually added
  return data_response
  if(jwt_conn is None):
    print("no connection")
    data_response="no connection"
######################################################################
##### Step 4: Return the data and run the app                       ##
######################################################################
@app.route('/')
def index():
  #return data_response
   return call_url()
@app.route('/<path:path>')
def index2(path):
  i=0
  while i <=10:
    print("sleeping 1 second for the time ",i)
    time.sleep(1)
    i+=1
  sys.exit(1)

if __name__ == '__main__':
	if cf_port is None:
		app.run(host='0.0.0.0', port=5000, debug=True)
	else:
		app.run(host='0.0.0.0', port=int(cf_port), debug=True)
