from django.shortcuts import render, HttpResponse
from .models import TodoItem
import pandas as pd
QueryCount = 1
# Create your views here.
def home(request):
    return render(request, "base.html")

def analysis(request):
    items = TodoItem.objects.all()
    global QueryCount
    if QueryCount == 1:
        global access_token
        #access_token = get_the_acess_token()
        #print("comes here")
        QueryCount += 1
    access_token = ''
    print("print--",access_token)
    chain_data = get_nifty_option_chain(access_token)
    cleaned_data = get_nifty_chain_clean_data(chain_data)
    #html_table = cleaned_data.to_html(classes="table table-striped", index=False)  # Bootstrap styling
    html_table = cleaned_data.to_html(classes="table table-bordered", index=False, table_id="myTable")
    return render(request, 'analysis.html', {'table': html_table})
    #return render(request, "analysis.html", {"items":items})


def get_the_acess_token():
    import urllib.parse
    import requests
    import requests
    api_key = "" #ADD THIS
    api_secret = "" #ADD THIS
    redirect_uri = "http://localhost:5000"
    url = ""
    payload={
    'code': "", #ADD THIS
    'client_id': api_key,
    'client_secret': api_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
    }
    headers = {
    'Content-Type': '',#ADD THIS
    'Accept': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = response.json()
    access_token = response_json['access_token']
    #print(response.text)
    return access_token
    

def get_nifty_option_chain(access_token):
    import requests
    url = "" #ADD THIS
    payload = {
    'instrument_key': 'NSE_INDEX|Nifty 50',
    'expiry_date': '2025-03-13'
    }
    headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'
    }
    response1 = requests.get(url, headers=headers, params=payload)
    ocdata = pd.DataFrame.from_dict(response1.json()['data'])
    return ocdata

def get_nifty_chain_clean_data(ocdata):
    call_df = pd.json_normalize(ocdata['call_options'])
    put_df = pd.json_normalize(ocdata['put_options'])
    call_df.rename(columns=lambda col: col.replace("market_data.", "call_").replace("option_greeks.", "call_greeks_"), inplace=True)
    put_df.rename(columns=lambda col: col.replace("market_data.", "put_").replace("option_greeks.", "put_greeks_"), inplace=True)
    result = pd.concat([ocdata.drop(columns=['call_options','put_options']), call_df,put_df], axis=1)
    return result
    display(result)
