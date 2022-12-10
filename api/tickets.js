import { addJobResultToMemory, generateTicketId, getCurrentTimestamp, normalizeId } from "./helpers.js"
import { insertPersistedComment, insertPersistedTicket, insertPersistedUser, updatePersistedTicket, validateInternalTicket } from "./schema.js"
import assert from "assert";
import lodash from 'lodash'
import { getDefaultAdminId, getGlobalState, getGlobalStateCopy, saveGlobalState } from "../persist.js"
import { renderPendingJob } from "./jobresults.js"
import {  transformIncomingUserIntoInternal, usersSearchByEmailImpl } from "./users.js"
import { allowShortcutStringComment, transformIncomingCommentIntoInternal } from "./comments.js"
import { runTriggersOnNewCommentPosted } from "./triggers.js"
import { intCustomFields } from "./customfields.js";


// It's semi un-documented, but some ticket apis, especially the batch ones,
// let you create a new user inline, for example instead of providing
// requester_id: 234, providing requester: { name: 'name', email: 'example@example.com'}
// this function implements this feature.
function allowInlineNewUser(globalState, obj, keyToUse, keyId) {
    if (obj[keyToUse]) {
        const em = obj[keyToUse].email
        const nm = obj[keyToUse].name
        if (!em || !nm) {
            throw new Error(`attempted inline User but did not pass in an email or name`)
        }
        
        const foundByEmail = usersSearchByEmailImpl(globalState, em)?.users
        if (foundByEmail?.length) {
            const foundByName = foundByEmail.find(user=>user.name === nm)
            if (foundByName) {
                obj[keyId] = normalizeId(foundByName.id)
            } else {
                throw new Error(`attempted inline User but did name does not match existing user with this email`)
            }
        } else {
            const resultUser = transformIncomingUserIntoInternal(globalState, {name: nm, email:em})
            insertPersistedUser(globalState, resultUser)
            console.log(`created inline User`)
            obj[keyId] = resultUser.id
        }
    }

    if (obj[keyId]) {
        obj[keyId] = normalizeId(obj[keyId])
    }
}

export function apiTicketsImportCreateMany(payload) {
    // because this is an 'import' api, we allow setting createdat
    const globalState = getGlobalStateCopy()
    const response = []
    for (let [index, ticket] of payload.tickets.entries()) {
        allowInlineNewUser(globalState, ticket, 'requester', 'requester_id')
        allowInlineNewUser(globalState, ticket, 'submitter', 'submitter_id')
        const resultTicket = transformIncomingTicketImportIntoInternal(globalState, ticket)
        resultTicket.comment_ids = []
        if (ticket.comment) {
            // Zendesk allows this shorthand
            ticket.comments = [ticket.comment]
        }
        for (let comment of (ticket.comments||[])) {
            comment = allowShortcutStringComment(comment)
            allowInlineNewUser(globalState, comment, 'author', 'author_id')
            const c = transformIncomingCommentIntoInternal(globalState, comment, normalizeId(resultTicket.requester_id))
            insertPersistedComment(globalState, c)
            resultTicket.comment_ids.push(c.id)
            // Because this is 'import create many', not 'standard create many', skip triggers
        }

        insertPersistedTicket(globalState, resultTicket)
        response.push({index: index, id: resultTicket.id, account_id: "not yet implemented", "success": true /* extra */})
    }

    // Because this is 'import create many', not 'standard create many', skip triggers
    const newJobId = addJobResultToMemory(globalState, response)
    const finalResponse = renderPendingJob(newJobId)
    saveGlobalState(globalState)
    return finalResponse
}

export function apiTicketUpdateMany(payload) {
    const globalState = getGlobalStateCopy()
    const response = []

    for (let [index, ticket] of payload.tickets.entries()) {
        ticket.id = normalizeId(ticket.id)
        const existing = globalState.persistedState.tickets[ticket.id]
        if (!existing) {
            throw new Error(`cannot update, ticket id ${ticket.id} not found`)
        }

        const resultTicket = transformIncomingTicketUpdateIntoInternal(existing, ticket)
        if (ticket.comments) {
            throw new Error(`you can only set comments when importing`)
        }
        if (ticket.comment) {
            ticket.comment = allowShortcutStringComment(ticket.comment)
            if (ticket.comment.created_at) {
                throw new Error(`you can only set created_at when importing`)
            }

            allowInlineNewUser(globalState, ticket.comment, 'author', 'author_id')
            const c = transformIncomingCommentIntoInternal(globalState, ticket.comment, normalizeId(resultTicket.requester_id))
            insertPersistedComment(globalState, c)
            resultTicket.comment_ids.push(c.id)
            runTriggersOnNewCommentPosted(globalState, resultTicket, c)
        }

        updatePersistedTicket(globalState, resultTicket)
        response.push({index: index, id: resultTicket.id, "action":"update","status":"Updated","success":true})
    }

    const newJobId = addJobResultToMemory(globalState, response)
    const finalResponse = renderPendingJob(newJobId)
    saveGlobalState(globalState)
    return finalResponse
}

export function apiTicketsShowMany(payload) {
    const globalState = getGlobalState()
    const ids = payload.split(',')
    const result = []
    for (let id of ids) {
        id = normalizeId(id)
        if (!globalState.persistedState.tickets[id]) {
            console.log(`ticket not found ${id}`)
            continue
        }
        result.push(globalState.persistedState.tickets[id])
    }
    return {tickets: result}
}


function transformIncomingTicketUpdateIntoInternal(existing, incomingUpdate) {
    existing = {...existing}
    if (existing.status == 'closed') {
        throw new Error('cannot update a closed ticket')
    }
    if (incomingUpdate.subject) {
        existing.subject = incomingUpdate.subject
    }
    if (incomingUpdate.assignee_email||
        incomingUpdate.group_id||incomingUpdate.organization_id||incomingUpdate.collaborator_ids ||
        incomingUpdate.additional_collaborators||incomingUpdate.followers||incomingUpdate.priority||incomingUpdate.email_ccs) {
        throw new Error("cannot update this property, not yet implemented")
    }

    /* interestingly we can update these */
    if (incomingUpdate.requester_id) {
        existing.requester_id = normalizeId(incomingUpdate.requester_id)
    }
    if (incomingUpdate.assignee_id) {
        existing.assignee_id = normalizeId(incomingUpdate.assignee_id)
    }

    if (incomingUpdate.status) {
        existing.status = incomingUpdate.status
    }
    if (incomingUpdate.additional_tags) { // less documented, but does work on latest api
        assert(Array.isArray(incomingUpdate.additional_tags), 'additional_tags must be an array')
        existing.tags = [...incomingUpdate.additional_tags, ...existing.tags]
        existing.tags = lodash.uniq(existing.tags)
    }
    if (incomingUpdate.remove_tags) { // less documented, but does work on latest api
        assert(Array.isArray(incomingUpdate.remove_tags), 'remove_tags must be an array')
        existing.tags = existing.tags.filter(t=>!incomingUpdate.remove_tags.includes(t))
    }
    if (incomingUpdate.tags) {
        existing.tags = incomingUpdate.tags
    }
    if (incomingUpdate.external_id||incomingUpdate.problem_id||incomingUpdate.due_at||
        incomingUpdate.updated_stamp||incomingUpdate.sharing_agreement_ids||incomingUpdate.macro_ids ||
        incomingUpdate.attribute_value_ids) {
        throw new Error("cannot update this property, not yet implemented")
    }
    intCustomFields(incomingUpdate.custom_fields)
    if (incomingUpdate.custom_fields) {
        // confirmed in zendesk api that this merges in, not replaces
        existing.custom_fields = [...incomingUpdate.custom_fields, ...existing.custom_fields]
        existing.custom_fields = lodash.uniqBy(existing.custom_fields, fld=>fld.id)
    }
    
    // ignore safe_update for now, would be good to implement in the future for testing race conditions
    existing.updated_at = getCurrentTimestamp()
    return existing
}

 // Ticket.CreateModel
function transformIncomingTicketImportIntoInternal(globalState, obj) {
    assert(!obj.id, `new ticket - cannot specify id`)
    if (obj.external_id || obj.type ||  obj.priority || obj.recipient 
        || obj.organization_id || obj.group_id || obj.collaborator_ids || obj.collaborators || 
        obj.follower_ids || obj.email_cc_ids || obj.via_followup_source_id || obj.macro_ids ||
         obj.ticket_form_id || obj.brand_id) {
        throw new Error("cannot set this property, not yet implemented")
    }
    if (obj.fields) {
        throw new Error("cannot set fields, not yet implemented")
    }
    intCustomFields(obj.custom_fields)
    return {
        id: generateTicketId(globalState.persistedState),
        created_at: obj.created_at || getCurrentTimestamp(),
        updated_at: obj.updated_at ||obj.created_at || getCurrentTimestamp(),
        subject: (obj.subject || obj.raw_subject || '(no subject given)'),
        raw_subject: (obj.subject || obj.raw_subject || '(no subject given)'),
        status: obj.status || 'open',
        description: obj.description || '(no description given)',
        requester_id: normalizeId(obj.requester_id || getDefaultAdminId()),
        submitter_id: normalizeId(obj.submitter_id || obj.requester_id || getDefaultAdminId()),
        assignee_id: normalizeId(obj.assignee_id || getDefaultAdminId()),
        tags: obj.tags || [],
        custom_fields: obj.custom_fields || [],
        fields: obj.fields || [],
        is_public: (obj.is_public === undefined) ? true : obj.is_public
    }
}
