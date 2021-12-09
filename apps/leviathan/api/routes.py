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

from flask import jsonify, request, abort
import json

from apps.monolith.api import app
from config import LoggerConfig
from .errors import InvalidUsage, RouteFileNotFound, DeviceNotFound
from common_models import ElasticIndex
import ctrl
logger = LoggerConfig.LOGGER

@app.route('/')
@app.route('/index')
def index():

    return 'Monolith API'

@app.route('/gp_gw')
def gp_gw():

    gateways = ctrl.vpn.get_gateways()

    if request.args.get("format") == "csv":

        return ctrl.to_csv(gateways)

    return jsonify(gateways)

@app.route('/gp_gw_users')
def gp_gw_users():

    if request.args.get("gateway"):
        gw = request.args.get("gateway")
    else:
        raise InvalidUsage(message="missing 'gateway' parameter")

    try:
        users = ctrl.vpn.get_gateway_users(gw)
    except:
        raise InvalidUsage(message=f"Could not find gateway {gw}")

    if not users:
        return f"No users found for gateway {gw}"

    if request.args.get("format") == "csv":
        return ctrl.to_csv(users)
    elif request.args.get("format") == "csv-noheaders":
        return ctrl.to_csv(users, include_headers=False)

    return jsonify(users)

@app.route('/firewall_zones')
def firewall_zones():

    if request.args.get("firewall"):
        firewall = request.args.get("firewall")
    else:
        raise InvalidUsage(message="missing 'firewall' parameter")

    try:
        with open(f"data/zones/{firewall}_zones.json", "r") as file:
            zones = json.loads(file.read())
    except FileNotFoundError:
        raise RouteFileNotFound(message=f"No zone file found for firewall:{firewall}")

    if request.args.get("format") == "csv":
        return ctrl.to_csv(zones)

    return jsonify(zones)

@app.route('/firewall_list')
def firewall_list():

    firewalls = []

    for fw in ctrl.firewall.get_firewall_all():
        firewalls.append({
            "name":fw.name
        })

    return jsonify(firewalls)

@app.route('/zone_routes')
def zone_routes():

    if request.args.get("firewall"):
        firewall = request.args.get("firewall")
    else:
        raise InvalidUsage(message="missing 'firewall' parameter")

    if request.args.get("zone"):
        zone = request.args.get("zone")
    else:
        raise InvalidUsage(message="missing 'zone' parameter")

    try:
        with open(f"data/zone_routes/{firewall.upper()}_{zone.upper()}.json", "r") as file:
            routes = json.loads(file.read())
    except FileNotFoundError:
        raise RouteFileNotFound(message=f"No route file found for zone:{zone} on firewall:{firewall}")

    if format:
        if request.args.get("format") == "csv":
            return ctrl.to_csv(routes)
        elif request.args.get("format") == "csv-noheaders":
            return ctrl.to_csv(routes, include_headers=False)

    return jsonify(routes)

@app.route('/search_inventory')
def search_inventory():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
                "error_code": 500,
                "data": {}
            }
        )

    index = ElasticIndex("sw-inventory")

    if index.es.indices.exists("sw-inventory") != True:
        return jsonify(
            {
                "success": False,
                "message": "The 'sw-inventory' index does not seem to exist.  Please verify this functionality is enabled.",
                "error_code": 500,
                "data": {}
            }
        )
    
    if request.args.get("query"):
        
        query = request.args.get("query")

        index = ElasticIndex("sw-inventory")
        
        try:
            elastic_hits = index.lquery(query, exact_match=False)
        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "error_code": 500,
                    "message": f"Query {query} caused an issue.  Please verify lucene syntax is correct",
                    "data": {}
                }
            )
        
        hits = []
        for eq in elastic_hits['hits']['hits']:
            hits.append(eq['_source'])
    else:
        hits = []

    return jsonify(
        {
            "success": True,
            "message": f"Query successfull.  {len(hits)} results found.",
            "data": hits
        }
    )

@app.route('/switch_info', methods=['GET', 'POST'])
def switch_info():

    # will raise error and except with 500 api return
    ctrl.system.check_elastic_connection()

    index = ElasticIndex("sw-inventory")

    if index.es.indices.exists("sw-inventory") != True:
        # raise exception with indication that the device inventory is missing
        raise Exception("no device inventory found.")

    if request.args.get("hostname"):
        hostname = request.args.get("hostname")
    else:
        raise InvalidUsage("hostname parameter missing", status_code=410)

    try:
        info = ctrl.switch.get_switch_info(hostname)

    # except any error during the query
    except Exception as e:
        raise Exception(str(e))

    if info:
    
        # generate the data
        data = ctrl.switch.show_mac(info['info'])
    
        # create the response
        response = {
            "success": True,
            "message": f"found device {info['info']['hostname']}",
            "data": info
        }
    
        return jsonify(response)

    else:
        raise DeviceNotFound(hostname)
    
@app.route('/blackhole_ip', methods=['GET', 'POST'])
def blackhole_ip():
    
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
                "error_code": 500,
                "data": {}
            }
        )

    index = ElasticIndex("blackholed_ips")
    
    if index.es.indices.exists("blackholed_ips") != True:
        return jsonify(
            {
                "success": False,
                "message": "The 'blackholed_ips' index does not seem to exist.  Please verify this functionality is enabled.",
                "error_code": 500,
                "data": {}
            }
        )
    
    if request.args.get("query"):
        query = request.args.get("query")
        
        try:
            elastic_hits = index.lquery(query, exact_match=False)
        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "error_code": 500,
                    "message": f"Query {query} caused an issue.  Please verify lucene syntax is correct",
                    "data": {}
                }
            )
        
        hits = []
        for q in elastic_hits['hits']['hits']:
            hits.append(q['_source'])
    
    else:
        hits = []
    
    return jsonify(
        {
            "success": True,
            "message": f"Query successfull.  {len(hits)} results found.",
            "data": hits
        }
    )

@app.route('/blackhole_domain', methods=['GET', 'POST'])
def blackhole_domain():
    try:
        ctrl.system.check_elastic_connection()
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
                "error_code": 500,
                "data": {}
            }
        )
    
    index = ElasticIndex("blackholed_domains")
    
    if index.es.indices.exists("blackholed_domains") != True:
        return jsonify(
            {
                "success": False,
                "message": "The 'blackholed_ips' index does not seem to exist.  Please verify this functionality is enabled.",
                "error_code": 500,
                "data": {}
            }
        )
    
    if request.args.get("query"):
        query = request.args.get("query")
        
        try:
            elastic_hits = index.lquery(query, exact_match=False)
        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "error_code": 500,
                    "message": f"Query {query} caused an issue.  Please verify lucene syntax is correct",
                    "data": {}
                }
            )
        
        hits = []
        for q in elastic_hits['hits']['hits']:
            hits.append(q['_source'])
    
    else:
        hits = []
    
    return jsonify(
        {
            "success": True,
            "message": f"Query successfull.  {len(hits)} results found.",
            "data": hits
        }
    )


@app.route('/show_mac_table', methods=['GET', 'POST'])
def show_mac_table():
    
    #will raise error and except with 500 api return
    ctrl.system.check_elastic_connection()
    
    index = ElasticIndex("sw-inventory")
    
    if index.es.indices.exists("sw-inventory") != True:
        #raise exception with indication that the device inventory is missing
        raise Exception("no device inventory found.")
    
    if request.args.get("hostname"):
        hostname = request.args.get("hostname")
    else:
        raise InvalidUsage("hostname parameter missing", status_code=410)
        
    try:
        info = ctrl.switch.get_switch_info(hostname)
        
    # except any error during the query
    except Exception as e:
        raise Exception(str(e))
    
    if info:

        #generate the data
        data = ctrl.switch.show_mac(info['info'])
        
        # create the response
        response = {
            "success": True,
            "message": f"found device {info['info']['hostname']}",
            "data":{}
        }
        
        if type(data) == list:
            response['message'] += f"-{len(data)} macs found."
        else:
            data = None
            response['message'] += f"-show mac table not supported."
            
        del info['info']['credential']
        
        response['data']['info'] = info['info']
        response['data']['macs'] = data

        return jsonify(response)
    
    else:
        raise DeviceNotFound(hostname)


@app.route('/raw_show/', methods=['GET', 'POST'])
def raw_show():
    # will raise error and except with 500 api return
    ctrl.system.check_elastic_connection()
    
    index = ElasticIndex("sw-inventory")
    
    if index.es.indices.exists("sw-inventory") != True:
        # raise exception with indication that the device inventory is missing
        raise Exception("no device inventory found.")
    
    if request.args.get("hostname"):
        hostname = request.args.get("hostname")
    else:
        raise InvalidUsage("hostname parameter missing", status_code=410)
    
    if request.args.get("command"):
        command = request.args.get("command")
    else:
        raise InvalidUsage("command parameter missing", status_code=410)
    
    try:
        info = ctrl.switch.get_switch_info(hostname)
    
    # except any error during the query
    except Exception as e:
        raise Exception(str(e))
    
    if info:
        
        # generate the data
        data = ctrl.switch.raw_show_output(info['info'], command.split())
        
        # create the response
        response = {
            "success": True,
            "message": f"found device {info['info']['hostname']}",
            "data": {}
        }
        
        del info['info']['credential']
        
        response['data']['info'] = info['info']
        response['data']['output'] = data
        
        return jsonify(response)
    
    else:
        raise DeviceNotFound(hostname)

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.errorhandler(RouteFileNotFound)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.errorhandler(DeviceNotFound)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.errorhandler(Exception)
def exception(error):
    
    err_msg = {
        "error_code": 500,
        "message": (str(error)),
        "success": False
    }
    
    return jsonify(err_msg)

@app.errorhandler(404)
def not_found_error(error):
    
    err_msg = {
        "error_code": 400,
        "message": (str(error)),
        "success": False
    }

    return jsonify(err_msg)
    
@app.errorhandler(500)
def internal_error(error):
    
    err_msg = {
        "error_code": 500,
        "message": (str(error)),
        "success": False
    }
    
    return jsonify(err_msg)