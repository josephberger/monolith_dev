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

from flask import render_template, request, redirect, url_for, flash
from flask_restx import Resource
from http import HTTPStatus
from ..models import NotFoundError
from apps.leviathan import app, api, plugin_mods
from apps.leviathan.forms import Search, Generic

from apps.leviathan import retrieve, taskmgr


@app.route('/endpoint_search', methods=['POST','GET'])
def endpoint_search():

    #method variables
    form = Search()
    device_query = None

    #if a query string exists, query
    if request.args.get("query"):
        query = request.args.get("query")
        device_query = retrieve.endpoint_info_query(query)

    if form.is_submitted():

        #if search button is pressed, get the query from the search box and redirect with requests
        if request.form.get("submit"):
            query = request.form.get("searchbar")
            return redirect(f"{request.url_root}endpoint_search?query={query}")

    return render_template('endpoint_search/endpoint_search.html', title='Endpoint Search', form=form,
                           searchbar=True,device_query=device_query, root_uri=request.url_root)


@app.route('/extended_search', methods=['POST','GET'])
def extended_search():

    #method variables
    form = Search()
    search_query = None
    query_type = None

    #if a query string exists, query
    if request.args.get("query"):
        query = request.args.get("query")
        query_type = request.args.get("query_type")
        if query_type == "vlan":
            search_query = retrieve.vlan_info_query(query)

    if form.is_submitted():

        #if search button is pressed, get the query from the search box and redirect with requests
        if request.form.get("submit"):
            query = request.form.get("searchbar")
            query_type = request.form.get("query_type")
            return redirect(f"{request.url_root}extended_search?query={query}&query_type={query_type}")

    return render_template('extended_search/extended_search.html', title='Extended Search', form=form,
                           searchbar=True,search_query=search_query, root_uri=request.url_root, query_type=query_type)

@app.route('/endpoint_info/<hostname>', methods=['POST','GET'])
def endpoint_info(hostname=None):

    #method variables
    form = Generic()
    device = None

    if hostname:

        hostname = hostname.replace('"','')
        device = retrieve.endpoint_all(hostname)

    if form.is_submitted():

        msg = "no conditions met"
        wait_time = 5000

        if request.form.get("rediscover"):
            job = taskmgr.rediscover_device_info(device['info'])
            msg = f"Rediscovering device at ip:{device['info']['ip']}.  Task ID:{job.id}"
            wait_time = 5000

        elif request.form.get("update_nmap"):
            job = taskmgr.rediscover_nmap_info(device['info'])
            msg = f"Updating scan info for ip:{device['info']['ip']}.  Task ID:{job.id}"
            wait_time = 10000

        elif request.form.get("update_vlan"):
            job = taskmgr.rediscover_vlan_info(device['info'])
            msg = f"Updating vlan info for ip:{device['info']['ip']}.  Task ID:{job.id}"
            wait_time = 5000

        elif request.form.get("update_interfaces"):
            job = taskmgr.rediscover_interface_info(device['info'])
            msg = f"Updating interfaces info for ip:{device['info']['ip']}.  Task ID:{job.id}"
            wait_time = 10000

        elif request.form.get("delete_endpoint"):
            job = taskmgr.remove_endpoint_info(device['info'])
            flash(f"Deleting information for:{device['info']['ip']}.  Task ID:{job.id}","information")
            return redirect(url_for("endpoint_search"))

        return render_template('message/message.html', title="Message",
                               message=msg,
                               redirect_url=request.url, wait_time=wait_time)

    if device:
        title = f'Endpoint Info - {hostname}'
        if device['info']['device_type'] in plugin_mods:
            device_type = device['info']['device_type']
            template = f'endpoint_info/{device_type}/endpoint_info.html'
        else:
            template = 'endpoint_info/endpoint_info.html'
    else:
        title = 'Endpoint Info'
        template = 'endpoint_info/endpoint_info.html'

    return render_template(template, title=title, device=device,
                               form=form)


@api.route('/api/endpoint_info/<hostname>')
class api_endpoint_info(Resource):
    @api.response(HTTPStatus.OK.value, "Get all the endpoint's information")
    @api.response(HTTPStatus.NOT_FOUND.value, "Endpoint doesn't exist")
    def get(self, hostname):

        endpoint = retrieve.endpoint_all(hostname.replace('"', ''))

        if endpoint:
            return endpoint

        raise NotFoundError(message = f"Endpoint '{hostname}' doesn't exist")

    @api.response(HTTPStatus.OK.value, "Delete all the endpoint's information")
    @api.response(HTTPStatus.NOT_FOUND.value, "Endpoint doesn't exist")
    def delete(self, hostname):

        endpoint = retrieve.endpoint_info(hostname)

        if endpoint:
            job = taskmgr.remove_endpoint_info(endpoint)

            return {"message":f"Removing endpoint {hostname}",
                    "job_id": job.id}

        raise NotFoundError(message=f"Endpoint '{hostname}' doesn't exist")


@api.route('/api/endpoint_search/<query>')
class api_endpoint_info(Resource):
    @api.response(HTTPStatus.OK.value, "Get endpoint list that matches query")
    def get(self, query):

        endpoint_query = retrieve.endpoint_info_query(query)

        if endpoint_query:
            reseponse = {}
            reseponse['data'] = endpoint_query['data']
            return reseponse