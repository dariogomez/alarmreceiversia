#!/usr/bin/python3
# -*- coding: utf-8 -*- 

import sys
import re
import json
import requests
from alarmManager import Config

Config.load('/etc/alarmReceiver.conf')

def parse_line(payload: str):
    print("mensaje: {}".format(payload))
    #37070047"SIA-DCS"0038R0L0#10303117[#10303117|Nri0001/BH005]_13:44:48,08-17-2022
    # All data starts with [ and ends with ]
    split_payload = payload.split('"')
    payload_end = split_payload[2]
    event_date = payload_end.split('_')[1]
    print("event_date: {}".format(event_date))
    message_block = re.findall(r'\[(.*?)\]', payload_end)[0]
    print(message_block)
    res = parse_adc_cid_message(message_block, event_date)
    print(res)

    if Config.get('post_send'):
        send_post_sia_event(res)

    return res


def parse_adc_cid_message(message: str, event_date: str) -> dict:
    #37070047"SIA-DCS"0038R0L0#10303117[#10303117|Nri0001/BH005]_13:44:48,08-17-2022
    message_blocks = message.split('|')

    ##10303117|Nri0001/BA005

    # starts with a #ACCT, so we drop the pound
    account_number = message_blocks[0][1:]
    print("account_number: {}".format(account_number))

    contact_id = message_blocks[1].split('/')
    print("contact_id: {}".format(contact_id))

    # 1 = New Event or Opening,
    # 3 = New Restore or Closing,
    # 6 = Previously reported condition still present (Status report)
    event_qualifier = contact_id[0][0]
    print("event_qualifier: {}".format(event_qualifier))

    # 3 decimal(!) digits XYZ (e.g. 602)
    #event_code = contact_id[0][1:]
    #print("event_code: {}".format(event_code))

    # 2 characters digits XY (e.g. BH)
    event_code = contact_id[1][0:2]
    print("event_code: {}".format(event_code))

    # 2 decimal(!) digits GG, 00 if no info (e.g. 01)
    group_or_partition_number = contact_id[0]
    print("group_or_partition_number: {}".format(group_or_partition_number))

    # 3 decimal(!) digits CCC, 000 if no info (e.g. 001)
    zone_number_or_user_number = int(contact_id[1][2:])
    print("zone_number_or_user_number: {}".format(zone_number_or_user_number))

    return {
        'event_date': event_date,
        'account_number': account_number,
        'event_qualifier': event_qualifier,
        'event_code': event_code,
        'group_or_partition_number': group_or_partition_number,
        'zone_number_or_user_number': zone_number_or_user_number
    }


def send_post_sia_event(data: dict):
    print(Config.get('post_send_url'))
    print("post: {}".format(data))
    send_post_data(Config.get('post_send_url'), data)


def send_post_data(url, json_data):
    reponse_codes = [200, 201]
    byte_length = str(sys.getsizeof(json_data))
    headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
    response = requests.post(url, data=json.dumps(json_data), headers=headers)

    if response.status_code not in reponse_codes:
        raise Exception(response.status_code, response.text)