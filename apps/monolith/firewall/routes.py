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

import json
import os
import threading
import time
from io import BytesIO

from flask import render_template, flash, redirect, url_for, send_file, request
from werkzeug.utils import secure_filename

import ctrl
from config import LoggerConfig
from ..firewall import app
from ..firewall.forms import GenerateAudit, ZoneLookup, PolicyTest, ExportCSV, Search, FWSearch
from common_models import ElasticIndex

logger = LoggerConfig.LOGGER

@app.route('/')
def index():

    return render_template('firewall/index.html', title='Firewall')

@app.route('/audits', methods=['GET', 'POST'])
def audits():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    csv_audits = ctrl.audits.get_audit_list("CSV")
    return render_template('firewall/audit/audits.html', title='Audits', csv_audits=csv_audits)

@app.route('/delete_audit/<audit_id>', methods=['GET', 'POST'])
def delete_audit(audit_id):
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    message = ctrl.audits.delete_aduit(audit_id)

    time.sleep(.5)
    flash(message)
    return redirect(url_for('audits'))

@app.route('/report/<id>')
def report(id="none"):
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    info = ctrl.audits.get_audit(id)

    if info["type"] == "CSV":
        return render_template('firewall/report/csv.html', title='Audits', id=id, info=info)
    elif info["type"] == "API":
        return render_template('firewall/report/api.html', title='Audits', id=id, info=info)

@app.route('/report_printer/<id>/<report_type>/<param>', methods=['GET', 'POST'])
def report_printer(id=None, report_type=None, param=None):
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = ExportCSV()
    print(id,report_type)
    if param == "None":
        rules = ctrl.audits.get_report(id, report_type)
    else:
        rules = ctrl.audits.get_report(id, report_type, param)


    if form.is_submitted():
        response_stream = BytesIO(ctrl.to_csv(rules).encode())
        return send_file(
            response_stream,
            mimetype="text/csv",
            attachment_filename=f"{id}_{report_type}_export.csv",
            as_attachment=True,
        )

    return render_template(f'firewall/report/{report_type}.html',
                           title=f'{id} - Report {report_type}',
                           form=form,
                           rules=rules,
                           id=id,
                           param=param)

@app.route('/generateaudit', methods=['GET', 'POST'])
def generateaudit():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    form = GenerateAudit()

    if form.validate_on_submit():

        filename = secure_filename(form.file.data.filename)
        form.file.data.save('uploads/' + filename)
        upload = 'uploads/' + filename

        threading.Thread(target=ctrl.audits.generate_csv_audit, args=(upload,)).start()

        flash("Report will be available soon")

        return redirect(url_for('audits'))

    return render_template('firewall/audit/generateaudit.html', title='Generate CSV', form=form )

@app.route('/zonelookup', methods=['GET', 'POST'])
def zonelookup():

    form = ZoneLookup()
    ip = form.ip.data

    if form.is_submitted():

        zones = ctrl.firewall.zone_lookup(ip=ip)

        return render_template('firewall/zoneresult.html', title='Zone Result', ip=ip, zone=zones )

    return render_template('firewall/zonelookup.html', title='Zone Lookup', form=form )

@app.route('/policytest', methods=['GET', 'POST'])
def policytest():

    form = PolicyTest()
    src_ip = form.src_ip.data
    dst_ip = form.dst_ip.data
    service = form.service.data

    if form.is_submitted():

        try:
            results = ctrl.firewall.firewall_policy_test(src_ip=src_ip, dst_ip=dst_ip, service=service)

            return render_template('firewall/policytest_result.html', title='Policy Test Result', results=results )

        except Exception as e:

            return render_template('errors/500.html', error=str(e)), 500

    return render_template('firewall/policytest.html', title='Policy Test', form=form )

@app.route('/fw_search', methods=['GET', 'POST'])
def fw_search():

    firewalls = []

    fws = ctrl.firewall.get_firewall_all()

    if fws:
        for fw in fws:
            firewalls.append(fw.name)

    return render_template('firewall/fw_search.html', title='Firewall Search', firewalls=firewalls)

@app.route('/fw_info', methods=['GET', 'POST'])
def fw_info():
    
    form = FWSearch()
    
    if request.args.get("firewall"):
        
        fw = ctrl.firewall.get_firewall(request.args.get("firewall").replace('"', ''))
        
        if fw:
        
            unordered_zones = {}
            with open(f"data/zones/{fw.name}_zones.json", "r") as file:
                for zone in json.loads(file.read()):
                    unordered_zones[zone['name']] = {}
                    
            for z in unordered_zones:
                if os.path.exists(f"data/zone_routes/{fw.name}_{z}.json"):
                    with open(f"data/zone_routes/{fw.name}_{z}.json", "r") as file:
                        unordered_zones[z]['routes'] = json.loads(file.read())
                else:
                    unordered_zones[z]['routes'] = []

            sort_list = []

            for z in unordered_zones:
                sort_list.append(z)

            ordered_zones = sorted(sort_list, key=ctrl.data.zero_pad_numbers)

            zones = {}

            for o in ordered_zones:
                zones[o] = unordered_zones[o]
                
        else:
            fw = None
            zones = []
            interfaces = []


        interfaces = {}
        with open(f"devices/{fw.name}_ifnets.json", "r") as file:
            for interface in json.loads(file.read()):
        
                name = interface['name']
                del interface['name']
                if interface['zone']:
                    interface['zone'] = interface['zone'].upper()
                interfaces[name] = interface
    
    else:
        fw = None
        zones = []
        interfaces = []

    if form.is_submitted():
    
        if request.form.get("export_routes"):
            zone_name = request.form.get("export_routes")
            response_stream = BytesIO(ctrl.to_csv(zones[zone_name]['routes']).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"{fw.name}_{zone}_routes.csv",
                as_attachment=True,
            )
        elif request.form.get("show_routes"):
            interface = str(request.form.get("show_routes"))
            routes = ctrl.firewall.route_lookup(fw_name=fw.name, iface=interface)

            return render_template('firewall/ifaceroutes.html', form=ExportCSV(), routes=routes, iface=interface, fw_name=fw.name)
        
        elif request.form.get("show_arp"):
            interface = str(request.form.get("show_arp"))
            arps = ctrl.firewall.arp_lookup(fw_name=fw.name, iface=interface)
            print(arps)
            return render_template('firewall/ifacearp.html', arps=arps, iface=interface, fw_name=fw.name)
        
        elif request.form.get("export_all_routes"):
            all_routes = []
            for zone in zones:
                for route in zones[zone]['routes']:
                    route['zone'] = zone
                    all_routes.append(route)
            response_stream = BytesIO(ctrl.to_csv(all_routes).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"{fw.name}_all_routes.csv",
                as_attachment=True,
            )
            
    return render_template('firewall/fw_info.html', title='Firewall Info', fw=fw, zones=zones, interfaces=interfaces, form=form)

@app.route('/policy', methods=['GET', 'POST'])
def policy():
    
    firewalls = []

    fws = ctrl.firewall.get_firewall_all()

    if fws:
        for fw in fws:
            firewalls.append(fw.name)

    return render_template('firewall/policy.html', title='Policy', firewalls=firewalls)

@app.route('/fw_policy/<firewall>', methods=['GET', 'POST'])
def fw_policy(firewall):
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    hits = ctrl.firewall.get_firewall_policies(firewall)

    return render_template('firewall/fw_policy.html', title=f'{firewall} Polcies', hits=hits, firewall=firewall, root_uri=request.url_root)

@app.route('/policy_search', methods=['GET', 'POST'])
def policy_search():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Policy Search", error=e)
    
    form = Search()

    if request.args.get("query"):
        query = request.args.get("query")

        index = ElasticIndex("fw-security-policies")

        elastic_hits = index.lquery(query, exact_match=False)

        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eq in elastic_hits['hits']['hits']:
                hits.append(eq['_source'])
        else:
            hits = None

    else:
        hits=None

    if form.is_submitted():

        if form.submit.data:

            query = form.searchbar.data
            return redirect(f"{request.url_root}policy_search?query={query}")

        if form.export.data:

            response_stream = BytesIO(ctrl.to_csv_differing_fields(hits).encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename="export.csv",
                as_attachment=True,
            )

    return render_template('firewall/policy_search.html', title='Policy Search', form=form, hits=hits,root_uri=request.url_root)


@app.route('/object_search', methods=['GET', 'POST'])
def object_search():
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Object Search", error=e)
    
    form = Search()
    
    if request.args.get("query"):
        query = request.args.get("query")
        
        index = ElasticIndex("fw-objects")
        
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
            return redirect(f"{request.url_root}object_search?query={query}")
    
    return render_template('firewall/object_search.html', title='Object Search', form=form, hits=hits)


@app.route('/object_info', methods=['GET', 'POST'])
def object_info():
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Switch Search", error=e)
    
    if request.args.get("object"):
        
        object = request.args.get("object")
        index = ElasticIndex("fw-objects")

        elastic_hits = index.query(object, field="name")
        
        info = []
        
        for h in elastic_hits['hits']['hits']:
            if h["_source"]['name'] == object.replace('"', ''):
                info.append(h['_source'])
                
        if len(info) == 0:
            info = None

    else:
        info = None

    return render_template('firewall/object_info.html', title='Object Info', objects=info, root_uri=request.url_root)

@app.route('/route_search', methods=['GET', 'POST'])
def route_search():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Route Search", error=e)
    
    form = Search()

    if request.args.get("query"):
        query = request.args.get("query")

        index = ElasticIndex("fw-routes")

        elastic_hits = index.lquery(query, exact_match=False)

        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for eq in elastic_hits['hits']['hits']:
                hits.append(eq['_source'])
        else:
            hits = None

    else:
        hits=None

    if form.is_submitted():

        if form.submit.data:

            query = form.searchbar.data
            return redirect(f"{request.url_root}route_search?query={query}")


    return render_template('firewall/route_search.html', title='Route Search', form=form, hits=hits)


@app.route('/blackhole_ip', methods=['GET', 'POST'])
def blackhole_ip():
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Blackholed IPs", error=e)

    index = ElasticIndex("blackholed_ips")
    
    if index.es.indices.exists("blackholed_ips") != True:
        return render_template('system_error.html', title="Blackholed IPs", error="The 'blackholed_ips' index does not seem to exist.  Please verify this functionality is enabled.")
    
    form = Search()
    
    if request.args.get("query"):
        query = request.args.get("query")
        

        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for q in elastic_hits['hits']['hits']:
                q['_source']['timestamp'] = q['_source']['@timestamp']
                del q['_source']['@timestamp']
                hits.append(q['_source'])
        else:
            hits = None
    
    else:
        hits = None
    
    if form.is_submitted():
        
        if form.submit.data:
            query = form.searchbar.data
            return redirect(f"{request.url_root}blackhole_ip?query={query}")
    
    return render_template('firewall/blackhole_ip.html', title='Blackholed IPs', form=form, hits=hits)


@app.route('/blackhole_domain', methods=['GET', 'POST'])
def blackhole_domain():
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return render_template('system_error.html', title="Blackholed Domains", error=e)
    
    index = ElasticIndex("blackholed_domains")
    
    if index.es.indices.exists("blackholed_domains") != True:
        return render_template('system_error.html', title="Blackholed Domains",
                               error="The 'blackholed_domains' index does not seem to exist.  Please verify this functionality is enabled.")
    
    form = Search()
    
    if request.args.get("query"):
        query = request.args.get("query")
        
        elastic_hits = index.lquery(query, exact_match=False)
        
        if len(elastic_hits['hits']['hits']) > 0:
            hits = []
            for q in elastic_hits['hits']['hits']:
                q['_source']['timestamp'] = q['_source']['@timestamp']
                del q['_source']['@timestamp']
                hits.append(q['_source'])
        else:
            hits = None
    
    else:
        hits = None
    
    if form.is_submitted():
        
        if form.submit.data:
            query = form.searchbar.data
            return redirect(f"{request.url_root}blackhole_domain?query={query}")
    
    return render_template('firewall/blackhole_domain.html', title='Blackholed Domains', form=form, hits=hits)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', error=error), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html', error=error), 500