import pan.xapi
import xmltodict
import ipaddress
import json

class PanOSFirewallError(Exception):
    pass

class PanOSFirewall():
    """
    |  Creates an object with all the needed variables and functions
    |  utilizes pan-python to call the various APIs.
    """
    def __init__(self, ip, username, password, hostname=None):

        """ __init__
        Parameters
        ----------"""

        if hostname:
            self.hostname = hostname
        else:
            self.hostname = ip

        try:
            self.xapi = pan.xapi.PanXapi(hostname=ip,api_username=username, api_password=password)
        except pan.xapi.PanXapiError:
            raise PanOSFirewallError("failed to log into ")

        self.interfaces = None
        self.gateways = None

    def retrieve_interfaces(self):

        self.interfaces = []

        cmd = "<show><interface>all</interface></show>"
        self.xapi.op(cmd=cmd)

        interfaces = xmltodict.parse("<root>" + self.xapi.xml_result() + "</root>")['root']['ifnet']['entry']
        if type(interfaces) == list:
            pass
        else:
            interfaces = [interfaces]

        for interface in interfaces:
            self.interfaces.append(interface)

    def retrieve_gateways(self):

        self.gateways = []

        cmd = "<show><global-protect-gateway><gateway></gateway></global-protect-gateway></show>"
        self.xapi.op(cmd=cmd)

        gateways = xmltodict.parse("<root>" + self.xapi.xml_result() + "</root>")['root']['entry']
        if type(gateways) == list:
            pass
        else:
            gateways = [gateways]

        for gateway in gateways:
            self.gateways.append(gateway)



