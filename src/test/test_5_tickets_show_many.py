
from test_helpers import *

def go5TicketsShowMany():
    ############## No results ###################
    result = sendGet('/api/v2/tickets/show_many', f'ids=999')
    sortResultsByOurNumber(result, stateIds, 'tickets')
    assertEq(0, len(result['tickets']))

    ############## One result ###################
    result = sendGet('/api/v2/tickets/show_many', f'ids={stateIds["ticket1"]}')
    sortResultsByOurNumber(result, stateIds, 'tickets')
    assertEq(1, len(result['tickets']))
    assertEq(stateIds["ticket1"], result['tickets'][0]['id'])
    assertEq('ticket1', result['tickets'][0]['subject'])

    ############## Many results, skip missing ###################
    result = sendGet('/api/v2/tickets/show_many', f'ids={stateIds["ticket2"]},999,{stateIds["ticket3"]}')
    sortResultsByOurNumber(result, stateIds, 'tickets')
    assertEq(2, len(result['tickets']))
    assertEq(stateIds["ticket2"], result['tickets'][0]['id'])
    assertEq('ticket2', result['tickets'][0]['subject'])
    assertEq(stateIds["ticket3"], result['tickets'][1]['id'])
    assertSubject('(no subject given)', result['tickets'][1]['subject'])

    ############## Thoroughly check data ###################
    allIds = ','.join(str(stateIds[f'ticket{i}']) for i in range(1,7))
    result = sendGet('/api/v2/tickets/show_many', f'ids={allIds}')
    sortResultsByOurNumber(result, stateIds, 'tickets')
    t1, t2, t3, _t4, _t5, t6 = result['tickets']
    assertEq(6, len(result['tickets']))
    for i in range(6):
        stateIds[f'lastUpdateTicket{i+1}'] = result['tickets'][i]['updated_at']
        confirmSet(result['tickets'][i], 'id|created_at|updated_at|description'.split('|'))
    

    expectedCustomFlds = [{'id': int(subInTemplates('%FLDID1%')), 'value': 'fldval1'}, {'id': int(subInTemplates('%FLDID2%')), 'value': 'fldval2'}]
    assertEq(stateIds["ticket1"], t1['id'])
    assertEq('ticket1', t1['subject'])
    assertEq('ticket1', t1['raw_subject'])
    assertEq('pending', t1['status'])
    assertEq(stateIds["user1"], t1['requester_id'])
    assertEq(stateIds["user1"], t1['submitter_id'])
    assertEq(stateIds["admin"], t1['assignee_id'])
    assertTagsEq(["tag1", "tag2"], t1['tags'])
    assertCustomFieldsEq(expectedCustomFlds, t1['custom_fields'])
    assertCustomFieldsEq(expectedCustomFlds, t1['fields'])
    assertEq(True, t1['is_public'])
    if not replayRecordedResponses:
        assertEq(2, len(t1['comment_ids']))

    assertEq(stateIds["ticket2"], t2['id'])
    assertEq('ticket2', t2['subject'])
    assertEq('ticket2', t2['raw_subject'])
    assertEq('open', t2['status'])
    assertEq(stateIds["user4inline"], t2['requester_id'])
    assertEq(stateIds["user4inline"], t2['submitter_id'])
    assertEq(stateIds["admin"], t2['assignee_id'])
    assertTagsEq(["tag1", "tag2"], t2['tags'])
    assertCustomFieldsEq([], t2['custom_fields'])
    assertCustomFieldsEq([], t2['fields'])
    assertEq(True, t2['is_public'])
    if not replayRecordedResponses:
        assertEq(1, len(t2['comment_ids']))

    assertEq(stateIds["ticket3"], t3['id'])
    assertSubject('(no subject given)', t3['subject'])
    assertSubject('(no subject given)', t3['raw_subject'])
    assertEq('open', t3['status'])
    assertEq(stateIds["admin"], t3['requester_id'])
    assertEq(stateIds["admin"], t3['submitter_id'])
    assertEq(stateIds["admin"], t3['assignee_id'])
    assertTagsEq(["tag1", "tag2", subInTemplates('%TAG_REMOVED_BY_TRIGGER%')], t3['tags'])
    assertCustomFieldsEq([], t3['custom_fields'])
    assertCustomFieldsEq([], t3['fields'])
    assertEq(True, t3['is_public'])
    if not replayRecordedResponses:
        assertEq(1, len(t3['comment_ids']))

    assertEq(stateIds["ticket6"], t6['id'])
    assertSubject('(no subject given)', t6['subject'])
    assertSubject('(no subject given)', t6['raw_subject'])
    assertEq('open', t6['status'])
    assertEq(stateIds["user1"], t6['requester_id'])
    assertEq(stateIds["user1"], t6['submitter_id'])
    assertEq(stateIds["admin"], t6['assignee_id'])
    assertTagsEq([subInTemplates('%TAG_REMOVED_BY_TRIGGER%')], t6['tags'])
    assertCustomFieldsEq([], t6['custom_fields'])
    assertCustomFieldsEq([], t6['fields'])
    assertEq(True, t6['is_public'])
    if not replayRecordedResponses:
        assertEq(1, len(t6['comment_ids']))
