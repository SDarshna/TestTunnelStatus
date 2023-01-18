#!/usr/bin/env python3

import prisma_sase
import io
import requests
import json
import os
import termtables as tt
import yaml
import argparse


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

def check_PA_node_state(node, state):
    #Update the node value
    if node == "SC":
        node_value = [51]
    elif node == "RN":
        node_value = [48]
    elif node == "all":
        node_value = [48,51]

    #Update the state value
    if state == "up":
        state_value = [1]
    elif state == "down":
        state_value = [3]
    elif state == "init":
        state_value = [0]
    elif state == "inactive":
        state_value = [2]
    elif state == "all":
        state_value = [0,1,2,3] 
    


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
            "values": [30]
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
        if data["node_type"] == 48:
           node_type = "Remote Network"
        elif data["node_type"] == 51:
           node_type = "Service Connection"

        if data["tunnel_state"] == 1:
            tunnel_state = "Up"
        elif data["tunnel_state"] == 0:
            tunnel_state = "Init" 
        elif data["tunnel_state"] == 2:
            tunnel_state = "Inactive"
        elif data["tunnel_state"] == 3:
            tunnel_state = "Down"
        
        RList.append([data['tunnel_name'], data["site_name"], tunnel_state,node_type])
        index+=1

    table_string = tt.to_string(RList, Header, style=tt.styles.ascii_thin_double)
    print(table_string)

def go():
    parser = argparse.ArgumentParser(description='Checking the operational status of tunnel associated with RN/SC .')
    parser.add_argument('-t1', '--T1Secret', help='Input secret file in .yml format for the tenant(T1) ')
    parser.add_argument('-node', '--NodeType', help='Inputs: all/SC/RN for Service Connection and Remote Network respectively ')  
    parser.add_argument('-state', '--NodeState', help='Inputs: all/up/down/inactive')
     
    args = parser.parse_args()
    T1_secret_filepath = args.T1Secret
    node = args.NodeType
    state = args.NodeState

    #Pass the secret of 'from tenant' to login
    sdk_login_to_controller(T1_secret_filepath)

    #Check PA node state
    check_PA_node_state(node, state)



if __name__ == "__main__":
    go()