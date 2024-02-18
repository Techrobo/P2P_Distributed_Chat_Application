# P2P_Distributed_Chat_Application
Peer-to-Peer Chat-based Distributed Application by Group 18 :  Ikenna Abara[3644968] and Shubham Gupta[3506475]


#Instructions

1. Firewall Settings :

In Linux Sytsem , Allow the Inbound and Outbound UDP messages :
$sudo iptables -A INPUT -p udp -j ACCEPT
$sudo iptables -A OUTPUT -p udp -j ACCEPT
If you want to keep the changes persistantly across reboots :
$sudo iptables-save > /etc/iptables/rules.v4   # For IPv4

In Linux Sytsem , Allow the Inbound and Outbound TCP messages :
$sudo iptables -A INPUT -p tcp -j ACCEPT
$sudo iptables -A OUTPUT -p tcp -j ACCEPT
If you want to keep the changes persistantly across reboots :
$sudo iptables-save > /etc/iptables/rules.v4   # For IPv4

In Windows System , Allow UDP Traffic on Windows Defender Firewall:

1.Open Windows Defender Firewall Settings:
    #Go to Control Panel > System and Security > Windows Defender Firewall.
2.Create Inbound Rule (Receive UDP Traffic):
    #Click on "Advanced settings" on the left-hand side panel.
    #In the Windows Defender Firewall with Advanced Security window, click on "Inbound Rules".
    #Click "New Rule..." in the Actions panel on the right-hand side.
    #Select "Port" and click "Next".
    #Select "UDP" and specify the port number you want to allow for incoming traffic. Click "Next".
    #Choose "Allow the connection" and click "Next".
    #Specify when the rule applies (domain, private, public). Usually, you'll want to select all options. Click "Next".
    #Give your rule a name and description, then click "Finish".
3.Create Outbound Rule (Send UDP Traffic):
    #Follow the same steps as above, but instead of selecting "Inbound Rules", choose "Outbound Rules".
    #Specify the same port number and protocol (UDP).
    #Allow the connection and set the appropriate profile settings.
4.Verify Rules:
    #After creating both inbound and outbound rules, verify that they appear in the list of rules in Windows Defender Firewall with Advanced Security.

In Windows System , Allow TCP Traffic on Windows Defender Firewall:

1.Open Windows Defender Firewall Settings:
    #Go to Control Panel > System and Security > Windows Defender Firewall.
2.Create Inbound Rule (Receive TCP Traffic):
    #Click on "Advanced settings" on the left-hand side panel.
    #In the Windows Defender Firewall with Advanced Security window, click on "Inbound Rules".
    #Click "New Rule..." in the Actions panel on the right-hand side.
    #Select "Port" and click "Next".
    #Select "TCP" and specify the port number you want to allow for incoming traffic. Click "Next".
    #Choose "Allow the connection" and click "Next".
    #Specify when the rule applies (domain, private, public). Usually, you'll want to select all options. Click "Next".
    #Give your rule a name and description, then click "Finish".
3.Create Outbound Rule (Send TCP Traffic):
    #Follow the same steps as above, but instead of selecting "Inbound Rules", choose "Outbound Rules".
    #Specify the same port number and protocol (TCP).
    #Allow the connection and set the appropriate profile settings.
4.Verify Rules:
    #After creating both inbound and outbound rules, verify that they appear in the list of rules in Windows Defender Firewall with Advanced Security.


2. Run the command in terminal and follow the command line instructions :
$ python .\app.py 