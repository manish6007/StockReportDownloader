from breeze_connect import BreezeConnect

# Initialize SDK
breeze = BreezeConnect(api_key="Q8h2250667_3783&075)iY55K73276#3")

# Obtain your session key from https://api.icicidirect.com/apiuser/login?api_key=YOUR_API_KEY
# Incase your api-key has special characters(like +,=,!) then encode the api key before using in the url as shown below.
import urllib
print("https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus("Q8h2250667_3783&075)iY55K73276#3"))

# Generate Session
breeze.generate_session(api_secret="^O57155529d~o1tJbHf973V907276B83",
                        session_token="47417053")

# Generate ISO8601 Date/DateTime String
import datetime
iso_date_string = datetime.datetime.strptime("28/02/2021","%d/%m/%Y").isoformat()[:10] + 'T05:30:00.000Z'
iso_date_time_string = datetime.datetime.strptime("28/02/2021 23:59:59","%d/%m/%Y %H:%M:%S").isoformat()[:19] + '.000Z'

# Connect to websocket(it will connect to tick-by-tick data server)
breeze.ws_connect()

# Callback to receive ticks.
def on_ticks(ticks):
    print("Ticks: {}".format(ticks))

# Assign the callbacks.
breeze.on_ticks = on_ticks

reponse = breeze.get_historical_data_v2(interval="1minute",
                            from_date= "2024-09-15T07:00:00.000Z",
                            to_date= "2024-09-17T07:00:00.000Z",
                            stock_code="ITC",
                            exchange_code="NSE",
                            product_type="cash")

response = breeze.get_demat_holdings()
#print(response)

# subscribe oneclick strategy stream
breeze.subscribe_feeds(stock_code = "ITC", exchange_code = "NSE", product_type = "cash")