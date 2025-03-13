from django.shortcuts import render, HttpResponse
from .models import TodoItem
import pandas as pd
import requests
import time
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
    access_token = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJEVDg1MzYiLCJqdGkiOiI2N2QzMTc0NGEzYzcwYjBiN2U5OGI0ZDciLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQxODg3MzAwLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDE5MDMyMDB9.l5IHNIWYlDgB8gj7l0W74XC3F4SPRHymaWXGYyDMJjg'
    #print("print--",access_token)
    for i in range(500):
        time.sleep(15)
        chain_data = get_nifty_option_chain(access_token)
        cleaned_data = get_nifty_chain_clean_data(chain_data)
        html_table = cleaned_data.to_html(classes="table table-bordered", index=False, table_id="myTable")
        fig_image,pcr_html= pcr_calculation(cleaned_data,i)
        return render(request, 'analysis.html', {'table': html_table,'fig_image':fig_image,'pcr_html':pcr_html})
    
    #return render(request, "analysis.html", {"items":items})


def get_the_acess_token():
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

def pcr_calculation(cleaned_data,i):
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    from IPython.display import display, clear_output
    import datetime
    import io
    import base64
    result_CalPcr = cleaned_data[['expiry', 'pcr', 'strike_price',
       'underlying_spot_price', 'call_ltp', 'call_volume',
       'call_oi', 'call_close_price', 'call_prev_oi', 'call_greeks_vega',
       'call_greeks_theta', 'call_greeks_gamma', 'call_greeks_delta',
       'call_greeks_iv', 'put_ltp', 'put_volume', 'put_oi',
       'put_close_price','put_prev_oi', 'put_greeks_vega', 'put_greeks_theta',
       'put_greeks_gamma', 'put_greeks_delta', 'put_greeks_iv']]
    result_CalPcr[['pcr','call_oi','call_prev_oi','put_oi','put_prev_oi','strike_price','underlying_spot_price']]
    result_CalPcr.loc[:, 'closestPrice'] =  (result_CalPcr['underlying_spot_price'] - result_CalPcr['strike_price'])
    min_value = result_CalPcr['closestPrice'].abs().min()

    filtered_indices = result_CalPcr[result_CalPcr['closestPrice'].abs() == min_value ].index
    index_value = filtered_indices[0] if not filtered_indices.empty else None
    changeinoi = result_CalPcr.iloc[[index_value-8,index_value-7,index_value-6,index_value-5,index_value-4,index_value-3,index_value-2,index_value-1,\
             index_value,index_value+1,index_value+2,index_value+3,index_value+4,index_value+5,index_value+6,index_value+7,index_value+8]][['pcr',\
             'call_oi','call_prev_oi','put_oi','put_prev_oi','strike_price','underlying_spot_price','closestPrice']]
    changeinoi.loc[:, 'call_oi_chng'] =  (changeinoi['call_oi'] - changeinoi['call_prev_oi'])
    changeinoi.loc[:, 'put_oi_chng'] =  (changeinoi['put_oi'] - changeinoi['put_prev_oi'])
    sum_put = changeinoi['call_oi_chng'].sum()
    sum_call = changeinoi['put_oi_chng'].sum()
    pcr_change =  round((sum_put / sum_call),3)
    data = pd.DataFrame(columns=['Time', 'Value'])


    plt.ion() 
    fig, ax = plt.subplots()
    def color_value(val):
        color = 'green' if val > 1 else 'red'  
        return f'background-color: {color}'

    
    current_time = datetime.datetime.now()

    formatted_time = current_time.strftime("%H:%M")

    new_time = i*5
    new_value = np.random.randint(0, 10)  
    
    new_row = pd.DataFrame({'Time': [formatted_time], 'Value': [pcr_change]})
    
    data = pd.concat([data, new_row], ignore_index=True)

    ax.clear()
    
    ax.plot(data['Time'], data['Value'], label="Live Data")
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.set_title("Live Chart Example")
    
        
    clear_output(wait=True)
    
        
    styled_data = data.style.applymap(color_value, subset=['Value'])

    html_styled_data = styled_data.to_html(classes="table table-striped", index=False)
    #display(fig)
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png')
    buffer.seek(0)

    # Encode the image to base64
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode('utf-8')
    image_data = f"data:image/png;base64,{graphic}"
    return image_data,html_styled_data
    
