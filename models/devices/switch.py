#
# Joseph Berger <airmanberger@gmail.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import netmiko
import json
import re

class SwitchCLIError(Exception):
    pass

class SwitchCLI:
    """
    Switch CLI class for cisco_ios, arista_eos or cisco_nxos

    ...

    Attributes
    ----------
    ip: str
        ip of the devicepip3
    username: str
        uername of the device
    device_type: str
        device type (must be netmiko compatable)
    hostname: str, optional
        hostname will be set to ip if not provided (fqdn is best)
    cli: netmiko.ConnectHandler
        embeded netmiko ConnectHandler object
    line_config: list
        list of configuration strings
    config: str
        entire config as one string
    interfaces: list
        list of dictionaries containing interface information
    vlans: list
        list of dictionaries containing vlan information
    vrfs: list
        list of dictionaries containing vrf information
    lldp_neighbors: list
        list of dictionaries containing lldp neighbor information
    status: str
        default sets to f"{hostname}: connected" once it has been fully instanciated

    Methods
    -------
    retrive_config()
        pulls the config and populates config and list_config variables
    parse_interfaces()
        pulls the interface config information and populates the interfaces variable
    retrieve_vlans()
        pulls the vlan config information and populates the vlan variable
    parse_vrfs()
        pulls the vrf config information and populates the vrf variable
    retrieve_lldp_neighbors()
        pulls the lld information information and populates the lld_neighbors variable
    retrieve_equipment()
        pulls the lld information information and populates the lld_neighbors variable
    """
    def __init__(self, ip, username, password, secret, device_type,hostname=None,slow_connection=False):
        """
        Parameters
        ----------
            ip: str
                ip of the devicepip3
            username: str
                uername of the device
            password: str
                primary password assiciated with the username
            secret: str
                enable password for the device
            device_type: str
                device type (must be netmiko compatable)
            hostname: str, optional
                hostname of the device
            slow_connection: bool
                flag it as a slow connection and use the delay factor for commands
        """

        supported_dt = ['cisco_ios','cisco_nxos','arista_eos']

        if hostname:
            self.hostname = hostname
        else:
            self.hostname = ip

        if device_type not in supported_dt:

            raise SwitchCLIError(f"{self.hostname}: {device_type} device type not supported.  Must be {','.join(supported_dt)}.")

        self.ip = ip
        self.device_type = device_type

        net_device = {
            'device_type': device_type,
            'ip': ip,
            'username': username,
            'password': password,
            'secret': secret,
            'port': 22,
        }

        try:
            self.cli = netmiko.ConnectHandler(**net_device)
        except Exception as e:
            raise SwitchCLIError(f"{self.hostname}: could not connect over ssh (port 22)")

        try:
            self.cli.enable()
        except ValueError:
            raise SwitchCLIError(f"{self.hostname}: could not enter enable mode, check password.")

        self.line_config = []

        self.config = None

        self.interfaces = None

        self.vlans = None

        self.vrfs = None

        self.lldp_neighbors = None

        self.equipment = None

        self.connected_routes = None

        self.static_routes = None

        self.ospf_routes = None

        self.protocols = None

        self.status = "connected"

        self.slow_connection = slow_connection


    def retrive_config(self):
        """ pulls the config from the device via netmiko and stores in self.config
        also parses out the config into lines and adds delination markers which is then
        stored in self.line_config

        """

        if self.slow_connection:

            self.config = self.cli.send_command("show running-config",delay_factor=5, max_loops=15000)
        else:
            self.config = self.cli.send_command("show running-config")

        lines = self.config.split("\n")
        self.line_config = []
        for line in lines:
            if line == "":
                line = "!"
            self.line_config.append(line)

    def retrieve_interfaces(self):
        self.parse_interfaces()
    def parse_interfaces(self):
        """ parses the self.config variable for interfaces, determines config for each
        then places them as a list of dictionaries in self.interfaces

        """

        if self.config == None:
            self.retrive_config()

        # find all the interfaces
        raw_ints = re.findall(r"\ninterface (.+?)\n", self.config)

        #interface list that gets returned
        interfaces = []

        for index, line in enumerate(self.line_config):
            for raw_int in raw_ints:
                interface = {
                    "name":raw_int,
                    "config":[]
                }
                if "interface " + raw_int == line:

                    ipaddr_index = 1
                    ip_addresses = {}
                    config_index = index + 1
                    config_line = self.line_config[config_index]
                    while config_line != "!":
                        if config_line[0] == " ":
                            interface["config"].append((config_line[1:]))
                        if "description " in config_line:
                            interface["description"] = config_line.replace(" description ", "")
                        if "switchport mode " in config_line:
                            interface["mode"] = config_line.replace(" switchport mode ", "")
                        if "ip address " in config_line:
                            ip_addresses[str(ipaddr_index)] = config_line.replace(" ip address ", "")
                            ipaddr_index += 1
                        config_index += 1
                        config_line = self.line_config[config_index]
                    if len(ip_addresses) > 0:
                        interface['addresses'] = ip_addresses
                    interfaces.append(interface)
                    break

        self.interfaces = interfaces


    def retrieve_vlans(self):
        """ parses the self.config variable for vlans, determines config for each
        then places them as a list of dictionaries in self.vlans

        """

        raw_vlans = re.findall(r"\n([0-9]+)\s*(\S*)\s*",self.cli.send_command("show vlan brief"))
        vlans = []
        for vl in raw_vlans:
            vlans.append({
                "number":vl[0],
                "name":vl[1]
            })

        self.vlans = vlans

    def parse_vrfs(self):
        """ parses the self.line_config variable for vrf definitions, determines config for each
        then places them as a list of dictionaries in self.vrfs

        """

        if self.config == None:
            self.retrive_config()


        if self.device_type == "cisco_nxos":
            keyword = "vrf context "
        else:
            keyword = "vrf definition "

        vrfs = []

        for line in self.line_config:
            if keyword in line:
                vrf = {
                    "name": line.replace(keyword, ""),
                }
                vrfs.append(vrf)

        self.vrfs = vrfs


    def retrieve_lldp_neighbors(self):
        """ pulls lldp neighbor information using cli based on self.device_type and
        loads them as a list of dictionaries into self.lldp_neighbors

        """

        neighbors = []

        if self.device_type == "arista_eos":
            if self.slow_connection:
                cli_json = self.cli.send_command("show lldp neighbors | json",delay_factor=5, max_loops=15000)
            else:
                cli_json = self.cli.send_command("show lldp neighbors | json")

            if "json: command not found" in cli_json:
                self.lldp_neighbors = neighbors
                return
            else:
                data = json.loads(cli_json)

            for d in data['lldpNeighbors']:
                neighbor= {
                    'neighbor_device': d['neighborDevice'],
                    'neighbor_port': d['neighborPort'],
                    'local_port': d['port'],
                }
                neighbors.append(neighbor)

        elif self.device_type == "cisco_ios":

            raw_output = self.cli.send_command("show lldp neighbors detail")
            raw_lines = raw_output.split("\n")

            lines = []
            for rl in raw_lines:
                if rl != "":
                    lines.append(rl)

            for index, line in enumerate(lines):

                if line == "------------------------------------------------":
                    neighbor = {
                        "local_port":""
                    }
                    config_index = index + 1
                    config_line = lines[config_index]
                    while config_line != "------------------------------------------------":
                        if 'Local Intf: ' in config_line:
                            neighbor['local_port'] = config_line.replace("Local Intf: ", "").replace(" ", "")
                        if 'Port id: ' in config_line:
                            neighbor['neighbor_port'] = config_line.replace("Port id: ", "").replace(" ", "")
                        if 'System Name: ' in config_line:
                            neighbor['neighbor_device'] = config_line.replace("System Name: ", "").replace(" ", "")

                        try:
                            config_index += 1
                            config_line = lines[config_index]
                        except:
                            break
                    neighbors.append(neighbor)

        self.lldp_neighbors = neighbors


    def retrieve_equipment(self):
        """ pulls inventory information using cli based on self.device_type and
        loads them as a list of dictionaries into self.equipment

        """
        equipment = []

        if self.device_type == "cisco_ios" or self.device_type == "cisco_nxos":

            if self.slow_connection:
                raw_output = self.cli.send_command("show inventory",delay_factor=5, max_loops=15000)
            else:
                raw_output = self.cli.send_command("show inventory")

            lines = raw_output.split("\n")

            for index, l in enumerate(lines):
                if "NAME" in l:
                    line1 = " " + lines[index] + " "
                    line2 = " " + lines[index + 1] + " "
                    item = {}
                    try:
                        item['name'] = re.findall(r'NAME: "(.+?)"', line1)[0]
                    except IndexError:
                        pass

                    try:
                        item['description'] = re.findall(r'DESCR: "(.+?)"', line1)[0]
                    except IndexError:
                        pass

                    try:
                        item['pid'] = re.findall(r"PID: (.+?)\s", line2)[0]
                    except:
                        pass

                    try:
                        item['sn'] = re.findall(r"SN: (.+?)\s", line2)[0]
                    except:
                        pass

                    equipment.append(item)

        elif self.device_type == "arista_eos":

            if self.slow_connection:
                output = self.cli.send_command("show inventory | json")
            else:
                output = self.cli.send_command("show inventory | json",delay_factor=5, max_loops=15000)


            if "json: command not found" in output:
                self.equipment = equipment
                return
            else:
                json_output = json.loads(output)

            item = {
                "name":json_output['systemInformation']['name'],
                'description':json_output['systemInformation']['description'],
                'sn':json_output['systemInformation']['serialNum'],
                "pid": json_output['systemInformation']['name']
            }

            equipment.append(item)

            #Interfaces (SFPs, QSFPs, ect)
            for key in json_output['xcvrSlots'].keys():

                if json_output['xcvrSlots'][key]['serialNum'] == "":
                    pass
                else:

                    item = {
                        "name": key,
                        'description': json_output['xcvrSlots'][key]['modelName'],
                        'sn': json_output['xcvrSlots'][key]['serialNum'],
                        "pid": json_output['xcvrSlots'][key]['modelName']
                    }

                    equipment.append(item)

        self.equipment = equipment


    def retrieve_routes_connected(self):

        entries = []

        if self.vrfs == None:
            self.parse_vrfs()

        #cisco ios regex route mappings
        # 0 - subnet
        # 1 - egress interface
        cisco_ios_regex = r"C\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}) is directly connected, (.*)\n"

        #arista eos regex route mappings
        # 0 - subnet
        # 1 - egress interface
        arista_eos_regex = r"C\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}) is directly connected, (.*)\n"

        # cisco nxos regex route mappings
        # 0 - subnet
        # 1 - next hop
        # 2 - egress interface
        # 3 - admin distance
        # 4 - metric
        cisco_nxos_regex = r"\n(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}).*\n\s*\*via (\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}), (.*), \[(\d*)/(\d*)\],"

        for vrf in self.vrfs:

            #if the device_type = cisco_ios
            if self.device_type == "cisco_ios":
                #use the cisco_ios_regex variable to parse the output
                raw_output = self.cli.send_command_timing(f"show ip route vrf {vrf['name']} connected")
                routes = re.findall(cisco_ios_regex, raw_output)

            # if the device_type = arista_eos
            elif self.device_type == "arista_eos":
                # use the cisco_ios_regex variable to parse the output
                raw_output = self.cli.send_command_timing(f"show ip route vrf {vrf['name']} connected")
                routes = re.findall(arista_eos_regex, raw_output)

            # if the device_type = cisco_nxos
            elif self.device_type == "cisco_nxos":
                # use the cisco_nxos_regex variable to parse the output
                raw_output = self.cli.send_command_timing(f"show ip route vrf {vrf['name']} direct")
                routes = re.findall(cisco_nxos_regex, raw_output)

            else:
                routes = []

            for i, rt in enumerate(routes):

                entry = {}

                # if the device_type = cisco_ios
                if self.device_type == "cisco_ios":

                    entry['subnet'] = rt[0]
                    entry['adminDistance'] = "0"
                    entry['metric'] = "0"
                    entry['nextHop'] = "self"
                    entry['egressInterface'] = rt[1]
                    entry['vrf'] = vrf['name']

                    entries.append(entry)

                # if the device_type = arista_eos
                elif self.device_type == "arista_eos":

                    entry['subnet'] = rt[0]
                    entry['adminDistance'] = "0"
                    entry['metric'] = "0"
                    entry['nextHop'] = "self"
                    entry['egressInterface'] = rt[1]
                    entry['vrf'] = vrf['name']

                    entries.append(entry)

                # if the device_type = cisco_nxos
                elif self.device_type == "cisco_nxos":

                    entry['subnet'] = rt[0]
                    entry['adminDistance'] = rt[3]
                    entry['metric'] = rt[4]
                    entry['nextHop'] = rt[1]
                    entry['egressInterface'] = rt[2]
                    entry['vrf'] = vrf['name']

                    entries.append(entry)

        self.connected_routes = entries


    def retrieve_routes_static(self):

        entries = []

        if self.vrfs == None:
            self.parse_vrfs()

        #cisco ios regex route mappings
        # 0 - subnet
        # 1 - admin distance
        # 2 - metric
        # 3 - next hop
        cisco_ios_regex = r"S\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}).*\[(\d*)/(\d*)\] via (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"

        #arista eos regex route mappings
        # 0 - subnet
        # 1 - admin distance
        # 2 - metric
        # 3 - next hop
        arista_eos_regex = r"S\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}).*\[(\d*)/(\d*)\] via (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"

        # cisco nxos regex route mappings
        # 0 - subnet
        # 1 - next hop
        # 2 - admin distance
        # 3 - metric
        cisco_nxos_regex = r"\n(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}).*\n\s*\*via (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}), \[(\d*)/(\d*)\]"

        for vrf in self.vrfs:

            #if the device_type = cisco_ios
            if self.device_type == "cisco_ios":
                #use the cisco_ios_regex variable to parse the output
                raw_output = self.cli.send_command_timing(f"show ip route vrf {vrf['name']} static")
                routes = re.findall(cisco_ios_regex, raw_output)

            # if the device_type = arista_eos
            elif self.device_type == "arista_eos":
                # use the cisco_ios_regex variable to parse the output
                raw_output = self.cli.send_command_timing(f"show ip route vrf {vrf['name']} static")
                routes = re.findall(arista_eos_regex, raw_output)

            # if the device_type = cisco_nxos
            elif self.device_type == "cisco_nxos":
                # use the cisco_nxos_regex variable to parse the output
                raw_output = self.cli.send_command_timing(f"show ip route vrf {vrf['name']} static")
                routes = re.findall(cisco_nxos_regex, raw_output)

            else:
                routes = []

            for i, rt in enumerate(routes):

                entry = {}

                # if the device_type = cisco_ios
                if self.device_type == "cisco_ios":

                    entry['subnet'] = rt[0]
                    entry['adminDistance'] = rt[1]
                    entry['metric'] = rt[2]
                    entry['nextHop'] = rt[3]
                    entry['egressInterface'] = "unknown"
                    entry['vrf'] = vrf['name']

                    entries.append(entry)

                # if the device_type = arista_eos
                elif self.device_type == "arista_eos":

                    entry['subnet'] = rt[0]
                    entry['adminDistance'] = rt[1]
                    entry['metric'] = rt[2]
                    entry['nextHop'] = rt[3]
                    entry['egressInterface'] = "unknown"
                    entry['vrf'] = vrf['name']

                    entries.append(entry)

                # if the device_type = cisco_nxos
                elif self.device_type == "cisco_nxos":

                    # 0 - subnet
                    # 1 - next hop
                    # 2 - admin distance
                    # 3 - metric

                    entry['subnet'] = rt[0]
                    entry['adminDistance'] = rt[2]
                    entry['metric'] = rt[3]
                    entry['nextHop'] = rt[1]
                    entry['egressInterface'] = "unknown"
                    entry['vrf'] = vrf['name']

                    entries.append(entry)

        self.static_routes = entries


    def retrieve_routes_ospf(self):

        if self.vrfs:
            pass
        else:
            self.parse_vrfs()

        entries = []

        #cisco ios regex route mappings
        # 0 - protocol junk and the subnet (extra parsing required and sometimes totally blank due to load balancing)
        # 1 - admin distance
        # 2 - metric
        # 3 - next hop ip
        # 4 - age (unused)
        # 5 - egress interface
        cisco_ios_regex = r"(.+)\[(\d+)/(\d+)] via (.+), (.+), (.+)\n"

        # arista eos regex route mappings
        # 0 - first junk, so whitespace, protocol and extra protocol options
        # 1 - subnet destination route entry
        # 2 - admin distiance
        # 3 - metric
        # 4 - next hop ip
        # 5 - egress interface
        arista_eos_regex = r"(.*)\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}).*\[(\d*)/(\d*)\] via (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}), (.*)\n"


        #cisco nxos regex route mappings
        # 0 - subnet destination route entry
        # 1 - nex hop ip
        # 2 - egress interface
        # 3 - 110
        # 4 - metric
        cisco_nxos_regex = r"\n(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}).*\n\s*\*via (\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}), (.*), \[(\d*)/(\d*)\],"

        for vrf in self.vrfs:

            raw_output = self.cli.send_command_timing(f"show ip route vrf {vrf['name']} ospf")

            #if the device_type = cisco_ios
            if self.device_type == "cisco_ios":
                #use the cisco_ios_regex variable to parse the output
                routes = re.findall(cisco_ios_regex, raw_output)

            # if the device_type = arista_eos
            elif self.device_type == "arista_eos":
                # use the cisco_ios_regex variable to parse the output
                routes = re.findall(arista_eos_regex, raw_output)

            # if the device_type = cisco_nxos
            elif self.device_type == "cisco_nxos":
                # use the cisco_nxos_regex variable to parse the output
                routes = re.findall(cisco_nxos_regex, raw_output)

            else:
                routes = []

            for i, rt in enumerate(routes):

                entry = {}
                load_balancer = 0

                # if the device_type = cisco_ios
                if self.device_type == "cisco_ios":
                    #if the match is a primary route entry
                    if rt[0][0] == "O":

                        subnet = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}", rt[0])

                        if len(subnet) > 0:
                            subnet = subnet[0]
                        else:
                            subnet = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", rt[0])

                        load_balancer = 0

                    #if the match is a secondary (alternate route) entry
                    else:
                        load_balancer += 1
                        subnet = entries[i - load_balancer]['subnet']

                    entry['subnet'] = subnet
                    entry['adminDistance'] = rt[1]
                    entry['metric'] = rt[2]
                    entry['nextHop'] = rt[3]
                    entry['egressInterface'] = rt[5]
                    entry['vrf'] = vrf['name']

                    entries.append(entry)

                # if the device_type = arista_eos
                elif self.device_type == "arista_eos":

                    entry['subnet'] = rt[1]
                    entry['adminDistance'] = rt[2]
                    entry['metric'] = rt[3]
                    entry['nextHop'] = rt[4]
                    entry['egressInterface'] = rt[5]
                    entry['vrf'] = vrf['name']

                    entries.append(entry)

                # if the device_type = cisco_nxos
                elif self.device_type == "cisco_nxos":

                    entry['subnet'] = rt[0]
                    entry['adminDistance'] = rt[3]
                    entry['metric'] = rt[4]
                    entry['nextHop'] = rt[1]
                    entry['egressInterface'] = rt[2]
                    entry['vrf'] = vrf['name']

                    entries.append(entry)

        self.ospf_routes = entries


    def retrieve_protocols(self):

        self.protocols = {}

        if self.vrfs == None:
            self.parse_vrfs()

        #if device type is Cisco IOS
        if self.device_type == "cisco_ios":

            for vrf in self.vrfs:
                raw_output = self.cli.send_command_timing(f"routing-context vrf {vrf['name']}\nshow ip protocols")
                protocols = re.findall(r'Routing Protocol is \"(.*)\"\n', raw_output)
                for p in protocols:
                    if "ospf" in p:
                        raw_output = self.cli.send_command_timing(f"show ip {p}")
                        rid = re.findall(fr' Routing Process \"{p}\" with ID (.*)\n', raw_output)
                        if len(rid) == 0:
                            rid = None
                        else:
                            rid = rid[0]
                    else:
                        rid = [None]
                    if p in self.protocols:
                        self.protocols[p]['vrf'].append(vrf['name'])
                    else:
                        self.protocols[p] = {
                            "vrf":[vrf['name']],
                            "rid":rid
                        }

        #if device type is Arista EOS
        elif self.device_type == "arista_eos":
            raw_output = self.cli.send_command_timing(f"show ip ospf")
            ospf = re.findall(r'Routing Process \"(.*)\" with ID (.*) VRF (.*)\n', raw_output)
            for o in ospf:
                if o[0] in self.protocols:
                    self.protocols[o[0]]['vrf'].append(o[2])
                else:
                    self.protocols[o[0]] = {
                        "vrf": [o[2]],
                        "rid": o[1],
                    }


    def retrieve_protocols_detail(self):

        if self.protocols:
            pass
        else:
            self.retrieve_protocols()

        #if device type is Cisco IOS
        if self.device_type == "cisco_ios":
            for p in self.protocols:
                if "ospf" in p:
                    raw_output = self.cli.send_command(f"show ip {p} neighbor detail")
                    neighbors = re.findall(r"Neighbor (.*), interface address (.*)\n    In the area (.*) via interface (.*)\n    Neighbor priority is (.*), State is (.*), (.*) state changes\n", raw_output)
                    self.protocols[p]['neighbors'] = []
                    for ni in neighbors:
                        self.protocols[p]['neighbors'].append(
                            {
                                "neighborID": ni[0],
                                "neighborIntAddress": ni[1],
                                "areaID": ni[2],
                                "localInterface": ni[3],
                                "neighborPriority":ni[4],
                                "state":ni[5]
                            }
                        )

        # if device type is Arista EOS
        elif self.device_type == "arista_eos":
            for p in self.protocols:
                if "ospf" in p:
                    raw_output = self.cli.send_command(f"show ip {p} neighbor detail")
                    neighbors = re.findall(
                        r"Neighbor (.*), VRF (.*), interface address (.*)\n  In area (.*) interface (.*)\n  Neighbor priority is (.*), State is (.*),",
                        raw_output)
                    self.protocols[p]['neighbors'] = []
                    for ni in neighbors:
                        self.protocols[p]['neighbors'].append(
                            {
                                "neighborID": ni[0],
                                "neighborIntAddress": ni[2],
                                "areaID": ni[3],
                                "localInterface": ni[4],
                                "neighborPriority":ni[5],
                                "state":ni[6]
                            }
                        )


    def __str__(self):

        return f"Switch CLI connection to  {self.hostname} over ssh"


    def __repr__(self):

        return f"Switch CLI connection to  {self.hostname} over ssh"

class ConnectionFailure:
    """
    Switch CLI class for devices that caused a connection failure
    ...

    Attributes
    ----------
    ip: str
        ip of the device
    device_type: str
        device type
    hostname: str, optional
        hostname of the device
    line_config: list
        list of configuration strings
    config: None
        remains empty due to configuration failure
    interfaces: None
        remains empty due to configuration failure
    vlans: None
        remains empty due to configuration failure
    vrfs: None
        remains empty due to configuration failure
    lldp_neighbors: None
        remains empty due to configuration failure
    status: string
        defaults to the "failure_reason" variable
    Methods
    -------
    """
    def __init__(self, ip, device_type, failure_reason, hostname=None):
        """
        Parameters
        ----------
            ip: str
                ip of the device
            device_type: str
                device type (must be netmiko compatable)
            hostname: str
                hostname of the device (not manditory)
            failure_reason: str
                whatever the desired failure reason (typically pass an error into here)
        """

        if hostname:
            self.hostname = hostname
        else:
            self.hostname = ip

        self.ip = ip
        self.device_type = device_type
        self.status = failure_reason

        self.line_config = []

        self.config = None

        self.interfaces = None

        self.vlans = None

        self.vrfs = None

        self.lldp_neighbors = None

    def __str__(self):

        return f"Connection failure to {self.hostname}: {self.status}"

    def __repr__(self):

        return f"Connection failure to {self.hostname}: {self.status}"