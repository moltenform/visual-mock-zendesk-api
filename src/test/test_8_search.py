from test_helpers import *


def go8Search():
    if replayRecordedResponses:
        trace('skipping, not yet in replayRecordedResponses')
        return

    s = r'''{
    "tickets": [
      {
        ### create ticket: open/no tag/no fld1/no fld2/fld3=target = isThere 
        "created_at": "2022-04-01T06:38:32.399Z",
        "subject": "t1",
        "status": "open",
        "custom_fields": [
            {"id":%FLDID3%, "value":"includeTicketsWhereFld3SaysThis"}
        ],
        "tags": [],
        "comment": {"body": "t1"}
      },
      {
        ### create ticket: no conditions match = filtered out  
        "created_at": "2022-04-02T06:38:32.399Z",
        "subject": "t2",
        "status": "closed",
        "custom_fields": [
            {"id":%FLDID1%, "value":"skipTicketsWhereFld1SaysThis"},
            {"id":%FLDID2%, "value":"skipTicketsWhereFld2SaysThis"},
            {"id":%FLDID3%, "value":"notTheLookedForValue"}
        ],
        "tags": ["%TAG_REMOVED_BY_TRIGGER%"],
        "comment": {"body": "t2"}
      },
      {
        ### create ticket: closed(wrong)/no tag/fld1=different/fld2=different/fld3=target = filtered out 
        "created_at": "2022-04-03T06:38:32.399Z",
        "subject": "t3",
        "status": "closed",
        "custom_fields": [
            {"id":%FLDID1%, "value":"differentVal1"},
            {"id":%FLDID2%, "value":"differentVal2"},
            {"id":%FLDID3%, "value":"includeTicketsWhereFld3SaysThis"}
        ],
        "tags": ["searchTag1", "searchTag2"],
        "comment": {"body": "t3"}
      },
      {
        ### create ticket: open/tag(wrong)/fld1=different/fld2=different/fld3=target = filtered out  
        "created_at": "2022-04-04T06:38:32.399Z",
        "subject": "t4",
        "status": "open",
        "custom_fields": [
            {"id":%FLDID1%, "value":"differentVal1"},
            {"id":%FLDID2%, "value":"differentVal2"},
            {"id":%FLDID3%, "value":"includeTicketsWhereFld3SaysThis"}
        ],
        "tags": ["searchTag1", "searchTag2", "%TAG_REMOVED_BY_TRIGGER%"],
        "comment": {"body": "t4"}
      },
      {
        ### create ticket: open/no tag/fld1=skip/fld2=different/fld3=target = filtered out  
        "created_at": "2022-04-05T06:38:32.399Z",
        "subject": "t5",
        "status": "open",
        "custom_fields": [
            {"id":%FLDID1%, "value":"skipTicketsWhereFld1SaysThis"},
            {"id":%FLDID2%, "value":"differentVal2"},
            {"id":%FLDID3%, "value":"includeTicketsWhereFld3SaysThis"}
        ],
        "tags": ["searchTag1", "searchTag2"],
        "comment": {"body": "t5"}
      },
      {
        ### create ticket: open/no tag/fld1=different/fld2=skip/fld3=target = filtered out  
        "created_at": "2022-04-06T06:38:32.399Z",
        "subject": "t6",
        "status": "open",
        "custom_fields": [
            {"id":%FLDID1%, "value":"differentVal1"},
            {"id":%FLDID2%, "value":"skipTicketsWhereFld2SaysThis"},
            {"id":%FLDID3%, "value":"includeTicketsWhereFld3SaysThis"}
        ],
        "tags": ["searchTag1", "searchTag2"],
        "comment": {"body": "t6"}
      },
      {
        ### create ticket: open/no tag/fld1=different/fld2=different/fld3=other(wrong) = filtered out  
        "created_at": "2022-04-07T06:38:32.399Z",
        "subject": "t7",
        "status": "open",
        "custom_fields": [
            {"id":%FLDID1%, "value":"differentVal1"},
            {"id":%FLDID2%, "value":"differentVal2"},
            {"id":%FLDID3%, "value":"notTheLookedForValue"}
        ],
        "tags": ["searchTag1", "searchTag2"],
        "comment": {"body": "t7"}
      }
    ]
    }'''
    s = subInTemplates(s)
    result = sendPostAndGetJob('/api/v2/imports/tickets/create_many', s)
    assertEq(7, len(result['results']))
    for i in range(7):
        assertEq(i, result['results'][i]['index'])
        stateIds[f'ticketTestSearch{i+1}'] = int(result['results'][i]['id'])
        assertEq(True, result['results'][i]['success'])

    s = r'''{
    "tickets": [
     {
        ### create ticket: open/no tag/fld1=different/fld2=different/fld3=target = isThere 
        "created_at": "2022-04-08T06:38:32.399Z",
        "subject": "t8",
        "status": "open",
        "custom_fields": [
            {"id":%FLDID1%, "value":"differentVal1"},
            {"id":%FLDID2%, "value":"differentVal2"},
            {"id":%FLDID3%, "value":"includeTicketsWhereFld3SaysThis"}
        ],
        "tags": ["searchTag1"],
        "comment": {"body": "t8"}
      }
    ]
    }'''
    s = subInTemplates(s)
    result = sendPostAndGetJob('/api/v2/imports/tickets/create_many', s)
    assertEq(1, len(result['results']))
    for i in range(1):
        assertEq(i, result['results'][i]['index'])
        stateIds[f'ticketTestSearch8'] = int(result['results'][i]['id'])
        assertEq(True, result['results'][i]['success'])

    ####### simple search ################
    clauses = [f'custom_field_%FLDID3%:notTheLookedForValue']
    q = f'query=' + quote(subInTemplates(" ".join(clauses))) + '&sort_by=created_at&sort_order=asc'
    result = sendGet('/api/v2/search', q)
    assertEq(2, result['count'])
    assertEq(stateIds['ticketTestSearch2'], result['results'][0]['id'])
    assertEq(stateIds['ticketTestSearch7'], result['results'][1]['id'])

    ####### tags search ################
    clauses = [f'tags:searchTag1', f'tags:searchTag2']
    q = f'query=' + quote(subInTemplates(" ".join(clauses))) + '&sort_by=created_at&sort_order=asc'
    result = sendGet('/api/v2/search', q)
    assertEq(6, result['count'])
    assertEq(stateIds['ticketTestSearch3'], result['results'][0]['id'])
    assertEq(stateIds['ticketTestSearch4'], result['results'][1]['id'])
    assertEq(stateIds['ticketTestSearch5'], result['results'][2]['id'])
    assertEq(stateIds['ticketTestSearch6'], result['results'][3]['id'])
    assertEq(stateIds['ticketTestSearch7'], result['results'][4]['id'])
    assertEq(stateIds['ticketTestSearch8'], result['results'][5]['id'])

    ####### complex search ################
    clauses = [
        '-status:closed',
        '-tags:%TAG_REMOVED_BY_TRIGGER%',
        '-custom_field_%FLDID1%:skipTicketsWhereFld1SaysThis',
        '-custom_field_%FLDID2%:skipTicketsWhereFld2SaysThis',
        'custom_field_%FLDID3%:includeTicketsWhereFld3SaysThis',
    ]

    # sort asc
    q = f'query=' + quote(subInTemplates(" ".join(clauses))) + '&sort_by=created_at&sort_order=asc'
    result = sendGet('/api/v2/search', q)
    assertEq(2, result['count'])
    assertEq(stateIds['ticketTestSearch1'], result['results'][0]['id'])
    assertEq(stateIds['ticketTestSearch8'], result['results'][1]['id'])

    # sort desc
    q = f'query=' + quote(subInTemplates(" ".join(clauses))) + '&sort_by=created_at&sort_order=desc'
    result = sendGet('/api/v2/search', q)
    assertEq(2, result['count'])
    assertEq(stateIds['ticketTestSearch8'], result['results'][0]['id'])
    assertEq(stateIds['ticketTestSearch1'], result['results'][1]['id'])

    # handle extra spaces
    q = f'query=' + quote(subInTemplates("  ".join(clauses))) + '&sort_by=created_at&sort_order=asc'
    result = sendGet('/api/v2/search', q)
    assertEq(2, result['count'])
    assertEq(stateIds['ticketTestSearch1'], result['results'][0]['id'])
    assertEq(stateIds['ticketTestSearch8'], result['results'][1]['id'])

    # handle quotes
    clauses[0] = '-status:"closed"'
    clauses[2] = '-custom_field_%FLDID1%:"skipTicketsWhereFld1SaysThis"'
    q = f'query=' + quote(subInTemplates(" ".join(clauses))) + '&sort_by=created_at&sort_order=asc'
    result = sendGet('/api/v2/search', q)
    assertEq(2, result['count'])
    assertEq(stateIds['ticketTestSearch1'], result['results'][0]['id'])
    assertEq(stateIds['ticketTestSearch8'], result['results'][1]['id'])
