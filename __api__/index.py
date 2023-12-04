import requests
import logging
    
def transfer(_from, to, amount):
    try:
        response = requests.get(f"http://localhost:8000/transfer/{_from}/{to}/{amount}")
    except:
        logging.error("Unable to send request to the EMPIRE server.")
    else:
        print(response.text)
        return response.text

def balanceOf(account):
    try:
        response = requests.get(f"http://localhost:8000/balance/{account}")
    except:
        logging.error("Unable to send request to the EMPIRE server.")
    else:
        print(response.json())
        return response.json()