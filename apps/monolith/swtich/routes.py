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

from io import BytesIO
import datetime
import threading
import re

from flask import render_template, send_file, request, redirect, flash
from apps.monolith.swtich.forms import SwitchSearch, SwitchInfo, InterfaceInfo, BulkCommands, LogSearch
from common_models import ElasticIndex
from config import LoggerConfig
import ctrl
from ..swtich import app

logger = LoggerConfig.LOGGER


@app.route('/')
def index():

    return render_template('switch/index.html', title='Switch')


@app.route('/logs', methods=['GET', 'POST'])
def logs():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Logs", error=e)

    form = LogSearch()

    if request.args.get("query"):
        query = request.args.get("query")
    
        index = ElasticIndex("switch_logs")
        
        if index.es.indices.exists("switch_logs"):
            elasticquery = index.query(query, field=None, exact_match=False, size=10000, sort_field="@timestamp", sort_order="desc")
            logs = []
            for q in elasticquery['hits']['hits']:
                q['_source']['timestamp'] = q['_source']['@timestamp']
                del q['_source']['@timestamp']
                logs.append(q['_source'])
                
        else:
            logs = None
            
    else:
        logs = None

    if form.is_submitted():
    
        if form.submit.data:
            
            query = form.searchbar.data
        
            return redirect(f"{request.url_root}logs?query={query}")
    
    return render_template('switch/logs.html', title="Switch Logs", form=form, logs=logs)


@app.route('/switch_info', methods=['GET', 'POST'])
def switch_info():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchInfo()
    
    if request.args.get("hostname"):
        
        hostname = request.args.get("hostname")
        
        index = ctrl.elk.ElasticIndex("sw-inventory")
        
        history = []
        
        #build the history list
        for i in range(0, 30):
            history_date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(i), '%Y-%m-%d')
            if index.es.indices.exists(f"{history_date}__sw-inventory"):
                history.append(history_date)
        
        info = ctrl.switch.get_switch_info(hostname)
        
        #if a button is pressed (submitted)
        if form.is_submitted():
    
            # if the interface "show" button is pressed
            if request.form.get("show_interface"):
                interface = request.form.get("show_interface")
                output = ctrl.switch.show_interface(info['info'], interface)
                return render_template('switch/output.html', title=f"Interface Status", data=output)

            # if the interface "show mac table" button is pressed
            elif request.form.get("show_int_mac_table"):
                interface = request.form.get("show_int_mac_table")
                output = ctrl.switch.show_interface_mac(info['info'], interface)
                if info['info']['device_type'] == "arista_eos" and type(output) == list:
                    return render_template('switch/cli_output/all_os/mac_table.html', title=f"{interface} MAC Table",
                                           macs=output, info=info['info'], interface=interface)
                elif info['info']['device_type'] == "cisco_ios" and type(output) == list:
                    return render_template('switch/cli_output/all_os/mac_table.html', title=f"{info['info']['hostname']} MAC Table",
                                           macs=output, info=info['info'], interface=interface)
                elif info['info']['device_type'] == "cisco_nxos" and type(output) == list:
                    return render_template('switch/cli_output/all_os/mac_table.html', title=f"{info['info']['hostname']} MAC Table",
                                           macs=output, info=info['info'], interface=interface)
                else:
                    return render_template('switch/output.html', title=f"{interface} MAC Table", data=output)

            # if the VLAN "show stp" button is pressed
            elif request.form.get("show_stp"):
                vlan_number = request.form.get("show_stp")
                output = ctrl.switch.show_vlan_stp(info['info'], vlan_number)
                return render_template('switch/output.html', title=f"VLAN STP", data=output)
            
            # if the VLAN "show mac table" button is pressed
            elif request.form.get("show_mac_table"):
                vlan_number = request.form.get("show_mac_table")
                output = ctrl.switch.show_vlan_mac(info['info'], vlan_number)
                if info['info']['device_type'] == "arista_eos" and type(output) == list:
                    return render_template('switch/cli_output/all_os/mac_table.html', title=f"{vlan_number} MAC Table",
                                           macs=output, info=info['info'], vlan_number=vlan_number)
                elif info['info']['device_type'] == "cisco_ios" and type(output) == list:
                    return render_template('switch/cli_output/all_os/mac_table.html', title=f"{info['info']['hostname']} MAC Table",
                                           macs=output, info=info['info'], vlan_number=vlan_number)
                elif info['info']['device_type'] == "cisco_nxos" and type(output) == list:
                    return render_template('switch/cli_output/all_os/mac_table.html', title=f"{info['info']['hostname']} MAC Table",
                                           macs=output, info=info['info'], vlan_number=vlan_number)
                else:
                    return render_template('switch/output.html', title=f"{vlan_number} MAC Table", data=output)

            # if the vrf "show route" button is pressed
            elif request.form.get("show_ip_vrf"):
                vlan_number = request.form.get("show_ip_vrf")
                output = ctrl.switch.show_ip_vrf(info['info'], vlan_number)
                return render_template('switch/output.html', title=f"VRF Route", data=output)

            # if the device 'show run' is pressed (unused)
            elif form.run_config.data:
                
                output = ctrl.switch.show_run_config(info['info'])
                return render_template('switch/output.html', title=f"Running Config", data=output)

            # if the device 'show int status' is pressed
            elif form.interfacestatus.data:
                
                output = ctrl.switch.show_int_status(info['info'])
                if info['info']['device_type'] == "arista_eos" and type(output) == dict:
                    return render_template('switch/cli_output/arista_eos_int_status.html', title=f"Interface Status",
                                           interfaces=output, info=info['info'])
                else:
                    return render_template('switch/output.html', title=f"Interface Status", data=output)

            # if the device 'show inventory' is pressed
            elif form.inventory.data:
                
                output = ctrl.switch.show_inventory(info['info'])
                return render_template('switch/output.html', title=f"Interface Status", data=output)

            # if the device 'show environment' is pressed
            elif form.show_environment.data:
    
                output = ctrl.switch.show_environment(info['info'])
                return render_template('switch/output.html', title=f"Environment", data=output)

            # if the device 'show version' is pressed
            elif form.version.data:
                
                output = ctrl.switch.show_version(info['info'])
                return render_template('switch/output.html', title=f"Interface Status", data=output)

            # if the history 'go' is pressed
            elif form.history_go.data:
    
                history_date = request.form.get("history_date")
                query = '"' + info['info']['hostname'] + '"'
                return redirect(f"{request.url_root}historical_switch_info?hostname={query}&date={history_date}")

            # if the compare 'go' is pressed
            elif form.compare.data:
    
                first_date = request.form.get("first_record")
                second_date = request.form.get("second_record")
                query = '"' + info['info']['hostname'] + '"'
                return redirect(
                    f"{request.url_root}diff_switch_info?hostname={query}&first_date={first_date}&second_date={second_date}")

            # if the compare 'refresh device' is pressed
            elif form.refresh_device.data:
    
                threading.Thread(target=ctrl.switch.refresh_device, args=(info['info']['hostname'], info['info']['ip'])).start()
                flash(f"Device {info['info']['hostname']} data will be refreshed shorty.")

            # if the compare 'refresh device' is pressed
            elif form.vrf_arp_table.data:
                vrf = request.form.get("arp_vrf")
                if vrf == "default":
                    arps = ctrl.switch.show_arp(info['info'])
                else:
                    arps = ctrl.switch.show_arp(info['info'], vrf)
                if type(arps) == list:
                    return render_template('switch/cli_output/all_os/arp_table.html', title=f"{vrf} ARP Table",
                                           arps=arps, info=info['info'], vrf=vrf)
                else:
                    return render_template('switch/output.html', title=f"{vrf} ARP Table", data=arps)

            # if the device 'vrf int report' is pressed
            elif form.vrf_interface_report.data:
                vrf = request.form.get("vrf")
                report = ctrl.switch.vrf_interface_report([info['info']], vrf)
                response_stream = BytesIO(report.encode())
                report_hostname = info['info']['hostname'].split(".")[0]
                return send_file(
                    response_stream,
                    mimetype="text/csv",
                    attachment_filename=f"{report_hostname}_{vrf}_interface_report.csv",
                    as_attachment=True,
                )

            # if the device 'VRF ARP table' is pressed
            elif form.show_mac_addr_table.data:
                
                output = ctrl.switch.show_mac(info['info'])
                if info['info']['device_type'] == "arista_eos" and type(output) == list:
                    return render_template('switch/cli_output/all_os/mac_table.html', title=f"{info['info']['hostname']} MAC Table",
                                           macs=output, info=info['info'])
                elif info['info']['device_type'] == "cisco_ios" and type(output) == list:
                    return render_template('switch/cli_output/all_os/mac_table.html', title=f"{info['info']['hostname']} MAC Table",
                                           macs=output, info=info['info'])
                elif info['info']['device_type'] == "cisco_nxos" and type(output) == list:
                    return render_template('switch/cli_output/all_os/mac_table.html', title=f"{info['info']['hostname']} MAC Table",
                                           macs=output, info=info['info'])
                else:
                    return render_template('switch/output.html', title=f"{info['info']['hostname']} MAC Table", data=output)
                
        switch_device_types = ['cisco_ios', 'cisco_nxos', 'arista_eos']
        
        if info == None:
            return render_template('switch/blank_info.html', title='Device Not Found', form=form, info=info, history=history)
        elif info['info']['device_type'] == 'linux' and "cs-" in info['info']['hostname'].lower():
            return render_template('switch/consoleserver_info.html', title='Console Server Info', form=form, info=info,
                                   history=history)
        elif info['info']['device_type'] in switch_device_types:
            return render_template('switch/switch_info.html', title='Switch Info', form=form, info=info, history=history)
        else:
            return render_template('switch/unknown_info.html', title='Device Info', form=form, info=info, history=history)


@app.route('/historical_switch_info', methods=['GET', 'POST'])
def historical_switch_info():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchInfo()
    
    if request.args.get("date"):
        date = request.args.get("date")
    else:
        date = datetime.datetime.today().strftime('%Y-%m-%d')
    
    if request.args.get("hostname"):
        hostname = request.args.get("hostname")
        
        info = ctrl.switch.get_switch_info(hostname, date)
        
        switch_device_types = ['cisco_ios', 'cisco_nxos', 'arista_eos']
        
        if info == None:
            return render_template('switch/blank_info.html', title='Historical Device Not Found', form=form, info=info,
                                   date=date)
        elif info['info']['device_type'] == 'linux' and "cs-" in info['info']['hostname'].lower():
            return render_template('switch/historical_consoleserver_info.html', title='Historical Console Server Info',
                                   form=form, info=info, date=date)
        elif info['info']['device_type'] in switch_device_types:
            return render_template('switch/historical_switch_info.html', title='Historical Switch Info', form=form,
                                   info=info, date=date)
        else:
            return render_template('switch/historical_unknown_info.html', title='Historical Device Info', form=form, info=info,
                                   date=date)


@app.route('/diff_switch_info', methods=['GET', 'POST'])
def diff_switch_info():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchInfo()
    
    if request.args.get("first_date"):
        first_date = request.args.get("first_date")
    
    if request.args.get("second_date"):
        second_date = request.args.get("second_date")
    
    if request.args.get("hostname"):
        hostname = request.args.get("hostname")
        
        index = ctrl.elk.ElasticIndex(f"sw-inventory")
        
        elastic_hits = index.query(hostname, field="hostname")
        
        if len(elastic_hits['hits']['hits']) > 0:
            device = []
            for eq in elastic_hits['hits']['hits']:
                device.append(eq['_source'])
            
            if device[0]['device_type'] != "unkown":
                device_type = device[0]['device_type']
            else:
                device_type = None
            
            ss_name = device[0]['hostname'].split(".")[0].upper()
        
        else:
            device = None
        
        index = ctrl.elk.ElasticIndex(f"{first_date}__interfaces")
        
        if index.es.indices.exists(f"{first_date}__interfaces"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                first_interfaces = []
                for eq in elastic_hits['hits']['hits']:
                    first_interfaces.append(eq['_source'])
            else:
                first_interfaces = []
        
        else:
            first_interfaces = []
        
        index = ctrl.elk.ElasticIndex(f"{second_date}__interfaces")
        
        if index.es.indices.exists(f"{second_date}__interfaces"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                second_interfaces = []
                for eq in elastic_hits['hits']['hits']:
                    second_interfaces.append(eq['_source'])
            else:
                second_interfaces = []
        
        else:
            second_interfaces = []
        
        interfaces = ctrl.switch.diff(first_interfaces, second_interfaces, diff_key="name")
        if len(interfaces) == 0:
            interfaces = None
        
        index = ctrl.elk.ElasticIndex(f"{first_date}__vlans")
        
        if index.es.indices.exists(f"{first_date}__vlans"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                first_vlans = []
                for eq in elastic_hits['hits']['hits']:
                    first_vlans.append(eq['_source'])
            else:
                first_vlans = []
        
        else:
            first_vlans = []
        
        index = ctrl.elk.ElasticIndex(f"{second_date}__vlans")
        
        if index.es.indices.exists(f"{second_date}__vlans"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                second_vlans = []
                for eq in elastic_hits['hits']['hits']:
                    second_vlans.append(eq['_source'])
            else:
                second_vlans = []
        
        else:
            second_vlans = []
        
        vlans = ctrl.switch.diff(first_vlans, second_vlans, diff_key="number")
        if len(vlans) == 0:
            vlans = None
        
        index = ctrl.elk.ElasticIndex(f"{first_date}__neighbors")
        
        if index.es.indices.exists(f"{first_date}__neighbors"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                first_neighbors = []
                for eq in elastic_hits['hits']['hits']:
                    first_neighbors.append(eq['_source'])
            else:
                first_neighbors = []
        
        else:
            first_neighbors = []
        
        index = ctrl.elk.ElasticIndex(f"{second_date}__neighbors")
        
        if index.es.indices.exists(f"{second_date}__neighbors"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                second_neighbors = []
                for eq in elastic_hits['hits']['hits']:
                    second_neighbors.append(eq['_source'])
            else:
                second_neighbors = []
        
        else:
            second_neighbors = []
        
        neighbors = ctrl.switch.diff(first_neighbors, second_neighbors, diff_key="local_port")
        if len(neighbors) == 0:
            neighbors = None
        
        index = ctrl.elk.ElasticIndex(f"{first_date}__vrfs")
        
        if index.es.indices.exists(f"{first_date}__vrfs"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                first_vrfs = []
                for eq in elastic_hits['hits']['hits']:
                    first_vrfs.append(eq['_source'])
            else:
                first_vrfs = []
        
        else:
            first_vrfs = []
        
        index = ctrl.elk.ElasticIndex(f"{second_date}__vrfs")
        
        if index.es.indices.exists(f"{second_date}__vrfs"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                second_vrfs = []
                for eq in elastic_hits['hits']['hits']:
                    second_vrfs.append(eq['_source'])
            else:
                second_vrfs = []
        
        else:
            second_vrfs = []
        
        vrfs = ctrl.switch.diff(first_vrfs, second_vrfs, diff_key="name")
        if len(vrfs) == 0:
            vrfs = None
        
        index = ctrl.elk.ElasticIndex(f"{first_date}__equipment")
        
        if index.es.indices.exists(f"{first_date}__equipment"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                first_equipment = []
                for eq in elastic_hits['hits']['hits']:
                    first_equipment.append(eq['_source'])
            else:
                first_equipment = []
        
        else:
            first_equipment = []
        
        index = ctrl.elk.ElasticIndex(f"{second_date}__equipment")
        
        if index.es.indices.exists(f"{second_date}__equipment"):
            
            elastic_hits = index.query(hostname, field="hostname")
            
            if len(elastic_hits['hits']['hits']) > 0:
                second_equipment = []
                for eq in elastic_hits['hits']['hits']:
                    second_equipment.append(eq['_source'])
            else:
                second_equipment = []
        
        else:
            second_equipment = []
        
        equipment = ctrl.switch.diff(first_equipment, second_equipment, diff_key="name")
        if len(equipment) == 0:
            equipment = None
    
    else:
        device = None
        interfaces = None
        vlans = None
        neighbors = None
        vrfs = None
        equipment = None
    
    return render_template('switch/diff_switch_info.html', title='Compare Switch Info', first_date=first_date,
                           second_date=second_date, form=form, device=device, interfaces=interfaces,
                           vlans=vlans, neighbors=neighbors, vrfs=vrfs, equipment=equipment)


@app.route('/switch_search', methods=['GET', 'POST'])
def switch_search():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchSearch()
    
    if request.args.get("query"):
        query = request.args.get("query")
        
        index = ctrl.elk.ElasticIndex("sw-inventory")
        
        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eq in elastic_hits['hits']['hits']:
                hits.append(eq['_source'])
        else:
            hits = None
    
    else:
        hits = None
    
    if form.is_submitted():
        
        if form.submit.data:
            
            query = form.searchbar.data
            
            return redirect(f"{request.url_root}switch_search?query={query}")
        
        elif form.ansible.data:
            
            ans_inv = ctrl.switch.asnible_inventory(hits)
            return render_template('switch/output.html', title=f"Ansible Inventory", data=ans_inv)
        
        elif form.selected.data:
            
            query = []
            
            for device in hits:
                if f"{device['hostname']}_include" in request.form:
                    hostname = device['hostname']
                    query.append(f'"{hostname}"')
                    
            if len(query) > 0:
                
                query  = " OR ".join(query)
                
                return redirect(f"{request.url_root}bulk_commands?query={query}")
            #return render_template('switch/output.html', title="Selection Tester", data=output)
        
        elif form.export.data:
            
            response_stream = BytesIO(ctrl.to_csv(hits).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename="export.csv",
                as_attachment=True,
            )
    
    return render_template('switch/switch_search.html', title='Switch Search', form=form, hits=hits, root_uri=request.url_root.replace("fw_policy/",""))


@app.route('/bulk_commands', methods=['GET', 'POST'])
def bulk_commands():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = BulkCommands()
    
    if request.args.get("query"):
        query = request.args.get("query")
        
        index = ctrl.elk.ElasticIndex("sw-inventory")
        
        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            omitted = []
            for eq in elastic_hits['hits']['hits']:
                if eq['_source']['device_type'] == "cisco_ios" or eq['_source']['device_type'] == "arista_eos" or eq['_source']['device_type'] == "cisco_nxos":
                    hits.append(eq['_source'])
                else:
                    omitted.append(eq['_source'])
                    
            if len(omitted) == 0:
                omitted = None
        else:
            hits = None
            omitted = None
    
    else:
        hits = None
        omitted = None
    
    if hits:
        vrfs = set()
        for h in hits:
            device = ctrl.switch.get_switch_info(h['hostname'])
            if 'vrfs' in device:
                for v in device['vrfs']:
                    vrfs.add(v)
    else:
        vrfs = None
    
    if form.is_submitted():
        
        if form.show_mac_addr_table.data:
            all_macs = ctrl.switch.bulk_show_mac_table(hits)
            return render_template('switch/bulk_output/bulk_mac_table.html',
                                   title=f"Bulk MAC Addresses",
                                   macs=all_macs)
        
        elif form.vrf_interface_report.data:
            vrf = request.form.get("vrf")
            report = ctrl.switch.vrf_interface_report(hits, vrf)
            response_stream = BytesIO(report.encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"{vrf}_interface_report.csv",
                as_attachment=True,
            )
    
    return render_template('switch/bulk_commands.html', title='Bulk Commands', form=form, hits=hits,omitted=omitted, vrfs = vrfs)


@app.route('/historical_switch_search', methods=['GET', 'POST'])
def historical_switch_search():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchSearch()
    
    index = ctrl.elk.ElasticIndex("sw-inventory")
    
    history = []
    
    for i in range(1, 30):
        history_date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(i), '%Y-%m-%d')
        if index.es.indices.exists(f"{history_date}__sw-inventory"):
            history.append(history_date)
    
    if request.args.get("query"):
        
        query = request.args.get("query")
        hits = []
        for h in history:
            
            index = ctrl.elk.ElasticIndex(f"{h}__sw-inventory")
            
            elastic_hits = index.lquery(query, exact_match=False)
            
            for eq in elastic_hits['hits']['hits']:
                hit = eq['_source']
                hit['date'] = h
                hits.append(hit)
        
        if len(hits) == 0:
            hits = None
    
    else:
        hits = None
    
    if form.is_submitted():
        
        if form.submit.data:
            
            query = form.searchbar.data
            
            return redirect(f"{request.url_root}historical_switch_search?query={query}")
        
        elif form.ansible.data:
            
            ans_inv = ctrl.switch.asnible_inventory(hits)
            return render_template('switch/output.html', title=f"Ansible Inventory", data=ans_inv)
        
        elif form.export.data:
            
            response_stream = BytesIO(ctrl.to_csv(hits).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename="export.csv",
                as_attachment=True,
            )
    
    return render_template('switch/historical_switch_search.html', title='Historical Switch Search', form=form, hits=hits,
                           root_uri=request.url_root)


@app.route('/interface_search', methods=['GET', 'POST'])
def interface_search():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchSearch()
    
    if request.args.get("query"):
        query = request.args.get("query")
        
        index = ctrl.elk.ElasticIndex("interfaces")
        
        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eq in elastic_hits['hits']['hits']:
                hits.append(eq['_source'])
        else:
            hits = None
    else:
        hits = None
    
    if request.args.get("include_config") == "yes":
        include_config = "yes"
    else:
        include_config = None
    
    if form.is_submitted():
        
        if request.form.get("show"):
            
            hostname, interface = request.form.get("show").split("!SEPARATOR!")
            index = ctrl.elk.ElasticIndex("sw-inventory")
            query = index.query(hostname, field="hostname")
            
            device = query['hits']['hits'][0]
            
            output = ctrl.switch.show_interface(device, interface)
            return render_template('switch/output.html', title=f"Interface Status", data=output)
        
        elif form.submit.data:
            
            query = form.searchbar.data
            
            if request.form.get('includeconfig'):
                return redirect(f"{request.url_root}interface_search?query={query}&include_config=yes")
            
            return redirect(f"{request.url_root}interface_search?query={query}")
        
        elif form.export.data:
            
            response_stream = BytesIO(ctrl.to_csv_differing_fields(hits).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"{query}export.csv",
                as_attachment=True,
            )
    
    return render_template('switch/interface_search.html', title='Interface Search', form=form, hits=hits,
                           include_config=include_config)

@app.route('/interface_info', methods=['GET', 'POST'])
def interface_info():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchInfo()
    
    if request.args.get("hostname") and request.args.get("interface"):
        
        hostname = request.args.get("hostname")
        
        interface_name = request.args.get("interface")
        
        info = ctrl.switch.get_int_info(hostname, interface_name)
        
        if form.is_submitted():
            
            if form.gatherinfo.data:
                
                output = ctrl.switch.show_inventory(info['device'])
                return render_template('switch/output.html', title=f"Device Inventory", data=output)
        
        switch_device_types = ['cisco_ios', 'cisco_nxos', 'arista_eos']
        
        if info == None:
            return render_template('switch/blank_info.html', title='Device/Interface Not Found', form=form, info=info)
        elif info['info']['device']['device_type'] in switch_device_types:
            return render_template('switch/switch_info.html', title='Switch Info', form=form, info=info)
        else:
            return render_template('switch/unknown_info.html', title='Device Info', form=form, info=info)

        
@app.route('/vlan_search', methods=['GET', 'POST'])
def vlan_search():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchSearch()
    if request.args.get("query"):
        query = request.args.get("query")
        
        index = ctrl.elk.ElasticIndex("vlans")
        
        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eq in elastic_hits['hits']['hits']:
                hits.append(eq['_source'])
        else:
            hits = None
    else:
        hits = None
    
    if form.is_submitted():
        
        if form.submit.data:
            query = form.searchbar.data
            
            return redirect(f"{request.url_root}vlan_search?query={query}")
        
        if form.export.data:
            response_stream = BytesIO(ctrl.to_csv_differing_fields(hits).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"{query}export.csv",
                as_attachment=True,
            )
    
    return render_template('switch/vlan_search.html', title='Vlan Search', form=form, hits=hits)


@app.route('/vlan_info', methods=['GET', 'POST'])
def vlan_info():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    if request.args.get("vlan"):
        vlan_number = request.args.get("vlan")
        print(vlan_number)
        index = ctrl.elk.ElasticIndex("vlans")
        
        elastic_hits = index.query(vlan_number, field="number")
        
        if len(elastic_hits['hits']['hits']) > 0:
            vlans = []
            for eq in elastic_hits['hits']['hits']:
                vlans.append(eq['_source'])
            
            unames = set()
            for vlan in vlans:
                unames.add(vlan['name'])
            
            vlan_index = ctrl.elk.ElasticIndex("interfaces")
            elastic_hits = vlan_index.query(f"Vlan{vlan_number}", field="name")
            if len(elastic_hits['hits']['hits']) > 0:
                svis = []
                for eq in elastic_hits['hits']['hits']:
                    svis.append(eq['_source'])
            else:
                svis = None
        
        else:
            vlans = None
            unames = None
            svis = None
    
    else:
        vlans = None
        unames = None
        vlan_number = None
        svis = None
    return render_template('switch/vlan_info.html', title='Switch Info', vlans=vlans,
                           unames=unames, vlan_number=vlan_number, svis=svis)


@app.route('/vrf_search', methods=['GET', 'POST'])
def vrf_search():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchSearch()
    if request.args.get("query"):
        query = request.args.get("query")
        
        index = ctrl.elk.ElasticIndex("vrfs")
        
        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eq in elastic_hits['hits']['hits']:
                hits.append(eq['_source'])
        else:
            hits = None
    else:
        hits = None
    
    if form.is_submitted():
        
        if form.submit.data:
            query = form.searchbar.data
            
            return redirect(f"{request.url_root}vrf_search?query={query}")
        
        if form.export.data:
            response_stream = BytesIO(ctrl.to_csv_differing_fields(hits).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"{query}export.csv",
                as_attachment=True,
            )
    
    return render_template('switch/vrf_search.html', title='VRF Search', form=form, hits=hits)


@app.route('/equipment_search', methods=['GET', 'POST'])
def equipment_search():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchSearch()
    if request.args.get("query"):
        query = request.args.get("query")
        
        index = ctrl.elk.ElasticIndex("equipment")
        
        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eq in elastic_hits['hits']['hits']:
                hits.append(eq['_source'])
        else:
            hits = None
    else:
        hits = None
    
    if form.is_submitted():
        
        if form.submit.data:
            query = form.searchbar.data
            
            return redirect(f"{request.url_root}equipment_search?query={query}")
        
        if form.export.data:
            response_stream = BytesIO(ctrl.to_csv_differing_fields(hits).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"{query}export.csv",
                as_attachment=True,
            )
    
    return render_template('switch/equipment_search.html', title='Equipment Search', form=form, hits=hits)


@app.route('/neighbor_search', methods=['GET', 'POST'])
def neighbor_search():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = SwitchSearch()
    if request.args.get("query"):
        query = request.args.get("query")
        
        index = ctrl.elk.ElasticIndex("neighbors")
        
        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eq in elastic_hits['hits']['hits']:
                hits.append(eq['_source'])
        else:
            hits = None
    else:
        hits = None
    
    if form.is_submitted():
        
        if form.submit.data:
            query = form.searchbar.data
            
            return redirect(f"{request.url_root}neighbor_search?query={query}")
        
        if form.export.data:
            response_stream = BytesIO(ctrl.to_csv_differing_fields(hits).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"{query}export.csv",
                as_attachment=True,
            )
    
    return render_template('switch/neighbor_search.html', title='Neighbor Search', form=form, hits=hits)


@app.route('/route_search', methods=['GET', 'POST'])
def route_search():
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Route Search", error=e)
    
    form = SwitchSearch()
    
    if request.args.get("query"):
        query = request.args.get("query")
        
        index = ElasticIndex("sw-routes")
        
        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eq in elastic_hits['hits']['hits']:
                hits.append(eq['_source'])
        else:
            hits = None
    
    else:
        hits = None
    
    if form.is_submitted():
        
        if form.submit.data:
            query = form.searchbar.data
            return redirect(f"{request.url_root}route_search?query={query}")
    
    return render_template('switch/route_search.html', title='Switch Route Search', form=form, routes=hits, root_uri=request.url_root)


@app.route('/route_info', methods=['GET', 'POST'])
def route_info():
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Route Search", error=e)
    
    form = SwitchSearch()
    
    if request.args.get("subnet"):
        
        subnet = request.args.get("subnet")
        
        index = ElasticIndex("sw-routes")
        
        hits = []
        for eq in index.query(subnet, field="subnet")['hits']['hits']:
            hits.append(eq['_source'])
            
        info = {
            'subnet': subnet.replace('"',''),
            'found':[],
            'location':[],
            'fw_zones': []
        }
        
        for h in hits:
            info['found'].append(h)
            
            if h['protocol'] == "connected":
                info['location'].append(h)
        
        #nh_url = '<a href={0}switch_info?hostname="{1}">{2}</a>'
        
        interface_index = ElasticIndex("interfaces")
        for i,f in enumerate(info['found']):
            info['found'][i]['nextHopFound'] = "no"
            if f['protocol'] == "connected":
                pass
            else:
                ip = f['nextHop']
                for q in interface_index.lquery(ip,exact_match=True)['hits']['hits']:
                    hostname = q['_source']['hostname']
                    if not re.match("\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}",hostname):
                        info['found'][i]['nextHopFound'] = "yes"
                        info['found'][i]['nextHop'] = hostname
                        break
                
    
        index = ElasticIndex("fw-routes")
        
        for eq in index.query(subnet, field="destination")['hits']['hits']:
            info['fw_zones'].append(eq['_source'])
            
    else:
        info = None
    
    return render_template('switch/route_info.html', title='Switch Route Info', form=form, info=info,
                           root_uri=request.url_root)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', error=error), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html', error=error), 500