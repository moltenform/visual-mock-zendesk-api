/**
 * (This file is run in browser context, not node.)
 * 
 * Conveniently, the existing api calls give us everything we need.
 * 
 * Load feather icons.
 */
(function () {
    'use strict'
    feather.replace()
})()

/**
 * Hard-coded admin user id
 */
const DefaultAdminId = 111

/**
 * Delete all tickets
 */
async function onBtnDeleteAllTickets() {
    if (confirm("Clear test data, by deleting tickets?")) {
        await callApi('/api/delete_all_tickets')
    }
}

/**
 * Delete all state - including tickets and users
 */
async function onBtnDeleteAllTicketsAndUsers() {
    if (confirm("Clear test data, by deleting tickets and users?")) {
        await callApi('/api/delete_all')
    }
}

/**
 * Create a new comment on the ticket
 */
async function onBtnPostReply() {
    let txt = prompt('Reply with what text?')
    if (!txt) {
        return
    }

    let isPublic = prompt('Is this a public message? y/n', 'y')
    if (!isPublic) {
        return
    }

    isPublic = isPublic && isPublic.toLowerCase() === 'y'
    const payload = {
        tickets: [{
            id: inferCurrentTicketId(),
            comment: {
                author_id: DefaultAdminId,
                body: txt,
                public: isPublic
            }
        }]
    }

    // because we are calling through this api, this will correctly cause triggers to run
    await callApi('/api/v2/tickets/update_many.json', 'post', payload)
}

/**
 * Set the ticket status
 */
async function onBtnSetStatus(newStatus) {
    const payload = {
        tickets: [{
            id: inferCurrentTicketId(),
            status: newStatus
        }]
    }

    await callApi('/api/v2/tickets/update_many.json', 'post', payload)
}

/**
 * Set tags on the ticket
 */
async function onBtnSetTags() {
    let txt = prompt('Enter tags, separated by ;', 'tag1;tag2;tag3')
    if (!txt) {
        return
    }

    const payload = {
        tickets: [{
            id: inferCurrentTicketId(),
            tags: txt.split(';')
        }]
    }

    await callApi('/api/v2/tickets/update_many.json', 'post', payload)
}

/**
 * Get the ticket we are editing by looking at current url
 */
function inferCurrentTicketId() {
    let currentLocation = window.location.toString()
    const pts = currentLocation.split('tickets/')
    if (pts.length <= 1) {
        alert('Could not find current ticket id')
        throw new Error('Could not find current ticket id')
    }

    if (Number.isNaN(parseInt(pts[1]))) {
        alert('Could not parse current ticket id')
        throw new Error('Could not parse current ticket id')
    }

    return parseInt(pts[1])
}

/**
 * Make an api call
 */
async function callApi(endpoint, method = 'post', payload = undefined, manual = false) {
    if (manual) {
        const obj = JSON.stringify(payload || {})
        const s = `curl 'localhost:8999${endpoint}' -H "Content-Type: application/json" -X POST -d '${obj}'`
        prompt('You can run the following:', s)
        return
    }

    let options = {
        method: method,
        headers: {
            "Content-Type": "application/json",
            'Accept': 'application/json, text/plain, */*',
        },
        body: JSON.stringify(payload || {})
    }

    let response = await fetch(endpoint, options)
    if (response.status >= 200 && response.status < 300) {
        alert('API call succeeded.')
        setTimeout(() => location.reload(), 100)
    } else {
        let output = await response.text();
        alert('API call failed, details: ' + output)
        setTimeout(() => location.reload(), 100)
    }
}
