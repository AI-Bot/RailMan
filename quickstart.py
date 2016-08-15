import sys,json,requests,time,urllib,re
from wit import Wit
#railway_api='paxbk6508'
#railway_api='xfagr5086'
railway_api='hqvyn6929'
if len(sys.argv) != 2:
    print('usage: python ' + sys.argv[0] + ' <wit-token>')
    exit(1)
access_token = sys.argv[1]
#hi
#testing
# Quickstart example
# See https://wit.ai/ar7hur/Quickstart
def fetch_stnname(request):
    context = request['context']
    entities = request['entities']
    userinp = first_entity_value(entities, 'location').upper()
    code=stn_name_to_code(userinp)
    if code=='':
        context['stnname'] = 'Not found'
        return context
    context['stnname']=code
    return context

def first_entity_value(entities, entity):
    if entity not in entities:
        return None
    val = entities[entity][0]['value']
    if not val:
        return None
    return val['value'] if isinstance(val, dict) else val

def send(request, response):
    print(response['text'])

def get_forecast(request):
    context = request['context']
    entities = request['entities']

    loc = first_entity_value(entities, 'location')

    context['loc']=loc
    if loc:
        context['forecast'] = 'sunny'
    else:
        context['missingLocation'] = True
        if context.get('forecast') is not None:
            del context['forecast']
    return context

def fetch_statuspnr(request):
    context = request['context']
    entities = request['entities']
    pnr=str(first_entity_value(entities,'number'))
    pnr2 = first_entity_value(entities, 'location')
    if pnr=='None':
        #print('no pnr from number')
        num=(re.findall(r'\b\d+\b', str(pnr2)))
        if len(num)>0:
            pnr=num[0]
        else:
            context['missingLocation']='yes'
            return context

    url = 'http://api.railwayapi.com/pnr_status/pnr/' + str(pnr) + '/apikey/' + railway_api + '/'
    parsed_json = json.loads(requests.get(url).text)
    error = (parsed_json['error'])
    if str(error).lower() == 'true':
        context['pnr_status']='Error: Invalid/Old PNR No.'
        return context
    from_stn = parsed_json['from_station']
    des_stn = parsed_json['reservation_upto']
    date_of_jrny = parsed_json['doj']
    total_passengers = parsed_json['total_passengers']
    passengers = parsed_json['passengers']
    status_list = '\nFROM ' + from_stn['name'] + ' TO ' + des_stn['name'] + ' \nDate of Journey ' + date_of_jrny + '\n'
    for x in range(total_passengers):
        passenger_data = passengers[total_passengers - 1]
        status_list = status_list + ' 1. ' + str(passenger_data['no']) + ' Status ' + passenger_data['current_status'] + '  ->' + passenger_data['booking_status'] + '\n'
        total_passengers = total_passengers - 1
    context['pnr_status']=status_list
    return context

def fetch_statustrain(request):
    context = request['context']
    entities = request['entities']
    trainno=str(first_entity_value(entities,'number'))
    trainno2 = str(first_entity_value(entities, 'location'))
    if trainno=='None':
        num = (re.findall(r'\b\d+\b', str(trainno2)))
        if len(num) > 0:
            trainno = num[0]

    print(trainno)

    print(trainno)
    #print(trainno2)
    url = 'http://api.railwayapi.com/live/train/'+str(trainno)+'/doj/'+str(time.strftime("%Y%m%d"))+'/apikey/'+railway_api+'/'
    parsed_json = json.loads(requests.get(url).text)
    if str(parsed_json['response_code'])=='204':
        context['train_status'] = 'Invalid train no./Server not responding'
        return context

    if str(parsed_json['response_code']) == '510':
        context['train_status'] = parsed_json['error']
        return context
    train_status = parsed_json['position']
    context['train_status'] = train_status
    return context


def fetch_stncode(request):
    context = request['context']
    entities = request['entities']
    userinp=str(first_entity_value(entities,'location')).upper()
    #print(userinp)
    name=stn_code_name(userinp)
    if name=='':
        context['stncode'] = "Wrong station code or enter in code capital letters"
        return context
    context['stncode'] = name
    return context

def stn_code_name(userinp):
    url = 'http://api.railwayapi.com/code_to_name/code/' + str(userinp) + '/apikey/' + railway_api + '/'
    parsed_json = json.loads(requests.get(url).text)
    stations = parsed_json['stations']
    l_of_s = len(stations)
    searchobj = userinp
    name_code = ''
    while l_of_s > 0:
        data = stations[l_of_s - 1]
        if data['code'] == searchobj:
            name_code = (data['fullname'])
            break
        l_of_s = l_of_s - 1
    return name_code



def stn_name_to_code(userinp):
    url = 'http://api.railwayapi.com/name_to_code/station/' + userinp + '/apikey/' + railway_api + '/'
    parsed_json = json.loads(requests.get(url).text)
    stations = parsed_json['stations']
    l_of_s = len(stations)
    searchobj = userinp
    name_code = ''
    while l_of_s > 0:
        data = stations[l_of_s - 1]
        if data['fullname'] == searchobj:
            name_code = (data['code'])
            break
        l_of_s = l_of_s - 1
    return name_code


def fetch_train(requests):
    context = requests['context']
    entities = requests['entities']
    data = {'orgin': '', 'dest': '', "date": ''}
    #data=context['missingDate']
    dt = first_entity_value(entities, 'datetime')
    print(dt)
    dest = stn_name_to_code(first_entity_value(entities, 'destination').upper())
    origin = stn_name_to_code(first_entity_value(entities, 'origin').upper())
    if dest=='':
        context['train_list']="Wrong/Invalid destination name"
        return context
    elif origin=='':
        context['train_list']='Wrong/Invalid source name'
        return context
    print(origin)
    print(dest)
    if dt==None:

        data['orgin']=origin
        data['dest']=dest
        context['missingDate']=data
        return context
    month = dt[5:7]
    date = dt[8:10]
    url = 'http://api.railwayapi.com/between/source/'+str(origin)+'/dest/'+str(dest)+'/date/'+str(date)+'-'+str(month)+'/apikey/'+railway_api+'/'
    train_list=train_btw_stn(url)
    context['train_list']=train_list
    return context


def train_btw_stn(url):
    parsed_json = json.loads(requests.get(url).text)
    a = parsed_json['train']
    train_list = 'Train name   DEPT  ARVL \n'
    for x in range(len(a)):
        b = a[x]
        train_list = train_list + b['name'] + ' ' + b['src_departure_time'] + ' ' + b['dest_arrival_time'] + '\n'
    return train_list

def fetch_cancelled(request):
    context = request['context']
    entities = request['entities']
    dateinp=str(first_entity_value(entities, 'datetime'))
    url='http://api.railwayapi.com/cancelled/date/'+dateinp[8:10]+'-'+dateinp[5:7]+'-'+dateinp[0:4]+'/apikey/'+railway_api+'/'
    parsed_json = json.loads(requests.get(url).text)
    trains = parsed_json['trains']
    cancel_train = ''
    for x in range(len(trains)):
        data = trains[x]
        train = data['train']
        name = train['name']
        num = train['number']
        cancel_train = cancel_train + name + ' ' + num + '\n'
    context['cancel_train']=cancel_train
    return context
def fetch_reschedule(request):
    context = request['context']
    entities = request['entities']
    dateinp=str(first_entity_value(entities,'datetime'))
    #url = 'http://api.railwayapi.com/rescheduled/date/20-07-2016/apikey/paxbk6508/'
    url = 'http://api.railwayapi.com/rescheduled/date/' + dateinp[8:10] + '-' + dateinp[5:7] + '-' + dateinp[0:4] + '/apikey/' + railway_api + '/'
    parsed_json = json.loads(requests.get(url).text)
    trains = parsed_json['trains']
    reschleduled_train = ''
    for x in range(len(trains)):
        data = trains[x]
        name = data['name']
        num = data['number']
        reschleduled_train = reschleduled_train + name + ' ' + num + '\n'
    #print(reschleduled_train)
    context['reschedule_train']=str(reschleduled_train)
    return context

def fetch_route(request):
    context = request['context']
    entities = request['entities']
    trainno = str(first_entity_value(entities, 'number'))
    trainno2 = str(first_entity_value(entities, 'location'))
    if trainno == 'None':
        num = (re.findall(r'\b\d+\b', str(trainno2)))
        if len(num) > 0:
            trainno = num[0]

    if trainno==None:
        context['missingLocation']='yes'
        return context
    url = 'http://api.railwayapi.com/route/train/'+trainno+'/apikey/' + railway_api + '/'
    parsed_json = json.loads(requests.get(url).text)
    # route = parsed_json['route']
    reschleduled_train = ''

    tran_route = 'Station  ARVL  DEPT\n'
    for x in range(len(parsed_json['route'])):
        tran_route = tran_route + (parsed_json['route'][x]['fullname']) + ' ' + parsed_json['route'][x]['scharr'] + ' ' + parsed_json['route'][x]['schdep'] + '\n'
    context['train_route']=tran_route
    return context

actions = {
    'send': send,
    'getForecast': get_forecast,
    'fetch-statuspnr': fetch_statuspnr,
    'fetch-stncode': fetch_stncode,
    'fetch-stnname': fetch_stnname,
    'fetch-statustrain': fetch_statustrain,
    'fetch-train':fetch_train,
    'fetch-cancelled':fetch_cancelled,
    'fetch-reschedule':fetch_reschedule,
    }

client = Wit(access_token=access_token, actions=actions)
client.interactive()
