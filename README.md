# TestTunnelStatus
This script can be used to list the Tunnels associated with a RN/SC and print the status of the tunnel.

Input:
./Tunnel_Status.py --help            
usage: Tunnel_Status.py [-h] [-t1 T1SECRET] [-node NODETYPE] [-state NODESTATE]

Checking the operational status of tunnel associated with RN/SC .

optional arguments:
  -h, --help            show this help message and exit
  -t1 T1SECRET, --T1Secret T1SECRET
                        Input secret file in .yml format for the tenant(T1)
  -node NODETYPE, --NodeType NODETYPE
                        Inputs: all/SC/RN for Service Connection and Remote Network
                        respectively
  -state NODESTATE, --NodeState NODESTATE
                        Inputs: all/up/down/inactive
                        
CLI: ./Tunnel_Status.py -t1 T1-secret.yml -node all -state down

Output:
+-------------+------------+--------------+--------------------+
| Tunnel Name | Site Name  | Tunnel State | Tunnel Type        |
+=============+============+==============+====================+
| HQ-Tunnel   | Datacenter | Down         | Service Connection |
+-------------+------------+--------------+--------------------+
