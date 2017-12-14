#import the needed libraries
from urllib2 import Request, urlopen
import os,sys,csv,time,socket,json,getpass
from datetime import datetime

#import the pytan libraries - this is version 2.2
pytan_loc = "c:\\Python27\\pytan-2.2\lib"
sys.path.append(pytan_loc)
import pytan

#initialize the dictionaries
handler_args={}
kwargs = {}

#define function to grab the tanium trace query
def tanium_trace_destination(address):
    #get the handler working
    handler_args['loglevel'] = 1
    handler_args['debugformat'] = False
    handler_args['record_all_requests'] = True
    print "...CALLING: pytan.handler()"
    handler = pytan.Handler(**handler_args)
    
    #put the question together - this is filtered and qualified
    #the regex,output,localhost have to be placed manually
    kwargs["export_format"] = u'json'
    #multi sensor
    kwargs["sensors"] = [u'Computer Name',u'Trace Network Connections{TreatInputAsRegEx=0,OutputYesOrNoFlag=0,IncludeLocalhost=0,AbsoluteTimeRange='+tanium_time+u',DestinationIP='+address+u'}']
    #Relative time range example
    #kwargs["sensors"] = [u'Computer Name',u'Trace Network Connections{TreatInputAsRegEx=0,OutputYesOrNoFlag=0,IncludeLocalhost=0,TimeRange=unlimited,DestinationIP='+address+u'}']
    #qualified request
    kwargs["question_filters"] = [u'Trace Network Connections{TreatInputAsRegEx=0,OutputYesOrNoFlag=0,IncludeLocalhost=0,AbsoluteTimeRange='+tanium_time+u',DestinationIP='+address+u'},that contains:Connection attempted.']
    kwargs["qtype"] = u'manual'
    
    #make the call and wait
    print "...CALLING: handler.ask with args: {}".format(kwargs)
    response = handler.ask(**kwargs)
    
    #show the question as it would appear in the console - great for debugging
    print "...OUTPUT: Equivalent Question if it were to be asked in the Tanium Console: "
    print response['question_object'].query_text
    
    #if the dictionary has a question results convert this out to json
    if response['question_results']:
        # call the export_obj() method to convert response to CSV and store it in out
        export_kwargs = {}
        export_kwargs['obj'] = response['question_results']
        export_kwargs['export_format'] = 'json'
        out = handler.export_obj(**export_kwargs)
    
    #load out the json
    out_json = json.loads(out)
    
    #return the json from the function
    return out_json

#create a list of interesting domains
domain_list = ['whatismyip.akamai.com']
#initialize the ip address list
address_list = []
#create a result dictionary
result_dict = {}

#resolve the domains to addresses and put them in the list
for domain in domain_list:
    lookup = socket.gethostbyname(domain)
    address_list.append(lookup)

#get the ms epoch strings for tanium trace to work under absolute times based from present
#this is only 1 hr
tanium_time = str(int(time.time()) * 1000)+'|'+str(((int(time.time())) * 1000) - (3600 *1000))

#things used by the tanium call
handler_args['username'] = "your username" 
handler_args['host'] = "your hostname"
handler_args['port'] = "443"

#your password
handler_args['password'] = getpass.getpass('Password: ')

#iterate through the addresses and get the results in a dictionary of json stuffs
for address in address_list:
    result_dict[address] = tanium_trace_destination(address)

'''
for key,value in result_dict.iteritems():
    for row_item in value:
        for key,row_stuffs in row_item.iteritems():
            for items_in_row_stuffs in row_stuffs:
                print items_in_row_stuffs['column.display_name'],':',items_in_row_stuffs['column.values']
            print ""
'''
