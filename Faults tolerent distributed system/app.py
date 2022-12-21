"""
Some coding references: 
https://stackoverflow.com/questions/4906977/how-do-i-access-environment-variables-from-python
https://stackoverflow.com/questions/22878743/how-to-split-dictionary-into-multiple-dictionaries-fast
"""

import os
import sys
import requests
import time
from flask import Flask, request, make_response, jsonify, abort
from gevent.wsgi import WSGIServer
import json
import random
from itertools import islice
app = Flask(__name__)


# Initialize an empty data store
# The key/value pair stored in this assignment should include payload (vector clock) & timestamp
# eg: key:[value, payload, timestamp]
DS = {}

# Initialize an empty view store, and a length to keep track of # of nodes, and quorum constants

# in this assignment view would be a dictionary to store key-value pairs of both containers and their shard ids.
view = {}
all_nodes = []

IP_PORT = None
NUM_OF_VIEW = None
NUM_OF_SHARDS = None
NUM_OF_NODES = None

# Initialize array of keys and string of VC (not sure if it is necessary to be a global variable)
# to keep the indices consistent
# Not in a dictionary for the convenience of comparing LCs
# PAYLOAD[key] = 1
PAYLOAD = {}
TIMESTAMP = {}


# Set max size limit to 1MB (in bytes)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
maxVal = 1*1024*1024

def chunks(data, SIZE=10000):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}

##################
#
#	Payload operation
#
##################
def initializePayload(payload):
    vc = [0 for x in range(len(view))]
    stringVC = ''.join(str(index)+','for index in vc)
    return stringVC[:-1]

def updatePayload(payload, node):
    return initializePayload(payload)
    vc = payload.split(',')
    while len(vc) < len(view):
        vc.append(0)
    vc[node]=str(int(vc[node])+1)
    stringVC = ''.join(str(index)+','for index in vc)
    return stringVC[:-1]

def getIndex():
    i=0
    for node in view:
        i+=1
        if node == IP_PORT:
            return i

def chooseReplica(myPayload, replicaPayload, myTimestamp, replicaTimestamp):
    myVC = myPayload.split(',')
    reVC = replicaPayload.split(',')
    someGreater = False
    someLess = False
    for i in range(len(myVC)):
        if myVC == '' or reVC == '':
            continue
        if int(myVC[i]) > int(reVC[i]):
            someGreater = True
        elif int(myVC[i]) < int(reVC[i]):
            someLess = True
    if someGreater == someLess: # not compareable
        if myTimestamp > replicaTimestamp: #compare timestamp
            return False
        else: # it's either the same or less, so choose replica value
            return True
    elif someGreater: # all greater, choose my value
        return False
    elif someLess: # all less, choose replica value
        return True

def mergePayload(myPayload, replicaPayload):
    return initializePayload('a')
    myVC = myPayload.split(',')
    reVC = replicaPayload.split(',')
    maxVC = [max(index) for index in zip(myVC, reVC)]
    stringVC = ''.join(str(index)+','for index in maxVC)
    return stringVC[:-1]

##########################
#
# Shard operations
#
##########################
"""
Get confused :( When to do this?? when initialize the network?
A function to divide members
1. Get # of shards from ENV variables
2. Get containers from VIEW
	!!! convert view function may also need implementations
3. Divide them into different shards and store values of shard_ids to the view-map for corresponding keys
"""

"""
A function to change members in shards when there's only one node left in this shard
Rules: 
Better not changing the # of shards:
[A,B,C],[D,E]->Remove E->[A,B,C],[D]->[A,B],[C,D]
if all other shards remain only two nods, add the lonely one to any of them:
[A,B],[C,D],[E,F]->Remove F->[A,B],[C,D],[E]->[A,B],[C,D,E]

"""

"""
(Is this necessary if we write the same things to all nodes in the shard?)
A function to send its data to others when removing a node
"""
    
##########################
#
# New route endpoint /shard
#
##########################


@app.route('/shard/my_id', methods=['GET'])
def get_id():
    j = jsonify(id=view[IP_PORT])
    return reply(j, 200)


@app.route('/shard/all_ids', methods=['GET'])
def get_all_ids():
    global NUM_OF_SHARDS
    ids = []
    for i in range(0, NUM_OF_SHARDS):
        ids.append(str(i) )
    j = jsonify(result='Success', shard_ids=",".join(ids) )
    return reply(j, 200)

@app.route('/shard/members/<shard_id>', methods=['GET'])
def get_members(shard_id):
    members = getMembers( shard_id  )
    if len(members) < 1: # members is empty
        j = jsonify(result = "Error", msg="No shard with id %s"%shard_id)
        return reply(j, 404)
    else:
        j = jsonify(result = "Success", members = ",".join(members) )
        return reply(j, 200)

@app.route('/shard/count/<shard_id>', methods=['GET'])
def count(shard_id):
    if str(view[IP_PORT]) == shard_id:
        j = jsonify( result="Success", Count= str(len(DS)) )
        return reply(j, 200)
    members = getMembers(shard_id )
    for node in members:
        if node != IP_PORT:
            try:
                m = requests.get('http://%s/count/%s'%(str(node), str(shard_id) ), timeout=2 )
                if m.status_code != 404:
                    data = m.json()
                    count = data["Count"]
                    j = jsonify(result = "Success", Count = count)
                    return reply(j,200)
            except requests.exceptions.RequestException:
                # this replica is down
                print("TIMEOUT!!!!")
                pass
    j = jsonify( result="Error", msg = "No shard with id %s"%shard_id)
    return reply(j, 404)
	
@app.route('/shard/changeShardNumber', methods=['PUT'])
def changeShardNum():
    global NUM_OF_SHARDS
    num = int ( request.form.get('num') )
    if num == 0:
        j = jsonify(result="Error", msg = "Must have at least one shard")
        return reply(j, 400)
    if num > len(view):
        j = jsonify(result="Error", msg = "Not enough nodes for %s shards"%num)
        return reply(j, 400)
    if int(len(view)/num) <= 1:
        j = jsonify(result="Error", msg = "Not enough nodes. %s shards result in a nonfault tolerant shard"%num )
        return reply(j, 400)
    
    if num == NUM_OF_SHARDS:
        ids = []
        for i in range(0, NUM_OF_SHARDS):
            ids.append(str(i) )
        j = jsonify(result='Success', shard_ids=",".join(ids) )
        return reply(j, 200)

    allKeys = {}
    saved = []
    # save one node's data from each shard, make sure to clean current node
    for i in range(0, NUM_OF_SHARDS):
        for node in view:
            if str(view[node]) == str(i) and node not in saved and node != IP_PORT:
                saved.append(node)
                break
    for node in saved:
        try:
            m = requests.get('http://%s/share'%str(node), timeout = 5)
            if m.status_code != 404:
                data = m.json()
                savedDS = data['DS']
                allKeys.update( json.loads(savedDS) )
        except requests.exceptions.RequestException:
            print("getDS TIMEOUT!!!!")
            pass


    # redivide keys and nodes
    NUM_OF_NODES = int(len(view)/num) + 1
    if len(view) % num == 0:
        NUM_OF_NODES = len(view)/num
    
    shard_id = 0
    i = 0
    for node in view:
        # split
        view[node] = shard_id
        if i == NUM_OF_NODES:
            i = 0
            shard_id += 1
        view[node] = shard_id
        i+=1
        # clear myself
        if node == IP_PORT:
            DS.clear()
            PAYLOAD.clear()
            TIMESTAMP.clear()
        else:
            try:
                # clear all nodes
                m = requests.delete('http://%s/clear'%str(node), timeout= 5 )
                if m.status_code != 404:
                    print("not 404")
            except requests.exceptions.RequestException:
                print("clear TIMEOUT!!!!")
                pass
    
    # update view and shard in ALL nodes
    for node in view:
        if node != IP_PORT:
            try:
                m = requests.put('http://%s/updateShard'%str(node), timeout = 5, data={'view':json.dumps(view), 'num':num } )
                if m.status_code != 404:
                    print("not 404")
            except requests.exceptions.RequestException:
                print("updateShard TIMEOUT!!!!")
                pass

    if len(allKeys) == 0:
        NUM_OF_SHARDS=num
        ids = []
        for i in range(0, NUM_OF_SHARDS):
            ids.append(str(i))
        j = jsonify(result='Success', shard_ids=",".join(ids))
        return reply(j, 200)


    # split keys to each shard
    keyOnEachShard = int(len(allKeys)/num)
    if keyOnEachShard > len(allKeys) :
        keyOnEachShard = len(allKeys)
    id=0
    for item in chunks( allKeys, keyOnEachShard ):
        members = getMembers(id)
        for replica in members:
            if replica != IP_PORT:
                try:
                    m = requests.put('http://%s/sync'%str(replica), timeout = 5, data={'DS':json.dumps(item)} )
                    if m.status_code != 404:
                        print("not 404")
                except requests.exceptions.RequestException:
                    print("updateShard TIMEOUT!!!!")
                    pass
            else:
                DS.update(item)
        if id != num:
            id+=1
    
    NUM_OF_SHARDS = num

    ids = []
    for i in range(0, NUM_OF_SHARDS):
        ids.append(str(i) )
    # j = jsonify(result='Success', shard_ids=",".join(ids), allKeys=str(len(allKeys)), keyOnEach = str(keyOnEachShard), all_keys=json.dumps(allKeys) )
    j = jsonify(result='Success', shard_ids=",".join(ids) )
    return reply(j, 200)
                    

#######################
#
# Endpoints KVS
# Additionally return <shard_id> w/ "owner:<shardId>" when GETting a key
#
# If for any of the above /keyValue-store endpoints, you are unable to answer the request for causal consistency reasons, please return:
#
# {"result":"Error",
# "msg": "Unable to serve request and maintain causal consistency",
# "payload": <payload>},
# Status=400
# If for any of the above /keyValue-store endpoints, you are unable to answer the request because the entire shard which owns the key in question is unreachable (ie down or network partitioned away) please return:
#
# {"result":"Error",
# "msg": "Unable to access key: <key>",
# "payload": <payload>},
# Status=400
#
# !!!When will above scenarios occur???
#
#######################

"""
When getting keys, if not in this shard, ask others in other shards
When putting keys, still write all but only write to members in this shard
(is this ok? )
When putting, we need to decide which shard to put (random? reading the length of keys?)

"""
@app.route('/keyValue-store/<key>', methods=['GET','PUT','DELETE'])
def kvs(key):
    key = str(key)
    payload = request.form.get('payload')
    payload = initializePayload(payload)
    if not isValid(key) :# make sure key is valid
        j = jsonify(result='Error', msg='Key not valid', payload = str(payload) )
        return reply(j,400)
    if request.method == 'GET':
        if key in DS:
            # merge and update payload
            PAYLOAD[key] = initializePayload('a')
            # if payload too old
            #if not chooseReplica(str(PAYLOAD[key]), str(payload), 0, 0):
            #    j = jsonify(result="Error", msg="Payload out of date", payload = str(PAYLOAD[key]) )
            #    return reply(j, 400)
            status_code=200
            j = jsonify(result = 'Success', value = DS[key], owner = str(view[IP_PORT]), payload = str(PAYLOAD[key]) )
        else:
            # ask the shard with this key
            for node in view:
                if node != IP_PORT:
                    try:
                        m = requests.get('http://%s/client_request/%s'%(str(node), key), timeout=2 )
                        # if replica val is replaced, then msg should be replaced=true
                        if m.status_code != 404:
                            return make_response(m.text, m.status_code, {'Content-Type':'application/json'})
                    except requests.exceptions.RequestException:
                        # this replica is down
                        print("TIMEOUT!!!!")
                        pass

            if key in PAYLOAD:
                payload = PAYLOAD[key]
            j = jsonify(result = 'Error', msg = 'Key does not exist', payload = str(payload) )
            status_code=404
        return reply(j,status_code)

    if request.method == 'PUT':
        # missing value case
        if 'val' not in request.form:
            j = jsonify(result='Error', msg='Value is missing', payload = str(payload)  )
            return reply(j,400)
        # value is too large case
        val = request.form.get('val')
        if sys.getsizeof(val) > maxVal :
            j = jsonify(result='Error', msg='Object too large. Size limit is 1MB', payload = str(payload) )
            return reply(j,400)

        if key in DS:
            DS[key] = val
            PAYLOAD[key] = initializePayload('a')
            TIMESTAMP[key] = time.time()
            # broadcast, write to ALL members in shard
            members = getMembers( view[IP_PORT] )
            for replica in members:
                if replica != IP_PORT:
                    try:
                        m = requests.put('http://%s/client_request/%s'%(str(replica), key ), data={'val':DS[key], 'payload':PAYLOAD[key], 'timestamp':TIMESTAMP[key] }, timeout=2)
                        # if replica val is replaced, then msg should be replaced=true
                        if m.status_code != 404:
                            data = m.json()
                            PAYLOAD[key] = mergePayload(PAYLOAD[key], data["payload"])
                    except requests.exceptions.RequestException:
                            # this replica is down
                            print("TIMEOUT!!!!")
                            pass
            j = jsonify(msg='Updated successfully', replaced=True, owner=str(view[IP_PORT]), payload = str(PAYLOAD[key]))
            return reply(j, 200)
        else:
            # check if anyone has this key
            for node in view:
                if node != IP_PORT:
                    try:
                        m = requests.get('http://%s/client_request/%s'%(str(node), key ), timeout=2 )
                        if m.status_code != 404:
                            print("not 404")
                    except requests.exceptions.RequestException:
                        pass
                    if m.status_code != 404:
                        # if someone has it, put to all members
                        members = getMembers(view[node])
                        for replica in members:
                            if replica != IP_PORT:
                                try:
                                    m = requests.put('http://%s/client_request/%s'%(str(replica), key ), data={'val':val, 'payload':payload, 'timestamp':str(time.time()) }, timeout=5)
                                    if m.status_code != 404:
                                        print("not 404")
                                except requests.exceptions.RequestException:
                                    print("TIMEOUT!!!!")
                                    pass
                        j = jsonify(msg='Updated successfully', replaced=True, owner=str(view[node]), payload = payload)
                        return reply(j, 200)
            # no one has the key
            global NUM_OF_SHARDS
            # add it to a random shard
            r = random.randint(0, NUM_OF_SHARDS-1)
            members = getMembers(str(r) )
            for replica in members:
                if replica == IP_PORT:
                    DS[key] = val
                    PAYLOAD[key] = initializePayload('a')
                    TIMESTAMP[key] = time.time()
                if replica != IP_PORT:
                    try:
                        m = requests.put('http://%s/client_request/%s'%(str(replica), key ), data={'val':val, 'payload':payload, 'timestamp':str(time.time())  }, timeout=5)
                        if m.status_code != 404:
                            print("not 404")
                    except requests.exceptions.RequestException:
                        print("TIMEOUT!!!!")
                        pass
            j = jsonify(msg='Added successfully', replaced=False, owner=str(r), payload = payload)
            return reply(j, 201)

    if request.method == 'DELETE':
        # initialize payload if key is not in payload
        if not key in PAYLOAD:
            PAYLOAD[key] = initializePayload('a')
        if key in DS:
            DS.pop(key, None)
            PAYLOAD[key] = initializePayload('a')
            TIMESTAMP[key] = time.time()
            members = getMembers(view[IP_PORT] )
            for replica in members:
                if replica != IP_PORT:
                    try:
                        m = requests.delete('http://%s/client_request/%s'%(str(replica), key), timeout=2, data={'payload':PAYLOAD[key], 'timestamp':TIMESTAMP[key]})
                        # if replica val is replaced, then msg should be replaced=true
                        if m.status_code != 404:
                            PAYLOAD[key] = initializePayload('a')
                    except requests.exceptions.Timeout:
                        # this replica is down
                        print("TIMEOUT!!!!")
                        pass
            j = jsonify(result = 'Success', msg = 'Key deleted', owner = str(view[IP_PORT]), payload = str(PAYLOAD[key]))
            return reply(j,200)
        else:
            # check if anyone has the key
            for node in view:
                if node != IP_PORT:
                    try:
                        m = requests.get('http://%s/client_request/%s'%(str(node), key ), timeout=2 )
                        if m.status_code != 404:
                            # if someone has it, delete to all members
                            members = getMembers(view[node])
                            for replica in members:
                                if replica != IP_PORT:
                                    try:
                                        m = requests.delete('http://%s/client_request/%s'%(str(replica), key ), timeout=2, data={'payload':PAYLOAD[key], 'timestamp':TIMESTAMP[key] })
                                        if m.status_code != 404:
                                            print("not 404")
                                            data = m.json()
                                            payload = data["payload"]
                                    except requests.exceptions.RequestException:
                                        print("TIMEOUT!!!!")
                                        pass
                            j = jsonify(result='Success', msg = 'Key deleted', owner=str(id), payload = payload)
                            return reply(j, 200)
                    except requests.exceptions.RequestException:
                            # this replica is down
                            print("TIMEOUT!!!!")
                            pass

        # no one has the key
        if key in PAYLOAD:
            payload = PAYLOAD[key]
        else:
            PAYLOAD[key] = initializePayload('a')
        j = jsonify(result = 'Error', msg ='Key does not exist', payload = str(PAYLOAD[key]) )
        return reply(j,404)

##################################################################################################

# replicas' action
@app.route('/client_request/<key>', methods=['GET','PUT','DELETE'])
def client_request(key):
    if request.method == 'GET':
        return get(key)
    if request.method == 'PUT':
        val = request.form.get('val')
        payload = request.form.get('payload')
        time = request.form.get('timestamp')
        return put(key, val, payload, time)
    if request.method == 'DELETE':
        payload = request.form.get('payload')
        time = request.form.get('timestamp')
        return dele(key, payload, time)

@app.route('/keyValue-store/search/<key>', methods=['GET'])
def searchkey(key):
    payload = request.form.get('payload')
    payload = initializePayload(payload)
    if not isValid(key) :# make sure key is valid
        j = jsonify(result='Error', msg='Key not valid')
        return make_response(j, 400, {'Content-Type':'application/json'})


    if request.method == 'GET':
        if key in DS:
            PAYLOAD[key] = initializePayload('a')
            j = jsonify( result='Success', isExists=True, owner = str(view[IP_PORT]), payload= str(PAYLOAD[key]) )
            return reply(j, 200)
        else:
            # ask all shards
            for node in view:
                if node != IP_PORT:
                    m = requests.get('http://%s/client_request/%s'%(str(node), key), timeout=2)
                    # if replica val is replaced, then msg should be replaced=true
                    if m.status_code != 404:
                        data = m.json()
                        payload = data["payload"]
                        j = jsonify( result='Success', isExists=True, owner = str(view[node]), payload= payload )
                        return reply(j, 200)
        if key in PAYLOAD:
            payload = PAYLOAD[key]
        j = jsonify( result='Success', isExists=False, payload= str(payload) )
        return reply(j, 200)

# delete all keys in current node
@app.route('/clear', methods=['DELETE'])
def clear():
    #del DS[:]
    DS.clear()
    PAYLOAD.clear()
    TIMESTAMP.clear()
    j = jsonify (result="Cleared")
    return reply(j, 200)

# share all keys to members
@app.route('/share', methods=['GET','PUT'])
def share():
    if request.method == 'GET':
        j = jsonify(result="Success", DS=json.dumps(DS) )
        return reply(j, 200)
    if request.method == 'PUT':
        values = request.values
        sender = values['sender']
        members = getMembers(view[IP_PORT])
        for replica in members:
            if replica != IP_PORT and replica != sender:
                try:
                    m = requests.put('http://%s/sync'%str(replica), timeout=2, data={'DS':json.dumps(DS) })
                    if m.status_code != 404:
                        print("not 404")
                except requests.exceptions.RequestException:
                    pass
        j = jsonify(result="Shared")
        return reply(j, 200)

@app.route('/updateShard', methods=['PUT'])
def updateShard():
    global view
    global NUM_OF_SHARDS
    values = request.values
    updatedView = values['view']
    num = int(values['num'])
    view.clear()
    view.update(json.loads(updatedView))
    NUM_OF_SHARDS = num
    # update shard and view
    j = jsonify(result="Updated shard")
    return reply(j, 200)

@app.route('/count/<shard_id>', methods=['GET'])
def keyCount(shard_id):
    if str(view[IP_PORT]) == shard_id:
        j = jsonify( result="Success", Count= str(len(DS)) )
        return reply(j,200)
    else:
        j = jsonify( result="Error" )
        return reply(j,404)

@app.route('/addnode', methods=['PUT'])
def addnode():
    global NUM_OF_SHARDS
    values = request.values
    ip_port=values['ip_port']
    if ip_port not in view:
        view[ip_port] = int(NUM_OF_SHARDS - 1)
        all_nodes.append(ip_port)
    for key in PAYLOAD:
        PAYLOAD[key]=initializePayload('a')
        #updatePayload(PAYLOAD[key], getIndex())
    j = jsonify(msg='Success', DS=str(DS))
    return reply(j,200)

@app.route('/delnode', methods=['DELETE'])
def delnode():
    values = request.values
    ip_port = values['ip_port']
    if ip_port in view:
        all_nodes.remove(ip_port)
        del view[ip_port]
    j = jsonify(msg='Success')
    return reply(j, 200)

@app.route('/sync', methods=['PUT'])
def updateKey():
    updatedDS = request.form.get('DS')
    DS.update(json.loads(updatedDS))
    j = jsonify(msg='Successfully synced')
    return reply(j,200)

@app.route('/updateView', methods=['PUT'])
def updateView():
    values = request.values
    node=values['node']
    shard_id = values['shard_id']
    # update shard and view
    view[node] = int(shard_id)
    j = jsonify(result="Updated view")
    return reply(j, 200)

@app.route('/view', methods=['GET','PUT','DELETE'])
def viewOperation():
    global NUM_OF_SHARDS
    global all_nodes
    if request.method == 'GET':
        '''
            Should return that container's view of the system. i.e. A comma separated list of all of the ip-ports your containers are running on (the same string you pass to the environment variable VIEW when you run a container). This should look like this:
            'view': "176.32.164.10:8082,176.32.164.10:8083"}, 
            Status = 200
        '''
        view_string=",".join(all_nodes)
        j = jsonify(view=view_string)
        return reply(j,200)

    if request.method == 'PUT':
        '''
            Should tell container to initiate a view change, such that all containers in the system should add the new container's ip port <NewIPPort> to their views. Should return a confirmation which looks like:
            'result': "Success", 
            'msg'   : "Successfully added<NewIPPort> to view"}, 
            Status = 200

            If the container is already in the view, this should return an error message like so:
            'result': "Error", 
            'msg': "<NewIPPort> is already in view"},
            Status = 404

            !!!!still need SHARD implementation
        '''
        values = request.values
        ip_port = values['ip_port']

        if ip_port in all_nodes:
            msg = "%s is already in view" % ip_port
            j = jsonify(result='Error', msg=msg)
            return reply(j, 404)
        else:

            for node in view:
                if node != IP_PORT:
                    try:
                        m = requests.put('http://%s/addnode' % str(node), timeout=2, data={'ip_port': ip_port})
                        if m.status_code != 404:
                            print("not 404")
                    except requests.exceptions.RequestException:
                        pass
            view[ip_port] = int(NUM_OF_SHARDS - 1)
            all_nodes.append(ip_port)
            try:
                m = requests.put('http://%s/sync'%str(ip_port), timeout=2, data={'DS':json.dumps(DS) })
                if m.status_code != 404:
                    print("not 404")
            except requests.exceptions.RequestException:
                pass

            msg = "Successfully added %s to view" % ip_port
            j = jsonify(result='Success', msg=msg)
            return reply(j, 200)

    if request.method == 'DELETE':
        '''
            Should tell container to initiate a view change, such that all containers in the system should remove the old container's ip port <RemovedIPPort> from their views. Should return a confirmation which looks like:
            'result': "Success", 
            'msg'   : "Successfully removed <RemovedIPPort> from view"}, 
            Status = 200

            If the container is already in the view, this should return an error message like so:
            'result': "Error", 
            'msg': "<RemovedIPPort> is not in current view"},
            Status = 404
        '''

        values = request.values
        deleteNode = values['ip_port']
        count = len(getMembers(view[deleteNode]))
        this_id = view[deleteNode]
        if deleteNode not in view:
            msg = "%s is not in current view" % deleteNode
            j = jsonify(result='Error', msg=msg)
            return reply(j, 404)

        else:
            for node in view:
                if node != IP_PORT:
                    try:
                        m = requests.delete('http://%s/delnode' % str(node), timeout=3, data={'ip_port': deleteNode})
                        if m.status_code != 404:
                            print("not 404")
                    except requests.exceptions.RequestException:
                        pass

            all_nodes.remove(deleteNode)
            del view[deleteNode]

        if count == 2:
            # After deletion there would only be one node in the shard, see how many members do they have in shards
            # if >2, then move one of them to the this shard
            # if everyone else also have 2, join it to anyone of them
            lonely_node = getMembers(this_id)[0]
            for node in view:
                if len(getMembers(view[node])) > 2:
                    view[node] = this_id
                    m = requests.delete('http://%s/clear' % str(node), timeout=3)
                    if m.status_code != 404:
                        print("not 404")
                    moved_node = node
                    num=NUM_OF_SHARDS
                    for node in view:
                        if node != IP_PORT:
                            try:
                                #m = requests.put('http://%s/updateShard' % str(node), timeout=5,
                                #                data={'view': json.dumps(view), 'num': num})
                                m = requests.put('http://%s/updateShard' % str(node), timeout=5, data={'view':json.dumps(view),'num':num} )
                                if m.status_code != 404:
                                    print("not 404")
                            except requests.exceptions.RequestException:
                                pass
                    try:
                        m = requests.get('http://%s/share' % str(lonely_node), timeout=2)
                        if m.status_code != 404:
                            print("not 404")
                    except requests.exceptions.RequestException:
                        pass
                    msg = "Successfully removed %s from view" % deleteNode
                    j = jsonify(result='Success', msg=msg)
                    return reply(j, 200)

            lonely_id = view[lonely_node]

            if lonely_id != NUM_OF_SHARDS-1:
                for node in view:
                    if view[node] > lonely_id:
                        view[node] -= 1

            view[lonely_node] = 0

            NUM_OF_SHARDS -= 1
            num=NUM_OF_SHARDS
            for node in view:
                if node != IP_PORT:
                    m = requests.put('http://%s/updateShard' % str(node), timeout=5, data={'view': json.dumps(view),'num':num})
                    if m.status_code != 404:
                        print("not 404")

            members = getMembers(view[lonely_node])
            for node in members:
                if node != IP_PORT:
                    try:
                        m = requests.put('http://%s/share' % str(node), timeout=2, data={'sender': IP_PORT})
                        if m.status_code != 404:
                            print("not 404")
                    except requests.exceptions.RequestException:
                        pass

            if IP_PORT in members:
                try:
                    m = requests.get('http://%s/share' % str(lonely_node), timeout=5)
                    if m.status_code != 404:
                        data = m.json()
                        updatedDS = data["DS"]
                        DS.update(json.loads(updatedDS))
                except requests.exceptions.RequestException:
                    print("share TIMEOUT!!!!")
                    pass

        msg = "Successfully removed %s from view" % deleteNode
        j = jsonify(result='Success', msg=msg)
        return reply(j, 200)

##################
#
#	Previous methods that we could based on for implementation	
#
##################


def get(key):
    myPay = initializePayload('a')
    myTime = 0
    if key in DS:
        j = jsonify(result='Success', value=DS[key], owner=str(view[IP_PORT]), payload=myPay, timestamp=myTime)
        return reply(j, 200)
    else:
        j = jsonify(result='Error', msg='Key does not exist', payload=myPay, timestamp=myTime)
        return reply(j, 404)


def find(key):
    if key in DS:
        j = jsonify(result='Success', isExists=True, owner=str(view[IP_PORT]), payload=PAYLOAD[key], timestamp=TIMESTAMP[key])
        return reply(j, 200)
    else:
        j = jsonify(result='Error', isExists=False)
        return reply(j, 404)


def put(key, val, payload, time):
    # initialize payload for key if it doesn't exist
    if not key in PAYLOAD:
        PAYLOAD[key] = initializePayload('a')
    # merge and update payload
    PAYLOAD[key]=initializePayload('a')
    #PAYLOAD[key] = mergePayload( str(PAYLOAD[key]) , str(payload) )
    #PAYLOAD[key] = updatePayload( str(PAYLOAD[key]), getIndex() )
    TIMESTAMP[key] = time
    if key in DS:
        DS[key] = val
        j = jsonify(msg='Updated successfully', replaced=True, payload=PAYLOAD[key])
        return reply(j,200)
    else:
        DS[key] = val
        j = jsonify(msg='Added successfully', replaced=False, payload=PAYLOAD[key])
        return reply(j,201)


def dele(key, payload, time):
   
    if key in DS:
        PAYLOAD[key]=initializePayload('a')
        #PAYLOAD[key] = mergePayload(str(PAYLOAD[key]), str(payload) )
        #PAYLOAD[key] = updatePayload( str(PAYLOAD[key]), getIndex() )
        TIMESTAMP[key] = time
        DS.pop(key, None)
        j = jsonify(result='Success', existed=True, msg = 'Key deleted', payload=PAYLOAD[key])
        return reply(j,200)
    else:
        if not key in PAYLOAD:
            j = jsonify(result='Error', existed=False, payload=payload)
        else:
            j = jsonify(result='Error', existed=True, payload=PAYLOAD[key])
        return reply(j,404)

# Meet the size limit requirements
def isValid(key):
    return 0 < len(key) < 221

def reply(j, code):
    return make_response(j, code, {'Content-Type':'application/json'})

def serverdown():
	j = jsonify(result='Error', msg='Server unavailable')
	return reply(j,501)


def convert():
    global NUM_OF_SHARDS
    global NUM_OF_NODES
    global all_nodes
    NUM_OF_NODES = int(len(all_nodes)/NUM_OF_SHARDS) + 1
    if len(all_nodes) % NUM_OF_SHARDS == 0:
        NUM_OF_NODES = len(all_nodes)/NUM_OF_SHARDS
        # shard = 2, ip = 6
        # ip/shard = 3
        # shard = 2, ip = 5
        # ip/shard+1 = 3

    shard_id = 0
    i = 0
    for node in all_nodes:
        if i == NUM_OF_NODES:
            i = 0
            shard_id += 1
        view[node] = shard_id
        i+=1

def getMembers(shard_id):
    members = []
    for node in view:
        if view[node] == int(shard_id) :
            members.append(node)
    members.sort()
    return members

def get_nodes(viewString):
    global all_nodes
    all_nodes.extend(viewString.split(','))

if __name__ == '__main__':
    app.debug = True
    # Extract VIEW & IP_PORT from ENV variable
    VIEW = os.getenv('VIEW')

    NUM_OF_SHARDS = int(os.getenv('S'))

    IP_PORT = os.getenv('IP_PORT')

    get_nodes(VIEW)
    convert()

    
    app.run(host = "0.0.0.0", port = 8080)