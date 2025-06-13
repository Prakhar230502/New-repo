import pandas as pd
import os 
import config
import excel_functions
from kiteconnect import KiteConnect

def print_url(user_id: str):
    """ Function to generate URL for access token """
    kite = KiteConnect(api_key=config.config_keys[user_id]["api_key"])

    # Step 1: Generate a login URL
    return kite.login_url()

def generate_access_token(user_id: str, request_token):
    """ Function to generate access token for KiteConnect API """
    kite = KiteConnect(api_key=config.config_keys[user_id]["api_key"])
    # Step 3: Use the request token to obtain the access token
    data = kite.generate_session(request_token, api_secret=config.config_keys[user_id]["api_secret"])
    access_token = data["access_token"]
    excel_functions.set_access_token(user_id, access_token)
    print(user_id, ": Access Token: ", access_token)

if __name__ == "__main__":
    print_url()
    request_token = input("Enter the request token: ")
    generate_access_token(request_token)
