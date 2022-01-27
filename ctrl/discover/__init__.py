import os
import platform
from socket import gethostbyaddr, herror
from datetime import datetime

import yaml
from netmiko import SSHDetect
import nmap
import pytz

class Discover:

    def __init__(self, appconfig):
        self.credentials = appconfig.CREDENTIALS

    def ping(self, ip):
        """ Pings the IP given and if a response is found, add to redis queue
        Parameters
        ----------
            ip:str
                ip address of target device
        """

        #set the appropriate os level ping parameter
        current_os = platform.system().lower()
        if current_os == "windows":
            parameter = "-n"
        else:
            parameter = "-c"

        #perform the ping check against the ip using the os ping command
        ping_check = os.system(f"ping {parameter} 1 -w2 {str(ip)} > /dev/null 2>&1")

        #if ping is 0 (meaning response) return true, if not return false
        if ping_check == 0:
            return True
        else:
            return False

    def device_info(self, ip):
        """ attempts to ssh into the device and determine the device-type then records the inormation into elasticsearch
        Parameters
        ----------
            ip:str
                ip address of target device
        """

        # try to get the hostname
        # TODO does this need to be an error or can it be explicit?
        try:
            hostname = gethostbyaddr(ip)
            hostname = hostname[0]
        except herror:
            hostname = ip

        # create the record dictionary
        record = {
            "ip": ip,
            "hostname": hostname,
            "credential": "0",
            "device_type": "unknown"
        }

        # open the credential file
        with open(self.credentials, "r") as file:
            credentials = yaml.full_load(file)

        # for each credential, loop and try until success
        for credential in credentials:

            # create the net device dictionary
            net_device = {
                'device_type': 'autodetect',
                'ip': ip,
                'username': credential['username'],
                'password': credential['password'],
                'secret': credential['secret'],
                'port': 22,
            }

            # try to perform SShDetect from netmiko
            try:
                guesser = SSHDetect(**net_device)
                device_type = guesser.autodetect()

                if device_type:
                    pass
                else:
                    device_type = "unknown"

            # exception (such as ssh timeout) consider the device type to be unknown
            except Exception as e:
                device_type = "unknown"

            # if the device type is not unknown, set the credential and device type from SSHDetect and break the loop
            if "unknown" not in device_type:
                record['credential'] = str(credential['id'])
                record['device_type'] = device_type
                break

        return record

    def nmap_info(self, ip, hostname=None):
        """ performs nmap scan, formats with a timestamp and returns

        Parameters
        ----------
            ip:str
                ip address of target device
            hostname: str
                hostname of the device (DNS record)
        """
        # TODO add hostname lookup
        # TODO add arg for the ports to be scanned (TCP)

        nm = nmap.PortScanner()
        scan_info = nm.scan(ip, '22-1024,5601,8443,9200')

        # if the scan returns information for the ip, reformat the return dictionary
        if ip in scan_info['scan']:
            scan_info['scan'] = scan_info['scan'][ip]

        # generate the timestamp
        date_time_obj = datetime.strptime(str(datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f%z')),
                                          '%Y-%m-%dT%H:%M:%S.%f')
        timezone = pytz.timezone('America/New_York')
        timezone_date_time_obj = timezone.localize(date_time_obj)

        if hostname:
            pass
        else:
            hostname = ip

        # apply extra info to the nmap scan results
        scan_info['@timestamp'] = timezone_date_time_obj.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
        scan_info['hostname'] = hostname

        return scan_info
