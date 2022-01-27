import logging

def run(record, appconfig):
    """ record the device information after the ping check returns true
       ----------
        record:dict
           record from discover_device_info
        appconfig: config.Config
            environmental variables
        """

    #if the device type is in the supported device types
    if record['device_type'] in appconfig.PLUGIN_MODS:
        #set the plugin module
        try:
            plugin_module = appconfig.PLUGINS[record['device_type']]
            func = plugin_module.rediscover_interface_info
        except:
            logging.error(f"interface info is not supported ond devices type {record['device_type']}")
            return

        # run rediscover_vlan_info
        func((record, appconfig))