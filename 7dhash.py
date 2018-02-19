__title__       = '7dhash'
__version__     = '20180219.01'
__author__      = 'T Hendricks'
__description__ = 'Python scipt the pulls executed processes from tanium across 7 days in 7 queries'

#some of these may not be needed - it is my standard set for pytan things
import os,sys,csv,time,socket,json,getpass,pickle
from datetime import datetime, date, time, timedelta

#for use of pytan with jupyter - otherwise your output will be found in the console
jupyter_stdout = sys.stdout

#set where pytan be
pytan_loc = "/another/awesome/directory/pytan-2.2/lib"
#get pytan working
sys.path.append(pytan_loc)
import pytan
#set your console back to jupyter
sys.stdout = jupyter_stdout

#set where to store the pickles
pickle_dir='/some/pickle/dir/'
#pytan things to be set by the user
handler_args={}
kwargs = {}
handler_args['username'] = "tanium_user"
handler_args['host'] = "tanium.yourcompany.com"
handler_args['port'] = "443"
handler_args['password'] = getpass.getpass('Password: ')

#function to save pickle files
def save_obj(obj, name):
    with open(pickle_dir + name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

#function to load pickle files
def load_obj(name):
    with open(pickle_dir + str(name) + '.pkl', 'rb') as f:
        return pickle.load(f)

#the tanium call to grab md5s of the process hashes
def tanium_md5s(tanium_time):
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
    kwargs["sensors"] = [u'Trace Executed Process Hashes{TimeRange=absolute time range,AbsoluteTimeRange='+tanium_time+u',MaxResultsPerHost=1000}']
    #qualified request
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

#reformat the json to something more workable 
def format_hashes(pytan_out):
    #may be optimize with a dictionary comprehension but this is readable
    returned_dict = {}
    #row counter for the json returned
    row_num = 0
    
    #look throught the returned output - may be further optimized with enumerate call
    for line in pytan_out:
        #set the row name
        dict_row='row'+str(row_num)
        #grab the info if it exists
        try:
            #find the row number and the column number for the first entries in each - should work for this
            hash = md5s[row_num][dict_row][0]['column.values'][0]
            #md5 are 32 in length and have no spaces - there is actually and error that can be 32 in length
            if len(hash.split()[0]) == 32:
                returned_dict[hash] = [] # this can be set to other content, but the hash key is what i want
            #bump the row_num
            row_num += 1
        except:
            #bump the row_num - keeping the continue in case more to include in this function
            row_num += 1
            continue
    
    #give the dictionary back when done
    return returned_dict

#function to day results from 1 run and another run and combine into a single pickle file
def pickle_merge(pickle_file,new_dict):
    try:
        #grab the old
        old_md5s = load_obj(pickle_file)
    except:
        #make it empty if not there
        old_md5s = {}
    
    #print the old length
    print '... length of old md5s: '+str(len(old_md5s))
    
    #update the new into the old
    old_md5s.update(new_dict)
    
    #print the new length
    print '... length of new md5s: '+str(len(old_md5s))
    
    #save the pickle
    save_obj(old_md5s,pickle_file)

#empty dictionary for the run times
tanium_chain={}

#number of ms in a day
time_delta = 86400000
#current time in ms since epoch
current_time = int(datetime.now().strftime('%s')) * 1000
#last midnight
midnight = int(datetime.combine(date.today(), time.min).strftime('%s')) * 1000

#create a list of 7 days of time
for x in range(0,7):
    #start and end time - 1st day uses listings above
    start_time = midnight
    end_time = current_time
    #set a string for timeset
    day_num = 'md5s'+(datetime.now() - timedelta(days=x)).strftime('%Y%m%d')
    #in the dictionary - use the day as the key with the ms times as the value
    tanium_chain[day_num] = str(start_time)+'|'+str(end_time)
    #reset for the next loop
    current_time = midnight
    #reset for the next loop
    midnight = midnight - time_delta

#print out the chain
print tanium_chain

#let loose the kraken
for hashday in tanium_chain:
    print '----------------'
    print 'Working hashday'
    #make the call
    md5s = tanium_md5s(tanium_chain[hashday])
    #show the length
    print '...length hashes = '+str(len(md5s))
    #reformat the hashes
    formatted_hashes = format_hashes(md5s)
    #combine the pickles and write them to disk
    pickle_merge(hashday,formatted_hashes)
    print '... pickle file written as '+hashday
