from flask import Flask, request
from threading import Thread
import requests
import json


lyft_est = None


app = Flask(__name__)

@app.route('/', methods=['POST'])
def test():
    request.get_data()
    return request.args.get("start_lat")

@app.route('/ride_estimate', methods=['GET'])
def estimate_rides():
    global lyft_est
    lyft_est = None
    try:
        start_lat = request.args.get("start_lat")
        start_long = request.args.get("start_long")
        end_lat = request.args.get("end_lat")
        end_long = request.args.get("end_long")

        lyft_thread = Thread(target=lyft_estimate, args=(start_lat, start_long, end_lat, end_long), )
        lyft_thread.start()
        lyft_thread.join()
        uber_est = uber_estimate(start_lat, start_long, end_lat, end_long)

        estimates = {
            "lyft_est": lyft_est,
            "uber_est": uber_est
        }

        return json.dumps(estimates)

    except Exception:
        return json.dumps({"status": "Failed"})


def lyft_estimate2():
    client_token = ""

    k = {
        "start_lat": 37.7763,
        "start_long": -122.391,
        "end_lat": 37.7972,
        "end_long": -122.4533
    }

    url = "https://api.lyft.com/v1/cost?start_lat={}&start_lng={}&end_lat={}" \
                  "&end_lng={}".format(k["start_lat"], k["start_long"],
                                       k["end_lat"], k["end_long"])
    headers = {
        "Authorization": "bearer {}".format(client_token),
        "Content-Type": "application/json"
    }
    r = requests.get(url, headers=headers)
    return r.content


def lyft_estimate(start_lat, start_long, end_lat, end_long):
    client_token = ""

    params = {
        "start_lat": start_lat,
        "start_lng": start_long,
        "end_lat": end_lat,
        "end_lng": end_long
    }

    url = "https://api.lyft.com/v1/cost"
    headers = {
        "Authorization": "bearer {}".format(client_token),
        "Content-Type": "application/json"
    }
    r = requests.get(url, headers=headers, params=params)
    estimate_dict = r.json()

    lyft_line = next((item for item in estimate_dict["cost_estimates"] if item['ride_type'] == "lyft_line"), None)
    lyft = next((item for item in estimate_dict["cost_estimates"] if item['ride_type'] == "lyft"), None)
    lyft = get_lyft_dollars(lyft)

    lyft_dict = {
        "lyft": lyft
    }

    if lyft_line:
        lyft_line = get_lyft_dollars(lyft_line)
        lyft_dict["lyft_line"] = lyft_line

    global lyft_est
    lyft_est = lyft_dict #r.json()


def get_lyft_dollars(lyft_dict):
    max = lyft_dict.get("estimated_cost_cents_max")
    max_dollars = "-" + "%.2f" % round(max/100, 2)
    min = lyft_dict.get("estimated_cost_cents_min")
    min_dollars = "$" + "%.2f" % round(min/100, 2)

    lyft_dict["estimate"] = min_dollars + max_dollars
    return lyft_dict


def uber_estimate2():
    server_token = ""

    params = {
        "start_latitude": 37.7763,
        "start_longitude": -122.391,
        "end_latitude": 37.7972,
        "end_longitude": -122.4533
    }

    url = "https://api.uber.com/v1.2/estimates/price" #\
            #   "?start_latitude={}&start_longitude={}&end_latitude={}" \
            #         "&end_longitude={}".format(k["start_latitude"], k["start_longitude"],
            #                         k["end_latitude"], k["end_longitude"])
    headers = {
        "Authorization": "Token {}".format(server_token),
        "Content-Type": "application/json",
        "Accept-Language": "en_US"
    }
    r = requests.get(url, headers=headers, params=params)

    return r.content


def uber_estimate(start_lat, start_long, end_lat, end_long):
    server_token = ""

    params = {
        "start_latitude": start_lat,
        "start_longitude": start_long,
        "end_latitude": end_lat,
        "end_longitude": end_long
    }

    url = "https://api.uber.com/v1.2/estimates/price"
    headers = {
        "Authorization": "Token {}".format(server_token),
        "Content-Type": "application/json",
        "Accept-Language": "en_US"
    }
    r = requests.get(url, headers=headers, params=params)
    estimate_dict = r.json()

    uber_pool = next((item for item in estimate_dict["prices"] if item['display_name'] == "UberPool"), {})
    uber_x = next((item for item in estimate_dict["prices"] if item['display_name'] == "UberX"), None)
    uber_pool_high = uber_pool.get('high_estimate')
    uber_pool_low = uber_pool.get('low_estimate')
    if uber_pool_high and uber_pool_low:
        express_pool = ((uber_pool_high + uber_pool_low) / 2) * .7
    else:
        express_pool = None

    uber_estimate = {
        "uber_x": uber_x
    }
    if uber_pool:
        uber_estimate["uber_pool"] = uber_pool
        uber_estimate["express_pool"] = {
            "estimate": "$" + str(express_pool)
        }

    return uber_estimate #r.json()

