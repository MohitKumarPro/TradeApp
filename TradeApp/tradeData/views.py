from django.shortcuts import render, HttpResponse
from .models import TodoItem
import pandas as pd
import requests
import time
QueryCount = 1
# Create your views here.
import threading
import time




def home(request):
    return render(request, "base.html")

def analysis(request):
    items = TodoItem.objects.all()
    global QueryCount
    if QueryCount == 1:
        global access_token
        access_token = get_the_acess_token()
        #print("comes here")
        QueryCount += 1
    #access_token = ''
    #print("print--",access_token)
    chain_data = get_nifty_option_chain(access_token)
    return chain_data
        #cleaned_data = get_nifty_chain_clean_data(chain_data)
        #html_table = cleaned_data.to_html(classes="table table-bordered", index=False, table_id="myTable")
        #fig_image,pcr_html= pcr_calculation(cleaned_data,i)
        #return render(request, 'analysis.html', {'table': html_table,'fig_image':fig_image,'pcr_html':pcr_html})
    
    #return render(request, "analysis.html", {"items":items})

def nifty_chain(request):
    chain_data = analysis(request)
    cleaned_data = get_nifty_chain_clean_data(chain_data)
    cleaned_data = cleaned_data[['expiry','pcr','strike_price','underlying_spot_price','call_ltp','call_volume','call_oi','call_greeks_vega','call_greeks_theta','call_greeks_gamma','call_greeks_delta','call_greeks_iv','put_ltp','put_volume','put_oi','put_greeks_vega','put_greeks_theta','put_greeks_gamma','put_greeks_delta','put_greeks_iv']]
    html_table = cleaned_data.to_html(classes="table table-bordered", index=False, table_id="myTable")
    return render(request, 'option.html', {'table': html_table})

def live_pcr(request):
    chain_data = analysis(request)
    cleaned_data = get_nifty_chain_clean_data(chain_data)
    image_data,html_styled_data = pcr_calculation(cleaned_data)
    return render(request, 'live_pcr.html', {'table': html_styled_data,'fig_image':image_data})


def oi_change_data_display(request):
    chain_data = analysis(request)
    cleaned_data = get_nifty_chain_clean_data(chain_data)
    oi_data_table = oi_data_change(cleaned_data)
    return render(request, 'io_change.html', {'table': oi_data_table})

def get_the_acess_token():
    api_key = "" #ADD THIS
    api_secret = "" #ADD THIS
    redirect_uri = "http://localhost:5000"
    url = "https://api.upstox.com/v2/login/authorization/token"
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
    'expiry_date': '2025-03-20'
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

def pcr_calculation(cleaned_data):
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    from IPython.display import display, clear_output
    import datetime
    import io
    import base64
    import matplotlib
    matplotlib.use('Agg')
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
    new_row = pd.DataFrame({'Time': [formatted_time], 'Value': [pcr_change]})
    
    data = pd.concat([data, new_row], ignore_index=True)
    data.to_csv('output.csv', mode='a', header=False, index=False)
    
    data = pd.read_csv('output.csv', header=None, names=['Time', 'Value'])
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
    plt.close()
    buffer.seek(0)

    # Encode the image to base64
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode('utf-8')
    image_data = f"data:image/png;base64,{graphic}"
    return image_data,html_styled_data

def oi_data_change(cleaned_data):
    import pandas as pd
    import time
    from IPython.display import display, clear_output
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

    filtered_indices = result_CalPcr[result_CalPcr['closestPrice'].abs() ==min_value ].index
    index_value = filtered_indices[0] if not filtered_indices.empty else None
    changeinoi = result_CalPcr.iloc[[index_value-8,index_value-7,index_value-6,index_value-5,index_value-4,index_value-3,index_value-2,index_value-1,\
             index_value,index_value+1,index_value+2,index_value+3,index_value+4,index_value+5,index_value+6,index_value+7,index_value+8]][['pcr',\
             'call_oi','call_prev_oi','put_oi','put_prev_oi','strike_price','underlying_spot_price','closestPrice']]
    changeinoi.loc[:, 'call_oi_chng'] =  (changeinoi['call_oi'] - changeinoi['call_prev_oi'])
    changeinoi.loc[:, 'put_oi_chng'] =  (changeinoi['put_oi'] - changeinoi['put_prev_oi'])
    changeinoi1 = changeinoi[["call_prev_oi","call_oi","call_oi_chng","strike_price","put_oi","put_oi_chng","put_prev_oi","underlying_spot_price"]]
    def style_dataframe_with_bar(df, columns, max_values):
        def bar_fill(value, max_value):
            if pd.isna(value) or max_value == 0:  # Handle NaN or zero max_value
                return ""
            width_percentage = (value / max_value) * 100
            return (
            f"""
            background: linear-gradient(90deg, green {width_percentage}%, white {width_percentage}%);
            text-align: center;
            """
            )
    
    # Apply the bar_fill function to each column in the DataFrame
        styled_df = df.style
        for col, max_value in zip(columns, max_values):
            styled_df = styled_df.applymap(
                lambda x: bar_fill(x, max_value) if pd.notna(x) else "", subset=[col]
            )
    
        return styled_df

# Define the max values for the progress bars
    max_values = [10, 10]  # Max values for 'Call_OI_Score' and 'Put_OI_Score'

    max_value_call = changeinoi1['call_oi_chng'].abs().max()
    max_value_put = changeinoi1['put_oi_chng'].abs().max()
    max_value_call_oi = changeinoi1['call_oi'].abs().max()
    max_value_put_oi = changeinoi1['put_oi'].abs().max()
    actual_max = max(max_value_call, max_value_put,max_value_call_oi,max_value_put_oi)
    max_values = [max_value_call, max_value_put,max_value_call_oi,max_value_put_oi]
    clear_output(wait=True)
    oi_change_data = style_dataframe_with_bar(changeinoi1, ["call_oi_chng", "put_oi_chng","call_oi","put_oi"], max_values)
    html_styled_data = oi_change_data.to_html(classes="table table-striped", index=False)
    return html_styled_data

