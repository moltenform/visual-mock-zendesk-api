from test_helpers import *


def go4TicketsCreateMany():
    # author defaults
    #     requester set, author set (comment1)
    #     requester set, author not set but prev is (comment2)
    #     requester set, author not set (testAuthorId1)
    #     requester not set, author set  (testAuthorId2)
    #     requester not set, author not set but prev is (testAuthorId3)
    #     requester not set, author not set (plainStringComment2)

    # note that if comment isn't set, zendesk api will ask for a 'description',
    # this is misleading because a description passed in will also create a first comment.
    s = r'''{
    "tickets": [
      {
        "subject": "ticket1",
        "created_at": "2022-01-01T06:38:32.399Z",
        "requester_id": %USER1%,
        "status": "pending", ### note ids are sometimes quoted, sometimes not, need to support both
        "custom_fields": [{"id":"%FLDID1%", "value":"fldval1"}, {"id":%FLDID2%, "value":"fldval2"}],
        "tags": ["tag1", "tag2"],
        "comments": [
          {
            "created_at": "2022-01-02T06:38:32.399Z",
            "body": "comment1",
            "public": false,
            "author_id": %USER2%
          },
          {
            "created_at": "2022-01-03T06:38:32.399Z",
            "body": "comment2",
            "public": true
            ### test missing authorid: author will be api-user
          }
        ]
      },
      {
        "subject": "ticket2",
        "created_at": "2022-01-01T06:38:32.399Z",
        "requester": {"name":"utest4inline", "email": "utest4inline@a.com"}, ### inline user creation
        "tags": ["tag1", "tag2"],
        "comment": {"body": "plainStringComment1"} ### comment syntax shortcut, comment not comments
        ### status default to open
        ### comments default to public=true
        ### test missing authorid: author will be utest4inline
      },
      {
        "comment": "plainStringComment2", ### comment syntax shortcut, string data type
        "tags": ["tag1", "tag2", "%TAG_REMOVED_BY_TRIGGER%"] ### we'll remove it
        ### test missing authorid: author will be api-user
      },
      {
        "requester_id": %USER2%,
        "submitter_id": %USER3%,
        "comments": [{"body": "testAuthorId1"}]
        ### test missing authorid: author will be user2
      },
      {
        "comments": [
            ### careful, must add a created_at or the created_at will be the same causing the order to be arbitrary
            {"body": "testAuthorId2", "author_id": "%USER1%", "created_at": "2022-03-01T06:38:32.399Z"}, ### test missing authorid: author will be user1
            {"body": "testAuthorId3"}] ### test missing authorid: author will be api-user
      },
      {
        "requester_id": %USER1%,
        "comments": [{"body": "testAuthorIdUpdate", "author_id": "%USER2%"}],
        "tags": ["%TAG_REMOVED_BY_TRIGGER%"] ### we won't remove it because we'll add a private comment
      }
    ]
  }'''

    s = subInTemplates(s)
    result = sendPostAndGetJob('/api/v2/imports/tickets/create_many', s)
    assertEq(6, len(result['results']))
    testBatchResults(result, action=None, status=None, hasSuccess=True)
    for i in range(6):
        assertEq(i, result['results'][i]['index'])
        stateIds[f'ticket{i+1}'] = int(result['results'][i]['id'])

    ############## Confirm inline user got created ###################
    result = sendGet('/api/v2/users/search', 'query=email:utest4inline@a.com')
    assertEq(1, result['count'])
    assertEq(1, len(result['users']))
    assertTrue(int(result['users'][0]['id']) > 0)
    assertEq('utest4inline', result['users'][0]['name'])
    assertEq('utest4inline@a.com', result['users'][0]['email'])
    stateIds['user4inline'] = int(result['users'][0]['id'])
