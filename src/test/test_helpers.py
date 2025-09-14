
import sys
import requests
import json
import urllib.parse
import test_recorded

try:
    from shinerainsevenlib.standard import *
    from shinerainsevenlib.core import *
except ImportError:
    raise ImportError('Please first run ' + 
        '`pip install shinerainsevenlib` to run these tests.')

configText = files.readAll('../configs.json', encoding='utf-8')
configs = json.loads(configText)
assertEq('/mock.zendesk.com', configs['overrideJobStatusUrlPrefix'])

# we support with+without .json suffix on all endpoints,
# so run tests twice, once with this True, and once with it False 
hitEndpointEndingWithJson = False

# instead of contacting mock-zendesk, contact recorded responses
# from a real zendesk instance
replayRecordedResponses = False
replayRecordedResponsesCounter = 0

host = f'http://localhost:{configs["portNumber"]}'
stateIds = dict(
    admin = None,
    user1 = None,
    user2 = None,
    user3 = None,
)


def confirmSet(obj, flds):
    for fld in flds:
        assertTrue(fld in obj, f'field {fld} not present')
        assertTrue(obj[fld], f'field {fld} is null/None')

def subInTemplates(s):
    s = s.replace('%FLDID1%', str(stateIds["customFld1"]))
    s = s.replace('%FLDID2%', str(stateIds["customFld2"]))
    s = s.replace('%FLDID3%', str(stateIds["customFld3"]))
    s = s.replace('%USER1%', str(stateIds["user1"]))
    s = s.replace('%USER2%', str(stateIds["user2"]))
    s = s.replace('%USER3%', str(stateIds["user3"]))
    for i in range(6):
        s = s.replace(f'%TICKET{i+1}%', str(stateIds.get(f'ticket{i+1}', '')))

    for obj in configs['customTriggers']:
        if obj['action']=='removeTagWhenPublicCommentPosted':
            s = s.replace('%TAG_REMOVED_BY_TRIGGER%', obj['value'])
        if obj['action']=='openPostWhenPublicCommentContainingTextPosted':
            s = s.replace('%TEXT_NOTICED_BY_TRIGGER%', obj['value'])

    return s


def quote(s):
    return urllib.parse.quote(s)

def sendGet(endpoint, encodedQueryString=''):
    return sendImpl('GET', endpoint, encodedQueryString=encodedQueryString)

def sendPost(endpoint, jsonData):
    return sendImpl('POST', endpoint, jsonData=jsonData)

def sendImpl(method, endpoint, jsonData=None, encodedQueryString=''):
    global configs
    if not endpoint.endswith('delete_all'):
        if not hitEndpointEndingWithJson:
            if endpoint.endswith('.json'):
                endpoint = endpoint.replace('.json', '')
        else:
            if not endpoint.endswith('.json'):
                endpoint += '.json'

    if encodedQueryString:
        encodedQueryString = '?' + encodedQueryString
    if endpoint.startswith('http'):
        fullEndpoint = f'{endpoint}{encodedQueryString}'
    else:
        assertTrue(endpoint.startswith('/api'), endpoint)
        fullEndpoint = f'{host}{endpoint}{encodedQueryString}'

    # would use curl, but want to fail on non-2xx responses
    # and most distros don't have latest curl with --fail-with-body
    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'

    if jsonData:
        assertTrue(isinstance(jsonData, str))
        assertTrue(not '%' in jsonData, "missing template?", jsonData.split('%')[-1])
        jsonData = stripComments(jsonData)
        try:
            json.loads(jsonData)
        except:
            assertTrue(False, 'looks like the json we are about to send does not parse', jsonData)

    
    trace('fullEndpoint=' + fullEndpoint, jsonData, '\n\n\n')
    if replayRecordedResponses:
        global replayRecordedResponsesCounter
        index = replayRecordedResponsesCounter
        replayRecordedResponsesCounter += 1
        text = test_recorded.simulatedResponses[index]
        code = 400 if text.strip().startswith('Error') else 200
        r = Bucket(text=text, status_code=code)
    else:
        r = doRequest(method, fullEndpoint, headers=headers, data=jsonData)

    if not (r.status_code>=200 and r.status_code<=299):
        trace('was sending,', method, fullEndpoint, jsonData)
        if 'x-zendesk-api-warn' in r.headers:
            trace('x-zendesk-api-warn = ' + r.headers['x-zendesk-api-warn'])
        trace(f"status_code={r.status_code}")
        assertTrue(False, f"status_code={r.status_code}", r.text)
    else:
        try:
            return json.loads(r.text)
        except:
            assertTrue(False, 'looks like the json we got does not parse', r.text)
    
    return None



def sendPostAndGetJob(endpoint, jsonData):
    jobStatus = sendPost(endpoint, jsonData)
    checkJobStatusOk(jobStatus, 'queued')
    response = sendGet(jobStatus['job_status']['url'])
    checkJobStatusOk(response, 'completed')
    return response['job_status']

def stripComments(s):
    lines = s.replace('\r\n', '\n').split('\n')
    lines = jslike.map(lines, lambda line: line.split('###')[0])
    return '\n'.join(lines)
    
def checkJobStatusOk(response, expectedStatus):
    theId = response['job_status']['id']
    if not replayRecordedResponses:
        assertTrue(configs['overrideJobStatusUrlPrefix'] in response['job_status']['url'])
    assertTrue(response['job_status']['url'].endswith(f'/api/v2/job_statuses/{theId}.json'))
    
    if expectedStatus == 'completed':
        assertTrue(int(response['job_status']['total']) > 0)
        assertTrue(int(response['job_status']['progress']) > 0)
        assertTrue(len(response['job_status']['message']) > 0)
        assertEq('completed', response['job_status']['status'])
    elif expectedStatus == 'queued':
        assertTrue((response['job_status']['total']) is None)
        assertTrue((response['job_status']['progress']) is None)
        assertTrue((response['job_status']['message']) is None)
        assertTrue(response['job_status']['status'] in ['completed', 'queued'], response['job_status']['status'])
    else:
        assertTrue(False, 'unsupported', expectedStatus)

def assertTagsEq(tags1, tags2):
    assertEq(sorted(tags1), sorted(tags2))

def assertCustomFieldsEq(flds1, flds2):
    def fldsToDictAndNoNulls(f):
        result = {}
        for pair in f:
            # remove null values
            if pair['value'] is not None:
                result[pair['id']] = pair['value']
        return result
    assertEq(fldsToDictAndNoNulls(flds1), fldsToDictAndNoNulls(flds2))

def assertSubject(expected, got):
    if replayRecordedResponses and expected=='(no subject given)' and got is None:
        return True
    assertEq(expected, got)
    return None

def testComment(c, authorId, text, public=True):
    if replayRecordedResponses:
        confirmSet(c, 'id|created_at'.split('|'))
    else:
        confirmSet(c, 'id|created_at|updated_at'.split('|'))
        assertEq(text, c['html_body'])

    assertEq('Comment', c['type'])
    assertEq(text, c['body'])
    assertEq(text, c['plain_body'])
    assertEq(public, c['public'])
    assertEq(authorId, c['author_id'])
    assertEq([], c['attachments'])

def testBatchResults(result, action, status, hasSuccess=False):
    for i, item in enumerate(result['results']):
        if not replayRecordedResponses or ('index' in item):
            assertEq(i, item['index'])
        if action is not None and status is not None:
            thisAction = action if isinstance(action, str) else action(i)
            thisStatus = status if isinstance(status, str) else status(i)
            assertEq(thisAction, item['action'])
            assertEq(thisStatus, item['status'])
        assertTrue(int(item['id']) > 0)
        if hasSuccess:
            if not replayRecordedResponses or ('success' in item):
                assertEq(True, item['success'])


def doRequest(method, *args, **kwargs):
    if method.upper() == 'GET':
        return requests.get(*args, **kwargs)
    elif method.upper() == 'PUT':
        return requests.put(*args, **kwargs)
    elif method.upper() == 'DELETE':
        return requests.delete(*args, **kwargs)
    elif method.upper() == 'POST':
        return requests.post(*args, **kwargs)
    else:
        assertTrue(False, "unknown method")
        return None

def setupStateIds():
    if replayRecordedResponses:
        stateIds['customFld1'] = 10993199398427
        stateIds['customFld2'] = 10993238892315
        stateIds['customFld3'] = 11130845293467
        stateIds['admin'] = 10981611611675
    else:
        customFlds = configs['customFields']
        lCustomFlds = list(customFlds.keys())
        stateIds['customFld1'] = customFlds[lCustomFlds[0]]
        stateIds['customFld2'] = customFlds[lCustomFlds[1]]
        stateIds['customFld3'] = customFlds[lCustomFlds[2]]
        stateIds['admin'] = 111

def sortResultsByOurNumber(obj, stateIdsLocal, key):
    # maps to our numbers, so we are comparing 'ticket2' to 'ticket3'
    invertedDict = dict((v, k) for k, v in stateIdsLocal.items())
    obj[key].sort(key=lambda val: invertedDict.get(val['id']))
