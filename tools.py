# author: Satyendra Gurjar
# -------------------
# tools.py
# -------------------
# this script contains utility methods
# for websphere configuration
#

# -----------------------------------------imports
import sys
import java


# -----------------------------------------constants
line_sep      = java.lang.System.getProperty('line.separator')
classpath_sep = ';'
path_sep      = java.lang.System.getProperty('path.separator')


# -----------------------------------------create_cluster
# creates cluster with no member in it
# -----------------------------------------
def create_cluster(scope_id,cluster_params):
    name      =cluster_params.get('name');
    desc      =cluster_params.get('description');
    pref_local=cluster_params.get('preferLocal');
    init_state=cluster_params.get('initialState');

    attrs = []
    attrs.append(["name", name])
    attrs.append(["description", desc])
    attrs.append(["preferLocal", pref_local])
    attrs.append(["stateManagement", [["initialState", init_state]]])
    cluster = AdminConfig.create("ServerCluster", scope_id, attrs)

    print '=======created cluster %s' % cluster
    print AdminConfig.showall(cluster)
    print '==============================='

    return cluster;
#end create_cluster


# -----------------------------------------create_new_members_in_cluster
# creates new servers and add to cluster
#   cluster: id of cluster
#   node: id of node servers to be created
#   server_list: list of name of servers to
#       be created and add to the cluster
# -----------------------------------------
def create_new_members_in_cluster(cluster,node,server_list):
    added_servers=[]

    for server in server_list:
        attrs = []
        attrs.append(["memberName", server])
        server = AdminConfig.createClusterMember(cluster, node, attrs)
        added_servers.append(server)

    print '=======added members to cluster %s' % cluster
    members=AdminConfig.showAttribute(cluster,'members')
    members=members[1:len(members)-1] # first and last []
    for m in members.split():
        print AdminConfig.show(m)
        print "-----"
    print '==============================='

    return added_servers;

#end create_new_members_in_cluster

#------------------------------------------create_server
# creates new server
def create_server(node_id, server_name, template_name='default'):
    err_msg='ERROR (create_server): NOT creating server.'

    if not node_id:
        print err_msg + ' No node_id'
        return 0
    #end if

    if not server_name:
        print err_msg + ' No server_name'
        return 0
    #end if

    attrs=[]
    attrs.append(["name", server_name])

    template=get_app_server_template(template_name)
    if not template:
        print 'No template found by name "%s". Creating server without using template ' % template_name
        server = AdminConfig.createUsingTemplate("Server", node_id, attrs, template)
    else:
        print 'Creating server "%s" using template "%s"' % (server_name,template_name)
        server = AdminConfig.create("Server", node_id, attrs)
    #end if

    print '========Created server %s' % server
    print AdminConfig.show(server)
    print '================================='

    return server;

##end create_server

#-------------------------------------------get_app_server_template
# return APPLICATION_SERVER type server template with name template_name
#
def get_app_server_template(template_name):
    templates=AdminConfig.listTemplates('Server').split(line_sep)
    for template in templates:
        try:
            server_type=AdminConfig.showAttribute(template,'serverType')
            if ('APPLICATION_SERVER'==server_type):
                if (template_name==AdminConfig.showAttribute(template,'name')):
                    return template;
        except:   # ignore,
            None; # when serverType is not an attribute of template
    #end for

    print 'ERROR(get_app_server_template) No server template found of APPLICATION_SERVER type by name "%s" ' % template_name;
    return 0;
##end def get_app_server_template

#------------------------------------------get_virtual_host
def get_virtual_host(virtual_host_name):
    existing_virtual_hosts=AdminConfig.list('VirtualHost')
    for existing_vh in existing_virtual_hosts.split(line_sep):
        existing_vh_name=AdminConfig.showAttribute(existing_vh,'name')
        if virtual_host_name==existing_vh_name:
            return existing_vh;
    #end for

    return None

#end def get_virtual_host

#------------------------------------------is_virtual_host_port_exists
def is_virtual_host_port_exists(virtual_host, port):
    aliases=AdminConfig.showAttribute(virtual_host,'aliases')
    aliases=aliases[1:len(aliases)-1]
    for alias in aliases.split():
        existing_host=AdminConfig.showAttribute(alias,'hostname')
        existing_port=AdminConfig.showAttribute(alias,'port')
        if port == existing_port:
            return 1;
        #end if
    #end for

    return 0;
#end def is_virtual_host_port_exists

# -----------------------------------------add_port_to_virtual_host
def add_port_to_virtual_host(virtual_host, port, host='*'):
    err_msg='ERROR(add_port_to_virtual_host): NOT adding port. '

    if is_virtual_host_port_exists(virtual_host, port):
        print '%s Port "%s" already exists in virtual host %s ' % (err_msg,port,virtual_host)
        return 0;
    #end if

    attrs=[]
    attrs.append(['hostname', host])
    attrs.append(['port', port])
    host_alias=AdminConfig.create('HostAlias', virtual_host, attrs)
    print 'Added port to virtual host. virtual_host=%s attrs=%s' % (virtual_host,attrs)

    return host_alias;

#end def add_port_to_virtual_host

# -----------------------------------------get_virtual_host_template
def get_virtual_host_template(template_name):
    templates=AdminConfig.listTemplates('VirtualHost')
    for template in templates.split('\n'):
        if template_name==AdminConfig.showAttribute(template,'name'):
            return template;
    #end for

    return None;

#end def get_virtual_host_template

# -----------------------------------------create_virtual_host
def create_virtual_host(cell_id, virtual_host_name, template_name='default_host'):

    err_msg='ERROR(create_virtual_host): NOT creating virtual host. '

    existing_vh=get_virtual_host(virtual_host_name)
    if existing_vh:
        print '%s Virtual host "%s" already exists. "%s"' % (err_msg,virtual_host_name,existing_vh)
        return 0;
    #end if

    vh_template=get_virtual_host_template(template_name)
    if not vh_template:
        print '%s No Virtual host template by name "%s"' % (err_msg,template_name)
        return 0;
    #end if

    vh_attrs=[]
    vh_attrs.append(['name',virtual_host_name])
    new_vh=AdminConfig.createUsingTemplate('VirtualHost', cell_id, vh_attrs, vh_template)
    print 'Created new virtual host. "%s" ' % AdminConfig.showAttribute(new_vh,'name')

    return new_vh;

##end def create_virtual_host

# -----------------------------------------update_server_ports
#    ports map of ports to be updated.
#
#    example:
#
#        ports={
#            'BOOTSTRAP_ADDRESS'     :{'host':'host1.com','port':'9820'}
#           ,'SOAP_CONNECTOR_ADDRESS':{'host':'host2.com','port':'8890'}
#           ,'WC_defaulthost'        :{'host':'*'        ,'port':'9087'}
#           ,'WC_defaulthost_secure' :{'host':'*'        ,'port':'9449'}
#           ,'WC_adminhost'          :{'host':'*'        ,'port':'9067'}
#           ,'WC_adminhost_secure'   :{'host':'*'        ,'port':'9049'}
#        }
#--------------------------------------------------------------
def update_server_ports(node_name, server_name, ports):

    err_msg='ERROR (update_server_ports): NOT updating ports. ';

    if not node_name:
        print '%s No node_name' % (err_msg)
        return 0;
    ##end if

    if not server_name:
        print '%s No server_name' % (err_msg)
        return 0;
    ##end if

    if not ports:
        print '%s No ports' % (err_msg)
        return 0;
    ##end if

    ####if not cell_name: cell_name=AdminControl.getCell()###

    ###
    ###node_id=AdminConfig.getid('/Node:%s/' % (node_name))
    ###if not node_id:
    ###    print '%s No node found with name "%s"' % (err_msg, node_name)
    ###    return 0;
    #####end if

    server_id=AdminConfig.getid('/Node:%s/Server:%s/' % (node_name,server_name))
    if not server_id:
        print '%s No server found with name "%s" in node "%s"' % (err_msg, server_name, node_name)
        return 0;
    ##end if

    # bootstrap
    # ~~~~~~~~~
    bootstrap=ports.get('BOOTSTRAP_ADDRESS')
    if bootstrap:
        bs_attrs=[]
        host=bootstrap.get('host')
        port=bootstrap.get('port')
        if host: bs_attrs.append(['host', host]);
        if port: bs_attrs.append(['port', port]);
        if bs_attrs:
            ns=AdminConfig.list('NameServer', server_id)
            if not ns:
                print "%s NameServer not found in %s" % (err_msg, server_id)
                return 0;
            ##end if
            print 'Updating BOOTSTRAP_ADDRESS for %s. %s ' % (server_name,bs_attrs)
            AdminConfig.modify(ns, [['BOOTSTRAP_ADDRESS', bs_attrs]])
        else:
            print 'No attrinutes NOT updating BOOTSTRAP_ADDRESS.'
        #end bs_attrs
    #end if bootstrap

    # soap connector
    # ~~~~~~~~~~~~~~
    soapconnector=ports.get('SOAP_CONNECTOR_ADDRESS')
    if soapconnector:
        sc_attrs=[]
        host=soapconnector.get('host')
        port=soapconnector.get('port')
        if host: sc_attrs.append(['host', host])
        if port: sc_attrs.append(['port', port])
        if sc_attrs:
            soap = AdminConfig.list('SOAPConnector', server_id)
            if not soap:
                print '%s No SOAPConnector found in %s' (err_msg,server_id)
                return 0
            ##end if
            print 'Updating SOAP_CONNECTOR_ADDRESS for %s. %s ' % (server_name, sc_attrs)
            AdminConfig.modify(soap, [['SOAP_CONNECTOR_ADDRESS', sc_attrs]])
        else:
            print 'No attrinutes NOT updating SOAP_CONNECTOR_ADDRESS.'
        #end sc_attrs

    # WC_defaulthost
    # ~~~~~~~~~~~~~~
    wc_defaulthost=ports.get('WC_defaulthost')
    if wc_defaulthost:
            if not update_server_entry_special_endpoint(node_name, server_name, 'WC_defaulthost', wc_defaulthost):
                return 0;

    # WC_defaulthost_secure
    # ~~~~~~~~~~~~~~~~~~~~~
    wc_defaulthost_secure=ports.get('WC_defaulthost_secure')
    if wc_defaulthost_secure:
            if not update_server_entry_special_endpoint(node_name, server_name, 'WC_defaulthost_secure', wc_defaulthost_secure):
                return 0;

    # WC_adminhost
    # ~~~~~~~~~~~~
    wc_adminhost=ports.get('WC_adminhost')
    if wc_adminhost:
            if not update_server_entry_special_endpoint(node_name, server_name, 'WC_adminhost', wc_adminhost):
                return 0;

    # WC_adminhost_secure
    # ~~~~~~~~~~~~~~~~~~~
    wc_adminhost_secure=ports.get('WC_adminhost_secure')
    if wc_adminhost_secure:
            if not update_server_entry_special_endpoint(node_name, server_name, 'WC_adminhost_secure', wc_adminhost_secure):
                return 0;

    return 1;

## end def update_server_ports

#------------------------------------------update_server_entry_special_endpoint
def update_server_entry_special_endpoint(node_name, server_name, endpoint_name, endpoint_parms):
    err_msg="ERROR (update_server_entry_special_endpoint): NOT updating. "

    if not server_name:
        print '%s No server_name' % err_mag
        return 0;
    #end if

    if not endpoint_name:
        print '%s No endpoint_name' % err_mag
        return 0;
    #end if

    if not endpoint_parms:
        print '%s No endpoint_parms' % err_mag
        return 0;
    #end if

    attrs=[]
    host=endpoint_parms.get('host')
    port=endpoint_parms.get('port')
    if host: attrs.append(['host',host])
    if port: attrs.append(['port',port])

    if not attrs:
        print '%s No endpoint attributes. endpoint_parms=%s' % (err_mag,endpoint_parms)
        return 0;
    #end if

    node = AdminConfig.getid('/Node:%s/' % node_name)
    if not node:
        print '%s Node NOT found by name "%s"' % (err_mag, node_name)
        return 0;
    #end if

    server_entries=AdminConfig.list('ServerEntry', node).split(line_sep)
    for entry in server_entries:
        if server_name == AdminConfig.showAttribute(entry, "serverName"):
            special_endpoints=AdminConfig.showAttribute(entry, "specialEndpoints")
            special_endpoints=special_endpoints[1:len(special_endpoints)-1].split(' ')
            for special_endpoint in special_endpoints:
                if endpoint_name == AdminConfig.showAttribute(special_endpoint, "endPointName"):
                   end_point = AdminConfig.showAttribute(special_endpoint, "endPoint")
                   print 'Updating %s end point with for %s. %s' % (endpoint_name,server_name,attrs)
                   AdminConfig.modify(end_point, attrs)
                   return 1;
                ##end if
            ##end for
        ##end if
    ##end for entry in server_entries:

#------------------------------------------update_http_transport_ports
# ports={
#    'ssl':{'host':host, 'port':port}
#    'nonssl':{}
# }
def update_http_transport_ports(server_id, ports):
    httpNonSecureAddress = [["sslEnabled", "false"], ["address", [["host", ""], ["port", 9088]]]]
    httpSecureAddress = [["sslEnabled", "true"], ["address", [["host", ""], ["port", 9948]]], ["sslConfig", "DefaultSSLSettings"]]
    transports = [["transports:HTTPTransport", [httpNonSecureAddress, httpSecureAddress]]]
    web_container=AdminConfig.list("WebContainer", server_id)
    AdminConfig.modify(web_container, transports)
    print AdminConfig.showall(web_container);

##end def update_http_transport_ports

# -----------------------------------------get_custom_property
# gets custom property of config objects
#   config: config object custom properties to be get on
#   property_name: name of the property
# returns list of value for given property name
# -----------------------------------------
def get_custom_property(config, property_name, conf_attribute='properties'):
    existing_props = []  # there could be more then one property with same name

    properties=AdminConfig.showAttribute(config,conf_attribute)
    if not properties:
        return existing_props;

    properties = properties[1:len(properties)-1] # get rid of first [ and last ]
    #print properties;

    for p in properties.split():
        i_p = p.find('(')
        if (i_p > -1):
          if ( p[0:i_p] == property_name ):
            existing_props.append(p)

    return existing_props
#end get_custom_property

# -----------------------------------------set_custom_property
# sets custom properties on configuration object.
#   config: config object custom properties to be set on
#   properties: list of dict, each dict is one property
#   overwrite: if 1 overwrites property if exists.
# -----------------------------------------
def set_custom_property(config, properties, overwrite=1, conf_attribute='properties'):
    new_properties=[];
    for prop in properties:
        name=prop.get('name');
        if not name: continue;
        value=prop.get('value');
        if value is None: value='';
        descr=prop.get('description');
        if descr is None: descr='';
        reqrd=prop.get('required');
        if (reqrd is None) or (reqrd!='true'): reqrd='false';
        existing_properties=get_custom_property(config, name, conf_attribute);
        if existing_properties:
            if not overwrite:
                print 'custom property "%s" already exists, not creating.' % (name);
                return;
            else:
                print 'custom property "%s" already exists, overwriting...' % (name);
            for existing_prop in existing_properties:
                AdminConfig.remove(existing_prop);
        else:
            print 'custom property "%s" not exists, creating...' % (name);

        p=[ [ 'name', name ], [ 'value', value ], [ 'description', descr ], [ 'required', reqrd ] ];
        new_properties.append(p);

    if new_properties:
        AdminConfig.modify( config, [[conf_attribute, new_properties]] );
        print '-----updated custom properties for %s' % config;
        verify_props=AdminConfig.showAttribute(config,conf_attribute)
        verify_props=verify_props[1:len(verify_props)-1]
        for p in verify_props.split():
            print AdminConfig.showall(p)+line_sep;
        print '----------------------------';
    else:
        print 'no properties to set, did nothing.'

#end set_custom_property

#------------------------------------------------------set_ml_service_custom_properties
def set_ml_service_properties(server_id, properties, update_if_exists=0):
    mls=AdminConfig.list("MessageListenerService", server_id)
    print 'setting properties for %s' % mls;
    set_custom_property(mls, properties, update_if_exists);
##end def set_ml_service_custom_properties

#------------------------------------------------------set_transaction_service_properties
def set_transaction_service_properties(server_id, properties, update_if_exists=0):
    txs=AdminConfig.list("TransactionService", server_id)
    print 'setting properties for %s' % txs;
    set_custom_property(txs, properties, update_if_exists);
##end set_transaction_service_properties

#--------------------------------------------------------set_sslconfig_property
def set_sslconfig_property(server_id, new_value):
    err_msg='ERROR (set_sslconfig_property): NOT setting sslconfig property.'

    if not server_id:
        print err_msg + ' No server_id'
        return 0;

    if not new_value:
        print err_msg + ' No new_value'
        return 0;

    admin_services=AdminConfig.list('AdminService',server_id)
    if not admin_services:
        print err_msg + ' No AdminService for server_id ' + server_id
        return 0;

    preferred_connector=AdminConfig.showAttribute(admin_services,'preferredConnector')
    if not preferred_connector:
        print err_msg + ' No preferredConnector for server_id ' + server_id
        return 0;

    props=AdminConfig.showAttribute(preferred_connector,'properties')
    props=props[1:len(props)-1]
    for p in props.split(' '):
        name=AdminConfig.showAttribute(p,'name');
        value= AdminConfig.showAttribute(p,'value');
        if name=='sslConfig':
            print 'Updating sslConfig property to "%s" for: %s' % (new_value,server_id)
            AdminConfig.modify(p, [['value',new_value]])
            print '=========Updated sslConfig property for: %s ' % preferred_connector
            print AdminConfig.showall(preferred_connector).replace(line_sep,'')
            print '======================================='
            return 1;
        #end if
    #end for

    print err_msg + ' sslConfig property not found for server ' + server_id
    return 0;

##end def set_sslconfig_property

#--------------------------------------------------------set_jvm_props
# config_props={
#     verboseModeClass:"false"
#     verboseModeGarbageCollection:"false"
#     verboseModeJNI:"false"
#     initialHeapSize:"64"
#     maximumHeapSize:"512"
#     runHProf:"false"
#     debugMode:"false"
#     debugArgs:"-Djava.compiler=NONE -Xdebug -Xnoagent -Xrunjdwp:transport=dt_socket,server=y,suspend=n,address=7777"
#     disableJIT:"false"
#   }
#
# custom_props=[
#    {'name':'prop_name_1','value':'prop_value_1','description':'prop description 1'}
#    {'name':'prop_name_2','value':'prop_value_2','description':'prop description 2'}
#    {'name':'prop_name_3','value':'prop_value_3','description':'prop description 3'}
#  ]
#
#--------------------------------------------------------
def set_jvm_props(server_id, config_props, custom_props, update_if_exists=1):
    conf_attribute='systemProperties'

    jvm = AdminConfig.list('JavaVirtualMachine', server_id)

    updated=0

    if config_props:

        verboseModeClass            =config_props.get('verboseModeClass')
        verboseModeGarbageCollection=config_props.get('verboseModeGarbageCollection')
        verboseModeJNI              =config_props.get('verboseModeJNI')
        initialHeapSize             =config_props.get('initialHeapSize')
        maximumHeapSize             =config_props.get('maximumHeapSize')
        runHProf                    =config_props.get('runHProf')
        debugMode                   =config_props.get('debugMode')
        debugArgs                   =config_props.get('debugArgs')
        disableJIT                  =config_props.get('disableJIT')

        config_attrs=[]
        if verboseModeClass            : config_attrs.append(['verboseModeClass'            , verboseModeClass])
        if verboseModeGarbageCollection: config_attrs.append(['verboseModeGarbageCollection', verboseModeGarbageCollection])
        if verboseModeJNI              : config_attrs.append(['verboseModeJNI'              , verboseModeJNI])
        if initialHeapSize             : config_attrs.append(['initialHeapSize'             , initialHeapSize])
        if maximumHeapSize             : config_attrs.append(['maximumHeapSize'             , maximumHeapSize])
        if runHProf                    : config_attrs.append(['runHProf'                    , runHProf])
        if debugMode                   : config_attrs.append(['debugMode'                   , debugMode])
        if debugArgs                   : config_attrs.append(['debugArgs'                   , debugArgs])
        if disableJIT                  : config_attrs.append(['disableJIT'                  , disableJIT])

        if config_attrs:
            print 'Updating jvm configurations %s ' % jvm
            AdminConfig.modify(jvm, config_attrs);
            updated=1
        ##end if config_attrs:

    ##end if config_props:

    if custom_props:
        print 'Updating jvm custom properties %s ' % jvm
        set_custom_property(jvm, custom_props, update_if_exists, conf_attribute)
        updated=1
    ##end if custom_props:

    if updated:
        print '===========jvm properties updated %s' % jvm
        print AdminConfig.showall(jvm)
        print '================================='
    ##end if updated:

##end set_jvm_props

#----------------------------------------------------------------------------create_data_source
# creates new oracle data source in cell scope
#
#   cell_name: name of the cell datasource to be created in, optional.
#        If not provided then AdminControl.getCell() will be used.
#       This returns cell name to which wsadminis connected to.
#
#   jdbcprovider:  JDBC Provider where datasource will be created. (keys are case-sensitive)
#        This is map, can have attributes like 'name', 'description', 'classpath', 'implementationClassName'
#        Since websphere can have JDBC Provider with same name this method will try to match using attributes
#        given in map, in the order they are mentioned above.
#
#   datasource: map contains attributes of datasource to be created. (keys are case-sensitive)
#        'name'                      - name of datasource, required
#        'jndi'                      - jndi name of datasource. if not provided datasource
#                                      will be created without jndi name.
#        'description'               - description of datasource, optional
#        'authMechanismPreference'   - optional, if not provided BASIC_PASSWORD will be used.
#        'authDataAlias'             - Alias of J2C Authentication Data Entry, required
#        'template'                  - name of the datasource template to be use to create datasource, optional.
#                                      If not provided "Oracle JDBC Driver XA DataSource" will be used.
#        'mappingConfigAlias'        - Mapping-Configuration Alias, optional. if not provied 'DefaultPrincipalMapping' will be used
#
#        'connectionTimeout' - connectionpool setting, optional.
#        'maxConnections'    - connectionpool setting, optional.
#        'minConnections'    - connectionpool setting, optional.
#        'reapTime'          - connectionpool setting, optional.
#        'unusedTimeout'     - connectionpool setting, optional.
#        'agedTimeout'       - connectionpool setting, optional.
#        'purgePolicy'       - connectionpool setting, optional. valid values are 'EntirePool', 'FailingConnectionOnly'
#
#    properties: dict of custom properties for datasource, optional. (keys are case-sensitive)
#        example:
#            properties={'URL':'jdbc:oracle:thin:@host1.rac1.com:1234:mypassword'
#                ,'transactionBranchesLooselyCoupled':'true'}
#----------------------------------------------------------------------------
def create_data_source(cell_name, jdbcprovider, datasource, properties):
    err_msg="ERROR (create_data_source): NOT creating datasource.";

    ds_name=datasource.get('name');
    if not ds_name:
        print err_msg + " datasource name not found."
        return 0;
    #end if not ds_name:

    ds_auth_alias=datasource.get('authDataAlias')
    if not ds_auth_alias:
        print err_msg + " authDataAlias not found."
        return 0;
    #end if not ds_auth_alias:

    # get scope
    # ~~~~~~~~~
    if not cell_name: cell_name=AdminControl.getCell()
    scope='/Cell:' + cell_name;

    # get J2CResourceAdapter to enable cmp
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    resource_adapters=AdminConfig.getid(scope+'/J2CResourceAdapter:/').split(line_sep)
    resource_adapter=None
    for ra in resource_adapters:
        if 'WebSphere Relational Resource Adapter' == AdminConfig.showAttribute(ra,'name'):
            resource_adapter=ra
            break
        ##end if
    ##end for ra in resource_adapters:

    if not resource_adapter:
        print '%s No J2CResourceAdapter found in "%s" scope.' % (err_msg, scope);
        return 0;
    #end if not resource_adapter

    # get datasource properties
    #~~~~~~~~~~~~~~~~~~~~~~~~~~
    ds_jndi      =datasource.get('jndi');
    ds_desc      =datasource.get('description');

    ds_auth_pref =datasource.get('authMechanismPreference');
    if not ds_auth_pref: ds_auth_pref='BASIC_PASSWORD'

    ds_template_name=datasource.get('template');
    if not ds_template_name: ds_template_name="Oracle JDBC Driver XA DataSource";

    # find jdbc provider
    # ~~~~~~~~~~~~~~~~~~
    matched_jdbc_provider=None;
    jdbc_prov_name=jdbcprovider.get('name');
    jdbc_prov_desc=jdbcprovider.get('description');
    jdbc_prov_clsp=jdbcprovider.get('classpath');
    jdbc_prov_impl=jdbcprovider.get('implementationClassName');
    jdbc_providers=AdminConfig.getid(scope+'/JDBCProvider:/');
    for jdbc_provider in jdbc_providers.split(line_sep):
        match=0;
        if (jdbc_prov_name):
            name=AdminConfig.showAttribute(jdbc_provider,"name")
            match=(name==jdbc_prov_name)

        if (jdbc_prov_desc):
            desc=AdminConfig.showAttribute(jdbc_provider,"description")
            match=(desc==jdbc_prov_desc)

        if (jdbc_prov_clsp):
            clsp=AdminConfig.showAttribute(jdbc_provider,"classpath")
            match=(clsp==jdbc_prov_clsp)

        if (jdbc_prov_impl):
            impl=AdminConfig.showAttribute(jdbc_provider,"implementationClassName")
            match=(impl==jdbc_prov_impl)

        if match:
            matched_jdbc_provider=jdbc_provider
            break;
    #end for jdbc_provider in jdbc_providers.split(line_sep):

    # can't find jdbprovider
    # ~~~~~~~~~~~~~~~~~~~~~~
    if not matched_jdbc_provider:
        print '%s NO jdbc provider found with "%s" in "%s" scope ' % (err_msg, jdbcprovider,scope);
        return 0;
    #endif

    # check if datasource already exists
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    matched_jdbc_provider_name=AdminConfig.showAttribute(matched_jdbc_provider,"name")
    existing_ds_list=AdminConfig.getid(scope + "/JDBCProvider:%s/DataSource:/" % matched_jdbc_provider_name)
    for existing_ds in existing_ds_list.split(line_sep):
        if ds_name == AdminConfig.showAttribute(existing_ds, "name"):
            print '%s DataSource "%s" already exists in "%s" scope.' % (err_msg, existing_ds,scope);
            return 0;
        #end if
    #end for

    # find datasource template
    # ~~~~~~~~~~~~~~~~~~~~~~~~
    ds_template = AdminConfig.listTemplates("DataSource", ds_template_name).split(line_sep)[0]
    if not ds_template:
        print '%s Could not find a DataSource template using "%s".' % (err_msg,ds_template_name)
        return 0;
    #end if

    # create datasource with template
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ds_attrs=[]
    ds_attrs.append(['name',ds_name]);
    if ds_jndi      : ds_attrs.append(['jndiName',ds_jndi]);
    if ds_desc      : ds_attrs.append(['description',ds_desc]);
    if ds_auth_pref : ds_attrs.append(['authMechanismPreference',ds_auth_pref]);
    if ds_auth_alias: ds_attrs.append(['authDataAlias',ds_auth_alias]);

    print 'Creating datasource %s... jdbcprovider=%s, datasource_template=%s, attrs=%s\n' % (ds_name,matched_jdbc_provider,ds_template,ds_attrs);
    ds=AdminConfig.createUsingTemplate('DataSource', matched_jdbc_provider, ds_attrs, ds_template)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # CMPConnectorFactory
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    cmp_cf_attrs=[]
    cmp_cf_attrs.append(['name', (ds_name + '_CF')]);
    cmp_cf_attrs.append(['authMechanismPreference',ds_auth_pref]);
    cmp_cf_attrs.append(['cmpDatasource',ds]);
    cmp_cf_attrs.append(['authDataAlias',ds_auth_alias]); # 'pidb205Manager/mpsdb'
    print 'Creating cmpconnectorfactory... resource_adapter=%s, attrs=%s\n' % (resource_adapter, cmp_cf_attrs)
    AdminConfig.create('CMPConnectorFactory', resource_adapter, cmp_cf_attrs);

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # MappingModule
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ds_mapping_module_alias=datasource.get('mappingConfigAlias')
    if not ds_mapping_module_alias: ds_mapping_module_alias='DefaultPrincipalMapping'
    mapping_module_attrs=[]
    mapping_module_attrs.append(['mappingConfigAlias',ds_mapping_module_alias]); #'DefaultPrincipalMapping'
    mapping_module_attrs.append(['authDataAlias',ds_auth_alias]); # 'pidb205Manager/mpsdb'
    print 'Creating mapping module... datasource=%s attrs=%s\n' % (ds,mapping_module_attrs)
    AdminConfig.create("MappingModule",ds,mapping_module_attrs);

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ConnectionPool
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    conn_pool_attrs=[]

    connectionTimeout=datasource.get('connectionTimeout')
    if connectionTimeout: conn_pool_attrs.append(['connectionTimeout',connectionTimeout]);

    maxConnections=datasource.get('maxConnections')
    if maxConnections: conn_pool_attrs.append(['maxConnections',maxConnections]);

    minConnections=datasource.get('minConnections')
    if minConnections: conn_pool_attrs.append(['minConnections',minConnections]);

    reapTime=datasource.get('reapTime')
    if reapTime: conn_pool_attrs.append(['reapTime',reapTime]);

    unusedTimeout=datasource.get('unusedTimeout')
    if unusedTimeout: conn_pool_attrs.append(['unusedTimeout',unusedTimeout]);

    agedTimeout=datasource.get('agedTimeout')
    if agedTimeout: conn_pool_attrs.append(['agedTimeout',agedTimeout]);

    purgePolicy=datasource.get('purgePolicy')
    if (purgePolicy) and (purgePolicy in ['EntirePool', 'FailingConnectionOnly']):
        conn_pool_attrs.append(['purgePolicy',purgePolicy]);

    if conn_pool_attrs:
        print 'Creating connectionpool... datasource=%s attrs=%s\n' % (ds,conn_pool_attrs)
        AdminConfig.create('ConnectionPool',ds,conn_pool_attrs);

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # J2EEResourcePropertySet
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print 'Updating J2EEResourcePropertySet...'
    res_prop_set=AdminConfig.list('J2EEResourcePropertySet',ds).split(line_sep)[0];
    if res_prop_set:
            print 'Updating "%s"' % res_prop_set
            existing_res_props=AdminConfig.showAttribute(res_prop_set,'resourceProperties')
            if existing_res_props:
                existing_res_props = existing_res_props[1:len(existing_res_props)-1] # get rid of first [ and last ]
                for p in existing_res_props.split():
                    p_name=AdminConfig.showAttribute(p,'name');
                    if properties.has_key(p_name):
                        AdminConfig.modify(p,[['value', properties[p_name]]]);
                        print 'modified '+ p;
    #end if res_prop_set

    print "======Created datasource====="
    print AdminConfig.showall(ds)
    print "============================="

    return ds

#end create_data_source

#------------------------------------------------------test_data_source
# Tests the connection to a DataSource.  The datasource_name
# passed in has to be saved in the configuration before
# attempting to run testConnection.
#
# RETURNS true if test was successful, otherwise false.
#------------------------------------------------------
def test_data_source(cell_name, jdbc_provider, datasource_name):
    ds=AdminConfig.getid('/Cell:%s/JDBCProvider:%s/DataSource:%s/' % (cell_name,jdbc_provider,datasource_name))
    if not ds:
        print "ERROR (test_data_source): datasource not found. cell_name=%s jdbc_provider=%s datasource_name=%s" % (cell_name, jdbc_provider, datasource_name)
        return 0;
    #end if not ds:

    try:
        test_result=AdminControl.testConnection(ds)
        print 'Test connection for datasource "%s" was successful. (%s)' % (ds, test_result)
        return 1;
    except:
        print 'ERROR (test_data_source): An attempt to connect to datasource "%s" has failed. See below for exception information--' % (ds)
        print sys.exc_info();
        return 0;
    #end try

##end test_data_source

#------------------------------------------------------create_mq_cf
def create_mq_cf(cell_name, mq_cf, conn_pool_params=None, session_pool_params=None):
    err_msg="ERROR (%s): Not creating MQ queue connection factory." % 'create_mq_cf'

    mq_cf_name         =mq_cf.get('name')
    mq_cf_jndi         =mq_cf.get('jndi')

    if not mq_cf_name:
        print "%s name not found in mq_cf argument" % (err_msg)
        return 0;
    ####end if not mq_cf_name

    if not mq_cf_jndi:
        print "%s jndi not found in mq_cf argument. %s" % (err_msg,mq_cf_name)
        return 0;
    ####end if not mq_cf_jndi

    mq_cf_desc         =mq_cf.get('description');
    mq_cf_auth_pref    =mq_cf.get('authMechanismPreference');
    mq_cf_xa_enabled   =mq_cf.get('XAEnabled');
    mq_cf_host         =mq_cf.get('host')
    mq_cf_port         =mq_cf.get('port');
    mq_cf_channel      =mq_cf.get('channel')
    mq_cf_transport    =mq_cf.get('transportType');
    mq_cf_msg_retention=mq_cf.get('msgRetention');

    # set defaults
    if not mq_cf_desc         : mq_cf_desc         =mq_cf_name+' MQ Queue ConnectionFactory';
    if not mq_cf_auth_pref    : mq_cf_auth_pref    ='BASIC_PASSWORD';
    if not mq_cf_xa_enabled   : mq_cf_xa_enabled   ='true';
    if not mq_cf_port         : mq_cf_port         ='1414';
    if not mq_cf_transport    : mq_cf_transport    ='CLIENT';
    if not mq_cf_msg_retention: mq_cf_msg_retention='true';

    # connection pool settings
    # ~~~~~~~~~~~~~~~~~~~~~~~~
    mq_cf_cp_timeout=mq_cf_cp_maxconn=mq_cf_cp_minconn=mq_cf_cp_reaptime=None;
    mq_cf_cp_unusedtimeout=mq_cf_cp_agedtimeout=mq_cf_cp_purgepolicy=None;
    if conn_pool_params:
        mq_cf_cp_timeout      =conn_pool_params.get('connectionTimeout');
        mq_cf_cp_maxconn      =conn_pool_params.get('maxConnections');
        mq_cf_cp_minconn      =conn_pool_params.get('minConnections');
        mq_cf_cp_reaptime     =conn_pool_params.get('reapTime');
        mq_cf_cp_unusedtimeout=conn_pool_params.get('unusedTimeout');
        mq_cf_cp_agedtimeout  =conn_pool_params.get('agedTimeout');
        mq_cf_cp_purgepolicy  =conn_pool_params.get('purgepolicy');

    # session pool settings
    # ~~~~~~~~~~~~~~~~~~~~~~~~
    mq_cf_sp_timeout=mq_cf_sp_maxconn=mq_cf_sp_minconn=mq_cf_sp_reaptime=None;
    mq_cf_sp_unusedtimeout=mq_cf_sp_agedtimeout=mq_cf_sp_purgepolicy=None;
    if session_pool_params:
        mq_cf_sp_timeout      =session_pool_params.get('connectionTimeout');
        mq_cf_sp_maxconn      =session_pool_params.get('maxConnections');
        mq_cf_sp_minconn      =session_pool_params.get('minConnections');
        mq_cf_sp_reaptime     =session_pool_params.get('reapTime');
        mq_cf_sp_unusedtimeout=session_pool_params.get('unusedTimeout');
        mq_cf_sp_agedtimeout  =session_pool_params.get('agedTimeout');
        mq_cf_sp_purgepolicy  =session_pool_params.get('purgepolicy');

    # get scope
    # ~~~~~~~~~
    if not cell_name: cell_name=AdminControl.getCell();
    scope="/Cell:"+cell_name;


    # find 'WebSphere MQ JMS Provider'
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    mq_jms_provider=None;
    for jms_provider in AdminConfig.getid(scope+'/JMSProvider:/').split(line_sep):
        if "WebSphere MQ JMS Provider"==AdminConfig.showAttribute(jms_provider,'name'):
            mq_jms_provider=jms_provider;
            break;
    #end for

    # 'WebSphere MQ JMS Provider' not found
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if not mq_jms_provider:
        print "%s MQ JMS Provider not found in %s scope." % (err_msg,scope)
        return 0;

    print 'MQ JMS Provider %s found in "%s" scope' % (mq_jms_provider,scope);

    # find mq provider template
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~
    mq_cf_template_name=mq_cf.get('template')
    mq_cf_template=None;
    if mq_cf_template_name:
        mq_cf_template = AdminConfig.listTemplates("MQQueueConnectionFactory", mq_cf_template_name).split(line_sep)[0]
        if not mq_cf_template:
            print '%s Could not find a MQQueueConnectionFactory template using "%s".' % (err_msg,ds_template_name)
            return 0;
        ####end if
    ####end if mq_cf_template_name

    # check if mq_cf already exists
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    mq_jms_provider_name=AdminConfig.showAttribute(mq_jms_provider,'name');
    existing_mq_cfs=AdminConfig.getid(scope + "/JMSProvider:%s/MQQueueConnectionFactory:/" % mq_jms_provider_name)
    for existing_mq_cf in existing_mq_cfs.split(line_sep):
        if mq_cf_name==AdminConfig.showAttribute(existing_mq_cf,'name'):
            print '%s "%s" MQQueueConnectionFactory alreasy exists.' % (err_msg,mq_cf_name)
            return 0;
        ####end if
    ####end for

    # create MQQueueConnectionFactory
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    mq_cf_attrs=[]
    mq_cf_attrs.append(['name',mq_cf_name])
    mq_cf_attrs.append(['jndiName',mq_cf_jndi])
    if mq_cf_desc         : mq_cf_attrs.append(['description'            ,mq_cf_desc])
    if mq_cf_auth_pref    : mq_cf_attrs.append(['authMechanismPreference',mq_cf_auth_pref])
    if mq_cf_xa_enabled   : mq_cf_attrs.append(['XAEnabled'              ,mq_cf_xa_enabled])
    if mq_cf_host         : mq_cf_attrs.append(['host'                   ,mq_cf_host])
    if mq_cf_port         : mq_cf_attrs.append(['port'                   ,mq_cf_port])
    if mq_cf_channel      : mq_cf_attrs.append(['channel'                ,mq_cf_channel])
    if mq_cf_transport    : mq_cf_attrs.append(['transportType'          ,mq_cf_transport])
    if mq_cf_msg_retention: mq_cf_attrs.append(['msgRetention'           ,mq_cf_msg_retention])

    mqcf=None;
    if mq_cf_template:
        print 'Creating MQQueueConnectionFactory using template %s \n\tjms_provider=%s \n\tattrs=%s\n' % (mq_cf_template,mq_jms_provider,mq_cf_attrs)
        mqcf=AdminConfig.createUsingTemplate('MQQueueConnectionFactory', mq_jms_provider, mq_cf_attrs, mq_cf_template)
    else:
        print 'Creating MQQueueConnectionFactory without using template. \n\tjms_provider=%s, \n\tattrs=%s\n' % (mq_cf_template,mq_jms_provider,mq_cf_attrs)
        mqcf=AdminConfig.create('MQQueueConnectionFactory', mq_jms_provider, mq_cf_attrs)

    # ConnectionPool
    #~~~~~~~~~~~~~~~~~
    conn_pool_attrs=[]
    if mq_cf_cp_timeout      : conn_pool_attrs.append(['connectionTimeout',mq_cf_cp_timeout]);
    if mq_cf_cp_maxconn      : conn_pool_attrs.append(['maxConnections'   ,mq_cf_cp_maxconn]);
    if mq_cf_cp_minconn      : conn_pool_attrs.append(['minConnections'   ,mq_cf_cp_minconn]);
    if mq_cf_cp_reaptime     : conn_pool_attrs.append(['reapTime'         ,mq_cf_cp_reaptime]);
    if mq_cf_cp_unusedtimeout: conn_pool_attrs.append(['unusedTimeout'    ,mq_cf_cp_unusedtimeout]);
    if mq_cf_cp_agedtimeout  : conn_pool_attrs.append(['agedTimeout'      ,mq_cf_cp_agedtimeout]);
    if (mq_cf_cp_purgepolicy) and (mq_cf_cp_purgepolicy in ['EntirePool', 'FailingConnectionOnly']):
                               conn_pool_attrs.append(['purgePolicy'      ,mq_cf_cp_purgepolicy ]);

    if conn_pool_attrs:
        print "Creating connection pool... \n\tMQQueueConnectionFactory=%s \n\tattrs=%s\n" % (mqcf,conn_pool_attrs)
        AdminConfig.create('ConnectionPool',mqcf,conn_pool_attrs,"connectionPool");

    # session pool
    # ~~~~~~~~~~~~
    session_pool_attrs=[]
    if mq_cf_sp_timeout      : session_pool_attrs.append(['connectionTimeout',mq_cf_sp_timeout]);
    if mq_cf_sp_maxconn      : session_pool_attrs.append(['maxConnections'   ,mq_cf_sp_maxconn]);
    if mq_cf_sp_minconn      : session_pool_attrs.append(['minConnections'   ,mq_cf_sp_minconn]);
    if mq_cf_sp_reaptime     : session_pool_attrs.append(['reapTime'         ,mq_cf_sp_reaptime]);
    if mq_cf_sp_unusedtimeout: session_pool_attrs.append(['unusedTimeout'    ,mq_cf_sp_unusedtimeout]);
    if mq_cf_sp_agedtimeout  : session_pool_attrs.append(['agedTimeout'      ,mq_cf_sp_agedtimeout]);
    if (mq_cf_sp_purgepolicy) and (mq_cf_sp_purgepolicy in ['EntirePool', 'FailingConnectionOnly']):
                               session_pool_attrs.append(['purgePolicy'      ,mq_cf_cp_purgepolicy ]);

    if session_pool_attrs:
        print "Creating session pool... \n\tMQQueueConnectionFactory=%s \n\tattrs=%s" % (mqcf,session_pool_attrs)
        AdminConfig.create('ConnectionPool',mqcf,session_pool_attrs,"sessionPool");

    print "+========Created MQQueueConnectionFactory %s" % mqcf
    print AdminConfig.showall(mqcf)
    print "+=============================================+"

    return mqcf;

#####end create_mq_cf######

#--------------------------------------create_shared_library
def create_shared_library(cell_name, shared_lib_name, jar_files, description='', overwrite=1):
    err_msg='ERROR (create_shared_library): NOT creating shared library.'

    if not shared_lib_name:
        print err_msg + " no shared_lib_name"
        return 0;

    if not cell_name: cell_name=AdminControl.getCell()
    scope='/Cell:'+AdminControl.getCell()+ '/'

    # check if exists
    shared_lib_id=AdminConfig.getid('%sLibrary:%s/' % (scope,shared_lib_name))
    if shared_lib_id:
        if not overwrite:
            print '%s shared lib "%s" already exists in "%s" scope' % (err_msg, shared_lib_id,scope)
            return 0;
        else:
            print 'Shared lib "%s" already exists in "%s" scope. overwriting...' % (shared_lib_id,scope)
        ##end if not overwrite
    ##end if shared_lib_id

    # validate jar files
    classpath=''
    for jar in remove_duplicates(jar_files):
        if not is_file_exists(jar):
            print err_msg;
            return 0;
        else:
            classpath=classpath+jar+classpath_sep
        ##end if
    ##end for

    # creating library
    lib_attrs=[]
    lib_attrs.append([ 'name'        , shared_lib_name ])
    lib_attrs.append([ 'classPath'   , classpath       ])
    lib_attrs.append([ 'description' , description     ])

    if shared_lib_id:
        print 'Removing existing shared library %s' % (shared_lib_id)
        AdminConfig.remove(shared_lib_id);

    scope_id=AdminConfig.getid(scope)
    print 'Creating shared library "%s" \n\tscope=%s \n\tattrs=%s'  % (shared_lib_name, scope_id,lib_attrs)
    lib=AdminConfig.create('Library', scope_id, lib_attrs)

    print '==========Created shared library %s' % lib
    print AdminConfig.showall(lib)
    print '================================================'

    return lib;

##end def create_shared_library


#--------------------------------------update_shared_lib
def update_shared_lib(cell_name, shared_lib_name, jar_files, description='', create=1):
    err_msg='ERROR (update_shared_lib): NOT updating shared library.'

    if not shared_lib_name:
        print err_msg + " no shared_lib_name"
        return 0;

    if not cell_name: cell_name=AdminControl.getCell()
    scope='/Cell:'+AdminControl.getCell()+ '/'

    # check if exists
    shared_lib_id=AdminConfig.getid('%sLibrary:%s/' % (scope,shared_lib_name))
    if not shared_lib_id:
        if create:
            print 'Shared lib "%s" does not exist. Creating...\n\tcell_name=%s\n\tlib_name=%s\n\tjar_file=%s\n\tdescription=%s' % (cell_name, shared_lib_name, jar_files, description)
            return create_shared_library(cell_name, shared_lib_name, jar_files, description)
        else:
            print '%s Shared lib "%s" does not exist.' % (err_msg)
        #end if
    #end if

    # updating library
    lib_attrs=[]

    if jar_files: # if any
        existing_jars =AdminConfig.showAttribute(shared_lib_id,'classPath').split(classpath_sep)
        jar_files.extend(existing_jars); # remember extend is 'addAll' append is 'add'
        # check files, perpare classpath string
        classpath=''
        for jar in remove_duplicates(jar_files):
            if not is_file_exists(jar):
                print err_msg;
                return 0;
            else:
                classpath=classpath+jar+classpath_sep
            ##end if
        ##end for
        lib_attrs.append(['classPath', classpath])
    ##end if jar_files

    existing_desc=AdminConfig.showAttribute(shared_lib_id,'description')
    if (description) and (description!=existing_desc):
        lib_attrs.append([ 'description', description])
    ##end if (description)

    if not lib_attrs:
        print '%s no attributes to update. "%s"'  % (err_msg,shared_lib_name)
        return 0;
    ##end if not lib_attrs

    print 'Updating shared library "%s" \n\tattrs=%s'  % (shared_lib_id,lib_attrs)
    AdminConfig.modify(shared_lib_id, lib_attrs)

    print '==========Updated shared library %s' % shared_lib_id
    print AdminConfig.showall(shared_lib_id)
    print '================================================'

    return 1;

##end def update_shared_lib

#--------------------------------------remove_shared_lib
def remove_shared_lib(cell_name, shared_lib_name):
    err_msg='ERROR (remove_shared_lib): NOT removing shared library.'

    if not shared_lib_name:
        print err_msg + " no shared_lib_name"
        return 0;
    ##end if not shared_lib_name

    if not cell_name: cell_name=AdminControl.getCell()
    scope='/Cell:'+AdminControl.getCell()+ '/'

    shared_lib_id=AdminConfig.getid('%sLibrary:%s/' % (scope,shared_lib_name))
    if not shared_lib_id:
        print '%s Shared lib "%s" not found.' % (err_msg, shared_lib_name)
        return 0;
    ##end if not shared_lib_id

    print 'Removing shared lib "%s"' % (shared_lib_id)
    ret=AdminConfig.remove(shared_lib_id)
    print 'Shared lib "%s" removed successfully.' % (shared_lib_id)

    return 1;

##end def remove_shared_lib

#--------------------------------------validate_shared_lib
# validates
#    1. if shared lib exists
#    2. if it has all the jar files specified in jar_files arg
#    3. if it does not have jar files more then specified in jar_files arg
#    4. if all the files in shared lib exist and readable
#---------------------------------------------------------
def validate_shared_lib(cell_name, shared_lib_name, jar_files):
    err_msg='ERROR (validate_shared_lib): NOT validating shared library.'
    validation_err_msg='ERROR (validate_shared_lib):'

    if not shared_lib_name:
        print err_msg + " no shared_lib_name"
        return 0;
    ##end if not shared_lib_name

    if not cell_name: cell_name=AdminControl.getCell()
    scope='/Cell:'+AdminControl.getCell()+ '/'

    shared_lib_id=AdminConfig.getid('%sLibrary:%s/' % (scope,shared_lib_name))
    if not shared_lib_id:
        print '%s Shared lib "%s" not exists.' % (validation_err_msg, shared_lib_name)
        return 0;
    ##end if not shared_lib_id

    validation_errors=0;

    existing_jars =AdminConfig.showAttribute(shared_lib_id,'classPath').split(classpath_sep)

    # first check if all the files in jar_files are in existing_jars
    for jar in jar_files:
        if not is_file_exists(jar):
            validation_errors = validation_errors + 1;
        elif jar not in existing_jars:
            print '%s Jar file "%s" not exists in shared lib "%s"' % (validation_err_msg, jar, shared_lib_id)
            validation_errors = validation_errors + 1;
        ##end if
    ##end for

    # then check if existing_jars have more files then jar_files
    for existing_jar in existing_jars:
        if not is_file_exists(existing_jar):
            validation_errors = validation_errors + 1;
        elif existing_jar not in jar_files:
            print '%s Jar file "%s" not needed in shared lib "%s"' % (validation_err_msg, existing_jar, shared_lib_id)
            validation_errors = validation_errors + 1;
        ##end if
    ##end for

    if not validation_errors:
        print 'shared lib "%s" is valid.' % (shared_lib_id)
    else:
        print 'shared lib "%s" is NOT valid.' % (shared_lib_id)

    return not (validation_errors); # returns true if no validation errors

## end validate_shared_lib

#--------------------------------------set_server_level_shared_lib
def set_server_level_shared_lib(server_name, shared_lib_name, properties={}):

    err_msg='ERROR (set_server_level_shared_lib): NOT setting server level shared lib.'

    if not server_name:
        print err_msg +' no server_name'
        return 0;

    if not shared_lib_name:
        print err_msg +' no shared_lib_name'
        return 0;

    server_id=AdminConfig.getid('/Server:%s/' % (server_name))
    if not server_id:
        print '%s server "%s" not exists.' % (err_msg,server_name)
        return 0;

    app_server=AdminConfig.list('ApplicationServer', server_id)
    if not app_server:
        print '%s application server "%s" not exists.' % (err_msg,server_id)
        return 0;

    # get existing classloader
    classloader=AdminConfig.showAttribute(app_server,'classloaders')
    classloader=classloader[1:len(classloader)-1]
    if classloader:
        classloader=classloader.split()[0] # get first one
        # check if lib exists
        libraries=AdminConfig.showAttribute(classloader,"libraries")
        libraries=libraries[1:len(libraries)-1]
        for lib in libraries.split():
            lib_name=AdminConfig.showAttribute(lib,"libraryName")
            if shared_lib_name==lib_name:
                if not overwrite:
                    print '%s Shared library "%s" already exist.' % (err_msg,lib)
                    return 0;
            ##end if shared_lib_name==lib_name:
        ##end for lib in libraries.split():
    ##end if classloader:

    if not classloader: # create new one
        mode=properties.get('mode')
        if not mode: mode='PARENT_FIRST'
        print 'Creating classloader. server=%s mode=%s' % (app_server,mode)
        new_classloader=AdminConfig.create('Classloader', app_server, [['mode',  mode]])
        classloader=new_classloader
    ##end if not classloader

    lib_attrs=[]
    lib_attrs.append(['libraryName', shared_lib_name])
    sharedClassloader=properties.get('sharedClassloader')
    if not sharedClassloader: sharedClassloader='true'
    lib_attrs.append(['sharedClassloader', sharedClassloader])

    print 'Adding library to classloader.\n\tclassloader=%s \n\tlibrary=%s ' % (classloader, lib_attrs)
    new_lib=AdminConfig.create('LibraryRef', classloader, lib_attrs)

    print '==========Shared lib set on server. %s' % (new_lib)
    print AdminConfig.showall(new_lib)
    print '=================================================='

##end set_server_level_shared_lib

#----------------------------------update_orb_service_settings
def update_orb_service_settings(server_id, orb_service_settings, orb_thread_pool_settings={}):
    err_msg='ERROR(update_orb_service_settings): NOT updating orb service settings for: %s ' % server_id;

    orb=AdminConfig.list('ObjectRequestBroker', server_id)

    enable                =orb_service_settings.get('enable'                )
    requestTimeout        =orb_service_settings.get('requestTimeout'        )
    requestRetriesCount   =orb_service_settings.get('requestRetriesCount'   )
    requestRetriesDelay   =orb_service_settings.get('requestRetriesDelay'   )
    connectionCacheMaximum=orb_service_settings.get('connectionCacheMaximum')
    connectionCacheMinimum=orb_service_settings.get('connectionCacheMinimum')
    commTraceEnabled      =orb_service_settings.get('commTraceEnabled'      )
    locateRequestTimeout  =orb_service_settings.get('locateRequestTimeout'  )
    forceTunnel           =orb_service_settings.get('forceTunnel'           )
    noLocalCopies         =orb_service_settings.get('noLocalCopies'         )

    orb_attrs=[]
    if enable                : orb_attrs.append(['enable'                ,enable                ])
    if requestTimeout        : orb_attrs.append(['requestTimeout'        ,requestTimeout        ])
    if requestRetriesCount   : orb_attrs.append(['requestRetriesCount'   ,requestRetriesCount   ])
    if requestRetriesDelay   : orb_attrs.append(['requestRetriesDelay'   ,requestRetriesDelay   ])
    if connectionCacheMaximum: orb_attrs.append(['connectionCacheMaximum',connectionCacheMaximum])
    if connectionCacheMinimum: orb_attrs.append(['connectionCacheMinimum',connectionCacheMinimum])
    if commTraceEnabled      : orb_attrs.append(['commTraceEnabled'      ,commTraceEnabled      ])
    if locateRequestTimeout  : orb_attrs.append(['locateRequestTimeout'  ,locateRequestTimeout  ])
    if forceTunnel           : orb_attrs.append(['forceTunnel'           ,forceTunnel           ])
    if noLocalCopies         : orb_attrs.append(['noLocalCopies'         ,noLocalCopies         ])

    #print 'orb_attrs=%s' % orb_attrs

    # Thread Pool Settings
    # --------------------
    thread_pool_inactivityTimeout=orb_thread_pool_settings.get('inactivityTimeout')
    thread_pool_isGrowable       =orb_thread_pool_settings.get('isGrowable'       )
    thread_pool_maximumSize      =orb_thread_pool_settings.get('maximumSize'      )
    thread_pool_minimumSize      =orb_thread_pool_settings.get('minimumSize'      )

    thread_pool_attrs=[]
    if thread_pool_inactivityTimeout: thread_pool_attrs.append(['inactivityTimeout',thread_pool_inactivityTimeout])
    if thread_pool_isGrowable       : thread_pool_attrs.append(['isGrowable'       ,thread_pool_isGrowable       ])
    if thread_pool_maximumSize      : thread_pool_attrs.append(['maximumSize'      ,thread_pool_maximumSize      ])
    if thread_pool_minimumSize      : thread_pool_attrs.append(['minimumSize'      ,thread_pool_minimumSize      ])

    #print 'thread_pool_attrs=%s' % thread_pool_attrs

    if orb_attrs:
        print 'Updating ORB service %s with attributes %s ' % (orb, orb_attrs)
        AdminConfig.modify(orb, orb_attrs)
        print '=====ORB service updated'
    #end if orb_attrs

    if thread_pool_attrs:
        orb_th_pool=AdminConfig.showAttribute(orb,'threadPool')
        print 'Updating ORB Service Thread Pool %s with attributes %s ' % (orb_th_pool, thread_pool_attrs)
        AdminConfig.modify(orb_th_pool, thread_pool_attrs)
        print '=====ORB Service Thread Pool updated.'
        print AdminConfig.showall(orb_th_pool);
        print '=======================================';
    #end if thread_pool_attrs

    return orb;

##end update_orb_service_settings


#--------------------------------------is_file_exists
def is_file_exists(file_name):
    err_msg='ERROR (is_file_exists): '
    file=java.io.File(file_name);

    if not file.exists():
        print '%s File "%s" does not exists' % (err_msg,file_name)
        return 0;

    if not file.isFile():
        print '%s "%s" is not a file' % (err_msg,file_name)
        return 0;

    if not file.canRead():
        print '%s File "%s" is not readable, check permissions.' % (err_msg,file_name)
        return 0;

    return 1;
##end def is_file_exists

#--------------------------------------remove_duplicates
def remove_duplicates(list):
    unique_list=[]
    for x in list:
        if x not in unique_list:
            unique_list.append(x)
    return unique_list;
##end def remove_duplicates

#--------------------------------------save
is_config_saved=0 # flag to remember we have saved config changes, node sync uses it

def save():
    if not AdminConfig.hasChanges():
        print('save: Unsaved configuration changes do not exist.')
        return 0;
    else:
        print('save: Unsaved configuration changes exist')

    yes = ask_user("Save configuration")
    if not yes:
        return 0;

    print('save: Saving configuration changes ...')
    AdminConfig.save()
    print('save: Configuration changes saved.')
    is_config_saved=1;

    return 1

##end def save

#------------------------------------------node_sync
# node_sync - Synchronize a node's repository with the cell repository.
#             This operation returns only after the synchronization is complete.
#             The return value indicates whether or not the operation was attempted.
#---------------------------------------------------
def node_sync(list_of_node_names):

    if not is_config_saved:
        return; # nothing saved, nothing to sync

    err=0;
    for node_name in list_of_node_names:
        node=AdminConfig.getid('/Node:%s/' % node_name)
        if not node:
            print 'node_sync: node "%s" doesnot exists' % (node_name);
            continue;

        sync_obj=AdminControl.completeObjectName('type=NodeSync,node=%s,*' % (node_name));
        retval=AdminControl.invoke(sync_obj, 'isNodeSynchronized').lower()
        if 'true' != retval:
            print('node_sync: node synchronization is not required (%s). node=%s' % (retval, node))
            continue;
        else:
            print('node_sync: node synchronization is required (%s). node=%s' % (retval, node))

        print('node synchronization begin... node=%s' % (node))
        retval=AdminControl.invoke(sync_obj, 'sync').lower();
        if retval=='true':
            print('node_sync: node synchronization completed successfully (%s). node=%s' % (retval, node))
        else:
            print('node_sync: node sync is NOT completed successfully (%s). cell=%s node=%s' % (retval, node))
            err=err+1;

    return err;
##end def node_sync

#------------------------------------------ask_user
# ask_user - asks a question on the console.
#            returns 1 if answer is 'yes', otherwise 0.
#-------------------------------------------
def ask_user(question):
    msg="%s? (y/n) [n]: " % question;
    response = raw_input(msg)
    response = response.lower()
    while response != 'y' and response != 'n' and response != '':
        response = raw_input(msg)
        response = response.lower()

    return (response == 'y');

##end def ask_user

#------------------------------------------exit
# python sys.exit method started throwing exception in recent version.
#
def exit(msg):
    try:
        sys.exit(msg)
    except:
        print '----'
        print msg
##def exit

#------------------------------------------show_menu
# if returns true then continue otherwise exit
#
def show_menu(next_step=None):
    if quite:
        return 1; # if we are quite always continue

    valid_responses=['0','1','2']
    if not next_step: valid_responses=['0','1']

    print ''
    print '\t*************************************'
    print '\tPress 0 to EXIT WITHOUT saving'
    print '\tPress 1 to EXIT AFTER   saving'
    if next_step: print '\tPress 2 to CONTINUE to next step: %s' % next_step
    print '\t*************************************'

    response = raw_input('\tENTER RESPONSE: ')
    while response not in valid_responses:
        response = raw_input('\tENTER RESPONSE: ')

    if '0' == response:
        if AdminConfig.hasChanges():
            print 'Changes have been made to the configuration, but these changes have not been saved.'
            if ask_user('Are you sure you want to quit without saving'):
                return 0
            else: # ask again
                return show_menu(next_step)
        else:
            return 0
    elif '1' == response:
        save()
        return 0
    else:
        return 1

##end def show_menu