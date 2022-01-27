from flask import render_template, request, redirect, url_for, flash
from flask_restx import Resource
from http import HTTPStatus
from ..models import NotFoundError
from apps.leviathan import app, api
from apps.leviathan.forms import SwitchSearch, Generic

from apps.leviathan import retrieve, taskmgr


@app.route('/endpoint_search', methods=['POST','GET'])
def endpoint_search():

    #method variables
    form = SwitchSearch()
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
    else:
        title = 'Endpoint Info'

    return render_template('endpoint_info/endpoint_info.html', title=title, device=device,
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