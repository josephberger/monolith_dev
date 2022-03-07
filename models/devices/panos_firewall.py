import pan.xapi
import xmltodict
import ipaddress
import json

class PanOSFirewallError(Exception):
    pass

class PanOSFirewall():
    """
    |  PanOS Firewall
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
        self.zones = None
        self.gateways = None

    def retrieve_interfaces(self):

        self.interfaces = []
        self.zones = []
        cmd = "<show><interface>all</interface></show>"
        self.xapi.op(cmd=cmd)

        #TODO make this explicit instead of implicit
        try:
            interfaces = xmltodict.parse("<root>" + self.xapi.xml_result() + "</root>")['root']['ifnet']['entry']
            if type(interfaces) == list:
                pass
            else:
                interfaces = [interfaces]

            zones = set()

            for interface in interfaces:
                self.interfaces.append(interface)
                if 'zone' in interface:
                    zones.add(interface['zone'])

            for zone in zones: self.zones.append({"name":zone})

        except:
            pass

    def retrieve_gateways(self):

        self.gateways = []

        cmd = "<show><global-protect-gateway><gateway></gateway></global-protect-gateway></show>"
        self.xapi.op(cmd=cmd)

        # TODO make this explicit instead of implicit
        try:
            gateways = xmltodict.parse("<root>" + self.xapi.xml_result() + "</root>")['root']['entry']
            if type(gateways) == list:
                pass
            else:
                gateways = [gateways]

            for gateway in gateways:
                self.gateways.append(gateway)
        except:
            pass



