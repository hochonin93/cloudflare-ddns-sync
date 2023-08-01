from dotenv import load_dotenv
import time
import os
import re
import sys
import json
import requests


def now_time():
    localtime = time.localtime()
    return time.strftime("%I:%M:%S", localtime)


def pprint(message: str):
    time = now_time()
    print(f"{time} {message}", flush=True)


def find_zone_id():
    # Search for the zone id of the specified domain
    res = requests.get(f"{domain}/zones",
                       params={"name": "bugwc.com"}, headers=headers).json()
    if res['success'] and res['result_info']['count'] == 1:
        return res['result'][0]['id']
    return False


def find_record_id(zone_id):
    # Search for the record id of the specified zone
    res = requests.get(
        f"{domain}/zones/{zone_id}/dns_records", params={"name": RECORD_NAME, "type": RECORD_TYPE}, headers=headers).json()
    if res['success'] and res['result_info']['count'] == 1:
        return res['result'][0]['id']
    return False


def update_record_ip(zone_id, record_id, current_ip):
    # Update the record of the specified zone
    data = {
        "content": current_ip,
        "name": RECORD_NAME,
        "proxied": IS_PROXIED,
        "type": RECORD_TYPE,
        "TTL": TTL
    }
    res = requests.put(
        f"{domain}/zones/{zone_id}/dns_records/{record_id}", headers=headers, json=data).json()

    return res['success']


def current_ip():
    # Get the current IP location
    ipv4_regex = r'([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])'

    response = requests.get("https://cloudflare.com/cdn-cgi/trace")
    ip = re.search(r'^ip=(.*)', response.text, flags=re.MULTILINE)

    if ip is None:
        response = requests.get("https://api.ipify.org")
        if response.status_code == 200:
            ip = response.text
        else:
            response = requests.get("https://ipv4.icanhazip.com")
            ip = response.text if response.status_code == 200 else None
    else:
        ip = ip.group(1)
    return ip


load_dotenv()


domain = "https://api.cloudflare.com/client/v4"
X_AUTH_KEY = os.getenv("X_AUTH_KEY")
X_AUTH_EMAIL = os.getenv("X_AUTH_EMAIL")
RECORD_NAME = os.getenv("RECORD_NAME")
RECORD_TYPE = os.getenv("RECORD_TYPE")
IS_PROXIED = bool(os.getenv("IS_PROXIED"))
TTL = int(os.getenv("TTL"))
SLEEP = int(os.getenv("SLEEP"))

headers = {
    "Content-Type": "application/json",
    "X-Auth-Email": X_AUTH_EMAIL,
    "X-Auth-Key": X_AUTH_KEY
}

while 1:
    # Find zone id
    zone_id = find_zone_id()
    if not zone_id:
        sys.exit()

    # Find record id
    record_id = find_record_id(zone_id)
    # Get current IP
    ip = current_ip()
    # Update record's IP
    if update_record_ip(zone_id, record_id, ip):
        pprint(f"success:true,ip update : {ip}")
    else:
        pprint("success:false")

    time.sleep(SLEEP)
