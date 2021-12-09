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

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

class SwitchSearch(FlaskForm):
    searchbar = StringField("Search")
    submit = SubmitField("Submit")
    export = SubmitField('Export')
    ansible = SubmitField("Ansible Inventory")
    selected = SubmitField("Bulk Commands")
    
class LogSearch(FlaskForm):
    searchbar = StringField("Search")
    submit = SubmitField("Submit")
    export = SubmitField('Export')

class ExportCSV(FlaskForm):
    export = SubmitField('Export CSV')
    back = SubmitField('Back')

class SwitchInfo(FlaskForm):
    interfacestatus = SubmitField("Show Interface Status")
    version = SubmitField("Show Version")
    inventory = SubmitField("Show Inventory")
    run_config = SubmitField("Show Config")
    history_go = SubmitField("Go")
    compare = SubmitField("Diff")
    show_mac_addr_table = SubmitField("Show MAC Table")
    show_environment = SubmitField("Show Environment")
    refresh_device = SubmitField("Refresh Device")
    vrf_interface_report = SubmitField("VRF Int Report")
    vrf_arp_table = SubmitField("VRF ARP Table")

class BulkCommands(FlaskForm):
    show_mac_addr_table = SubmitField("Show MAC Table")
    interfacestatus = SubmitField("Show Interface Status")
    vrf_interface_report = SubmitField("VRF Int Report")
    
class InterfaceInfo(FlaskForm):
    gatherinfo = SubmitField("Gather Information")

