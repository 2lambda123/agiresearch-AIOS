import re
import pandas as pd
import numpy as np

# This tool refers to the "DistanceMatrix" in the paper. Considering this data obtained from Google API, we consistently use this name in the code. 
# Please be assured that this will not influence the experiment results shown in the paper. 

class GoogleDistanceMatrix:
    def __init__(self, subscription_key: str="") -> None:
        self.gplaces_api_key: str = subscription_key
        self.data =  pd.read_csv('../database/googleDistanceMatrix/distance.csv')
        print("GoogleDistanceMatrix loaded.")

    def run(self, origin, destination, mode='driving'):
        origin = extract_before_parenthesis(origin)
        destination = extract_before_parenthesis(destination)
        info = {"origin": origin, "destination": destination,"cost": None, "duration": None, "distance": None}
        response = self.data[(self.data['origin'] == origin) & (self.data['destination'] == destination)]
        if len(response) > 0:
                if response['duration'].values[0] is None or response['distance'].values[0] is None or response['duration'].values[0] is np.nan or response['distance'].values[0] is np.nan:
                    return "No valid information."
                info["duration"] = response['duration'].values[0]
                info["distance"] = response['distance'].values[0]
                if 'driving' in mode:
                    info["cost"] = int(eval(info["distance"].replace("km","").replace(",","")) * 0.05)
                elif mode == "taxi":
                    info["cost"] = int(eval(info["distance"].replace("km","").replace(",","")))
                if 'day' in info["duration"]:
                    return "No valid information."
                return f"{mode}, from {origin} to {destination}, duration: {info['duration']}, distance: {info['distance']}, cost: {info['cost']}"

        return f"{mode}, from {origin} to {destination}, no valid information."
    
def extract_before_parenthesis(s):
    match = re.search(r'^(.*?)\([^)]*\)', s)
    return match.group(1) if match else s