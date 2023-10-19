import requests,json, getpass
# https://daft-develop.dtenabler.com/docs#/
token_url = "https://auth-develop.dtenabler.com/realms/develop/protocol/openid-connect/token"

test_api_url = "https://daft-develop.dtenabler.com/tables/"

# Step A - resource owner supplies credentials

#Resource owner (enduser) credentials
RO_user = "p.kuruppuarachchi@mycit.ie"
RO_password = "123456"

#client (application) credentials on apim.byu.edu

client_id = 'api'
client_secret = ''

#step B, C - single call with resource owner credentials in the body  and client credentials as the basic auth header
# will return access_token

data = {'grant_type': 'password','username': RO_user, 'password': RO_password}

access_token_response = requests.post(token_url, data=data, verify=False, allow_redirects=False, auth=(client_id, client_secret))

# print (access_token_response.headers)
# print (access_token_response.text)

tokens = json.loads(access_token_response.text)
# print ("access token: " + tokens['access_token'])

# Step C - now we can use the access_token to make as many calls as we want.
time_list = []
test_api_url2 = "https://daft-develop.dtenabler.com/tables/48799d0e-6be2-4cf8-a3d9-f9fbc8f4ecba-p1-foi-003/rows?c=p1_pro_0001"
for i in range(10):
  api_call_headers = {'Authorization': 'Bearer ' + tokens['access_token']}
  # print (api_call_headers)
  api_call_response = requests.get(test_api_url2, headers=api_call_headers, verify=False)

  # print (api_call_response.text)
  print(api_call_response.elapsed.total_seconds())
  time_list.append(api_call_response.elapsed.total_seconds())
print(sum(time_list)/len(time_list))


