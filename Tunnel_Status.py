#!/usr/bin/env python3

import prisma_sase
import io
import requests
import json
import csv
import time
import os
import termtables as tt
import yaml
import argparse

#Globals:
node_val_dict = {"SC": [51], "RN": [48], "all": [48,51]}
state_val_dict = {"up":[1], "down": [3],"init":[0],"inactive":[2],"all":[0,1,2,3]}
node_type_str_dict = {"48": "Remote Network", "51": "Service Connection"}
tunnel_state_str_dict = {"0": "Init", "1":"Up", "2":"Inactive", "3":"Down"}

def sdk_login_to_controller(filepath):
    with open(filepath) as f:
        client_secret_dict = yaml.safe_load(f)
        client_id = client_secret_dict["client_id"]
        client_secret = client_secret_dict["client_secret"]
        tsg_id_str = client_secret_dict["scope"]
        global tsg
        tsg = tsg_id_str.split(":")[1]
        #print(client_id, client_secret, tsg)

    global sdk 
    sdk = prisma_sase.API(controller="https://sase.paloaltonetworks.com/", ssl_verify=False)
   
    sdk.interactive.login_secret(client_id, client_secret, tsg)
    print("--------------------------------")
    print("Script Execution Progress: ")
    print("--------------------------------")
    print("Login to TSG ID {} successful".format(tsg))



def create_csv_output_file(Header, RList):
    with open('tunnel-status.csv', mode='w') as csv_file:
        csvwriter = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(Header)
        for Rec in RList:
            csvwriter.writerow(Rec)

def create_json_output_file():
    #create a dictionary
    data_dict = {}
 
    with open('tunnel-status.csv', encoding = 'utf-8') as csv_file_handler:
        csv_reader = csv.DictReader(csv_file_handler)
        i=0
        for rows in csv_reader:
            key = i
            data_dict[key] = rows
            i += 1
 
    with open('tunnel-status.json', 'w', encoding = 'utf-8') as json_file_handler:
        json_file_handler.write(json.dumps(data_dict, indent = 4))

def check_PA_node_state(node, state,days):
   
    node_value = node_val_dict[node]
    state_value = state_val_dict[state]

    rn_tunnel_status_url="https://pa-us01.api.prismaaccess.com/api/sase/v2.0/resource/custom/query/tunnels/tunnel_list"

    header = {
        "prisma-tenant": tsg
    }
    sdk._session.headers.update(header)

    payload = {
    "properties": [
        {
        "property": "tunnel_name"
        },
        {
        "property": "site_name"
        },
        {
        "property": "tunnel_state"
        },
        {
        "property": "node_type"
        }

    ],
    "filter": {
        "operator": "AND",
        "rules": [
        {
            "property": "event_time",
            "operator": "last_n_days",
            "values": [days]
        },
        
        {
            "property": "tunnel_state",
            "operator": "in",
            "values": state_value
        },
        {
            "property": "node_type",
            "operator": "in",
            "values": node_value
        }
     
        ]
    }
    }
   
    #print(payload)

    resp = sdk.rest_call(url=rn_tunnel_status_url, data=payload, method="POST")
    #print(resp.json())
    try:
        dataList = resp.json()["data"]
        if dataList == []:
            exit(0)
    except:
        print("No data found")
        exit(0)

    Header = ["Tunnel Name", "Site Name", "Tunnel State", "Tunnel Type"]
    RList = []
    index = 0
    for data in dataList:
        #print(data)
        node_type = node_type_str_dict[str(data["node_type"])]
        tunnel_state = tunnel_state_str_dict[str(data["tunnel_state"])]
           
        RList.append([data['tunnel_name'], data["site_name"], tunnel_state,node_type])
        index+=1

    create_csv_output_file(Header,RList)
    create_json_output_file()

    table_string = tt.to_string(RList, Header, style=tt.styles.ascii_thin_double)
    print(table_string)

def go():
    parser = argparse.ArgumentParser(description='Checking the operational status of tunnel associated with RN/SC .')
    parser.add_argument('-t1', '--T1Secret', help='Input secret file in .yml format for the tenant(T1) ',default="T1-secret.yml")
    parser.add_argument('-node', '--NodeType', help='Inputs: all/SC/RN for Service Connection and Remote Network respectively ',default='all')  
    parser.add_argument('-state', '--NodeState', help='Inputs: all/up/down/inactive', default='all')
    parser.add_argument('-days', '--Days', help='Data fetched for the last n days ',default=30)

    args = parser.parse_args()
    T1_secret_filepath = args.T1Secret
    node = args.NodeType
    state = args.NodeState
    days = int(args.Days)

    #Pass the secret of 'from tenant' to login
    sdk_login_to_controller(T1_secret_filepath)

    #Check PA node state
    check_PA_node_state(node, state,days)



if __name__ == "__main__":
    go()