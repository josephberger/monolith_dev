from flask import render_template, request, redirect, url_for, flash
from flask_restx import Resource, abort
from http import HTTPStatus
import ctrl
from ..models import NotFoundError
from apps.leviathan import app, api
from apps.leviathan.forms import SwitchSearch, Generic
from config import GlobalConfig
from tasks.rediscover import rediscover_device_info, rediscover_nmap_info
from tasks.remove import remove_endpoint_info


@app.route('/endpoint_search', methods=['POST','GET'])
def endpoint_search():

    #method variables
    form = SwitchSearch()
    device_query = None

    #if a query string exists, query.
    if request.args.get("query"):
        query = request.args.get("query")
        device_query = ctrl.retrieve.reteive_endpoint_info_query(query)

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
        device = ctrl.reteive_endpoint_all(hostname)

    if form.is_submitted():

        if request.form.get("rediscover"):
            job = GlobalConfig.DEFAULT_QUEUE.enqueue(rediscover_device_info.run, device['info'], description=f"Rediscover {device['info']['ip']}")
            flash(f"Rediscovering device at ip:{device['info']['ip']}.  Task ID:{job.id}","information")
            return redirect(url_for("endpoint_search"))

        if request.form.get("update_nmap"):
            job = GlobalConfig.HIGH_QUEUE.enqueue(rediscover_nmap_info.run, device['info'], description=f"Re-NMAP {device['info']['ip']}")
            flash(f"Updating scan info for ip:{device['info']['ip']}.  Task ID:{job.id}","information", )
            return redirect(url_for("endpoint_search"))

        if request.form.get("delete_endpoint"):
            job = GlobalConfig.HIGH_QUEUE.enqueue(remove_endpoint_info.run, device['info'], description=f"Delete {device['info']['ip']}")
            flash(f"Deleting information for:{device['info']['ip']}.  Task ID:{job.id}","information")
            return redirect(url_for("endpoint_search"))

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

        endpoint = ctrl.reteive_endpoint_all(hostname.replace('"', ''))

        if endpoint:
            return endpoint

        raise NotFoundError(message = f"Endpoint '{hostname}' doesn't exist")

    @api.response(HTTPStatus.OK.value, "Delete all the endpoint's information")
    @api.response(HTTPStatus.NOT_FOUND.value, "Endpoint doesn't exist")
    def delete(self, hostname):

        endpoint = ctrl.reteive_endpoint_info(hostname)

        if endpoint:
            job = GlobalConfig.HIGH_QUEUE.enqueue(remove_endpoint_info.run, endpoint,
                                                  description=f"Delete {endpoint['ip']}")

            return {"message":f"Removing endpoint {hostname}",
                    "job_id": job.id}

        raise NotFoundError(message=f"Endpoint '{hostname}' doesn't exist")


@api.route('/api/endpoint_search/<query>')
class api_endpoint_info(Resource):
    @api.response(HTTPStatus.OK.value, "Get endpoint list that matches query")
    #@api.response(HTTPStatus.NOT_FOUND.value, "Endpoint doesn't exist")
    def get(self, query):

        endpoint_query = ctrl.retrieve.reteive_endpoint_info_query(query)

        if endpoint_query:
            reseponse = {}
            reseponse['data'] = endpoint_query['data']
            return reseponse

        #raise NotFoundError(message=f"Endpoint '{hostname}' doesn't exist")