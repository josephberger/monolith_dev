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

from elasticsearch import Elasticsearch
import elasticsearch.exceptions
import json
import requests

class ElasticIndexError(Exception):
    pass

class ElasticIndex():

    def __init__(self, index, host="localhost", port="9200", auth=None):

        self.es_server = host
        self.port = str(port)
        self.index = index

        self.es = Elasticsearch([{'host': self.es_server, 'port': self.port}])

    def build(self):

        settings = """{
        "index": {
           "analysis": {
               "filter" : {
                 "my_word_delimiter" : {
                     "type" : "word_delimiter",
                     "preserve_original": "true"
                 }   
             },
              "analyzer": {
                 "my_analyzer": {
                    "type": "custom",
                    "tokenizer": "whitespace",
                    "filter": [
                       "lowercase",
                       "stop",
                       "my_word_delimiter"
                    ]
                         }
                     }
                 }
             }
         }"""

        status = requests.put(url=f"http://{self.es_server}:{self.port}/{self.index}")
        if status.status_code == 200:

            #print(f"Successfully created index {self.index}")
            status = requests.post(url=f"http://{self.es_server}:{self.port}/{self.index}/_close")
            status = requests.put(url=f"http://{self.es_server}:{self.port}/{self.index}/_settings", data=settings,
                              headers={"Content-Type": "application/json"})

            status = requests.post(url=f"http://{self.es_server}:{self.port}/{self.index}/_open")

            return True

        return False

    def delete(self):

        status = requests.delete(url=f"http://{self.es_server}:{self.port}/{self.index}")

        if status.status_code == 200:

            return True

        return False

    def rebuild(self):

        if self.delete():
            self.build()

    def add_document(self, data):

        self.es.index(index=self.index, ignore=400, doc_type='_doc', body=json.loads(json.dumps(data)))

    def remove_document(self, doc):

        try:
            self.es.delete(index=self.index, doc_type="_doc", id=doc['_id'])
        except Exception:
            pass

    def update_document(self,record_id,updates):

        body={"doc": updates}

        self.es.update(index=self.index, id=record_id, body=body)

    def lquery(self, search, field='*', exact_match=True, size=10000):

        if exact_match:
            search = '"'+str(search)+'"'

        search_param = {
            "size": size,
            "query": {
                "query_string": {
                    "query": search,
                    "default_field": field
                }
            }
        }

        try:
            response = self.es.search(index=self.index, body=search_param)
            return response
        except elasticsearch.exceptions.RequestError:
            raise ElasticIndexError(f"Query '{search}' contains invalid syntax.")

    def query(self, search, field=None, exact_match=True, size=10000, sort_field=False, sort_order="asc"):

        search_param = {
            "_source": True,
            "size": size,
            "query": {
                "simple_query_string": {
                    "query": search,
                    "analyze_wildcard": True,
                    "default_operator": "AND"
                }
            }
        }

        if sort_field:
            search_param['sort'] = [
                    { sort_field: {"order" : sort_order}}
                  ]

        if field:
            search_param['query']['simple_query_string']['fields'] = [field]

        try:

            response = self.es.search(index=self.index, body=search_param)
            return response

        except elasticsearch.exceptions.RequestError:
            raise ElasticIndexError(f"Query '{search}' contains invalid syntax.")
