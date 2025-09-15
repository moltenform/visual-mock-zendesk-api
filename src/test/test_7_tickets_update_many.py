from test_helpers import *


def go7TicketsUpdateMany():
    if replayRecordedResponses:
        trace('skipping, not yet in replayRecordedResponses')
        return

    import time
    time.sleep(1.5) # so that last_updated will be different.
    s = r'''{
    "tickets": [
      {
        "id": %TICKET1%,
        "status": "solved", ### will be overridden by trigger
        "requester_id": %USER2%,
        "submitter_id": %USER1%,
        "tags": ["tag2", "tag3", "tag2"], ### replace existing tags, remove dupes 
        "custom_fields": [{"id": %FLDID3%, "value":"fldval3_b"}, {"id": %FLDID2%, "value":"fldval2_b"}], ### this merges in
        "comment": {"body": "a %TEXT_NOTICED_BY_TRIGGER% b"} ### comment without an author id, requester is being changed
        ### trigger openPostWhenPublicCommentContainingTextPosted should fire
      },
      {
        "id": "%TICKET2%", ### support quoted ids
        "status": "solved",
        "additional_tags": ["tag2", "tag3", "tag2"], ### merge existing tags, remove dupes 
        "custom_fields": [{"id": "%FLDID2%", "value":"new"}] ### setting new flds, and quoted ids should work
      },
      {
        "id": %TICKET3%,
        "remove_tags": ["tag2", "tag3", "tag2"], ### remove existing tags
        "comment": {"body": "addedCommentOn3", "author_id":%USER1%} ### comment with an author id
      },
      {
        "id": %TICKET6%,
        ### adding a private comment, so removeTagWhenPublicCommentPosted trigger should not fire
        "comment": {"body": "addedCommentOn6", "public": false} ### comment without an author id, where prev comment != requesterid != admin
      }
    ]
  }'''

    s = subInTemplates(s)
    result = sendPostAndGetJob('/api/v2/tickets/update_many', s)
    assertEq(4, len(result['results']))
    assertEq(stateIds[f'ticket1'], result['results'][0]['id'])
    assertEq(stateIds[f'ticket2'], result['results'][1]['id'])
    assertEq(stateIds[f'ticket3'], result['results'][2]['id'])
    assertEq(stateIds[f'ticket6'], result['results'][3]['id'])
    for i, item in enumerate(result['results']):
        assertEq(i, item['index'])
        assertEq('update', item['action'])
        assertEq('Updated', item['status'])
        assertEq(True, item['success'])

    allIds = ','.join(str(stateIds[f'ticket{i}']) for i in range(1, 7))
    afterMods = sendGet('/api/v2/tickets/show_many', f'ids={allIds}')
    sortResultsByOurNumber(afterMods, stateIds, 'tickets')
    t1, t2, t3, _t4, _t5, t6 = afterMods['tickets']
    assertEq(6, len(afterMods['tickets']))

    ### confirm last_updated was bumped
    for i in range(1, 7):
        assertEq(stateIds[f'ticket{i}'], afterMods['tickets'][i - 1]['id'])
        modded = str(i) in '1,2,3,6'.split(',')
        wasUpdateBumped = stateIds[f'lastUpdateTicket{i}'] != afterMods['tickets'][i - 1]['updated_at']
        assertEq(modded, wasUpdateBumped)

    ### test the assertCustomFieldsEq helper
    assertCustomFieldsEq(
        [{
            'id': 1,
            'value': 'a'
        }, {
            'id': 2,
            'value': 'b'
        }], [{
            'id': 1,
            'value': 'a'
        }, {
            'id': 2,
            'value': 'b'
        }]
    )
    assertCustomFieldsEq(
        [{
            'id': 1,
            'value': 'a'
        }, {
            'id': 2,
            'value': 'b'
        }], [{
            'id': 2,
            'value': 'b'
        }, {
            'id': 1,
            'value': 'a'
        }]
    )
    assertException(
        lambda: assertCustomFieldsEq(
            [{
                'id': 1,
                'value': 'a'
            }, {
                'id': 2,
                'value': 'b'
            }], [{
                'id': 2,
                'value': 'b'
            }, {
                'id': 1,
                'value': 'c'
            }]
        ), Exception
    )
    assertTagsEq(['a', 'b'], ['a', 'b'])
    assertTagsEq(['a', 'b'], ['b', 'a'])
    assertException(lambda: assertTagsEq(['a', 'b'], ['a', 'a']), Exception)

    ### test ticket 1
    assertEq(stateIds["ticket1"], t1['id'])
    assertEq('ticket1', t1['subject'])
    assertEq('ticket1', t1['raw_subject'])
    assertEq('open', t1['status']) # set by trigger
    assertEq(stateIds["user2"], t1['requester_id'])
    assertEq(stateIds["user1"], t1['submitter_id'])
    assertEq(stateIds["admin"], t1['assignee_id'])
    assertTagsEq(["tag2", "tag3"], t1['tags']) # tags were modified
    expectedCustomFlds = [
        {
            'id': int(subInTemplates('%FLDID1%')),
            'value': 'fldval1'
        }, {
            'id': int(subInTemplates('%FLDID2%')),
            'value': 'fldval2_b'
        }, {
            'id': int(subInTemplates('%FLDID3%')),
            'value': 'fldval3_b'
        }
    ]
    assertCustomFieldsEq(expectedCustomFlds, t1['custom_fields'])
    assertCustomFieldsEq(expectedCustomFlds, t1['fields'])
    assertEq(True, t1['is_public'])
    if not replayRecordedResponses:
        assertEq(3, len(t1['comment_ids']))
    comments1 = sendGet(f'/api/v2/tickets/{t1["id"]}/comments')['comments']
    assertEq(3, len(comments1))
    testComment(comments1[0], authorId=stateIds['user2'], text='comment1', public=False)
    testComment(comments1[1], authorId=stateIds['admin'], text='comment2')
    testComment(comments1[2], authorId=stateIds['user2'], text=subInTemplates('a %TEXT_NOTICED_BY_TRIGGER% b'))

    ### test ticket 2
    assertEq(stateIds["ticket2"], t2['id'])
    assertEq('ticket2', t2['subject'])
    assertEq('ticket2', t2['raw_subject'])
    assertEq('solved', t2['status'])
    assertEq(stateIds["user4inline"], t2['requester_id'])
    assertEq(stateIds["user4inline"], t2['submitter_id'])
    assertEq(stateIds["admin"], t2['assignee_id'])
    assertTagsEq(["tag1", "tag2", "tag3"], t2['tags'])
    expectedCustomFlds = [{'id': int(subInTemplates('%FLDID2%')), 'value': 'new'}]
    assertCustomFieldsEq(expectedCustomFlds, t2['custom_fields'])
    assertCustomFieldsEq(expectedCustomFlds, t2['fields'])
    assertEq(True, t2['is_public'])
    if not replayRecordedResponses:
        assertEq(1, len(t2['comment_ids']))
    comments2 = sendGet(f'/api/v2/tickets/{t2["id"]}/comments')['comments']
    assertEq(1, len(comments2))
    testComment(comments2[0], authorId=stateIds['user4inline'], text='plainStringComment1')

    ### test ticket 3
    assertEq(stateIds["ticket3"], t3['id'])
    assertSubject('(no subject given)', t3['subject'])
    assertSubject('(no subject given)', t3['raw_subject'])
    assertEq('open', t3['status'])
    assertEq(stateIds["admin"], t3['requester_id'])
    assertEq(stateIds["admin"], t3['submitter_id'])
    assertEq(stateIds["admin"], t3['assignee_id'])
    assertTagsEq(["tag1"], t3['tags']) # removed by remove_tags and by trigger
    assertCustomFieldsEq([], t3['custom_fields'])
    assertCustomFieldsEq([], t3['fields'])
    assertEq(True, t3['is_public'])
    if not replayRecordedResponses:
        assertEq(2, len(t3['comment_ids']))
    comments3 = sendGet(f'/api/v2/tickets/{t3["id"]}/comments')['comments']
    assertEq(2, len(comments3))
    testComment(comments3[0], authorId=stateIds['admin'], text='plainStringComment2')
    testComment(comments3[1], authorId=stateIds['user1'], text='addedCommentOn3')

    ### test ticket 6
    assertEq(stateIds["ticket6"], t6['id'])
    assertSubject('(no subject given)', t6['subject'])
    assertSubject('(no subject given)', t6['raw_subject'])
    assertEq('open', t6['status'])
    assertEq(stateIds["user1"], t6['requester_id'])
    assertEq(stateIds["user1"], t6['submitter_id'])
    assertEq(stateIds["admin"], t6['assignee_id'])
    assertTagsEq(
        [subInTemplates('%TAG_REMOVED_BY_TRIGGER%')], t6['tags']
    ) # trigger won't fire because it's a private post
    assertCustomFieldsEq([], t6['custom_fields'])
    assertCustomFieldsEq([], t6['fields'])
    assertEq(True, t6['is_public'])
    if not replayRecordedResponses:
        assertEq(2, len(t6['comment_ids']))
    comments6 = sendGet(f'/api/v2/tickets/{t6["id"]}/comments')['comments']
    assertEq(2, len(comments6))
    testComment(comments6[0], authorId=stateIds['user2'], text='testAuthorIdUpdate')
    testComment(comments6[1], authorId=stateIds['user1'], text='addedCommentOn6', public=False)
