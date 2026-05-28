describe('Discussion', () => {
  it('all discussion actions', () => {
    cy.login()
    cy.request({
      method: 'POST',
      url: '/api/method/gameplan.test_api.clear_data?onboard=1',
    })
    cy.request('POST', '/api/method/frappe.client.insert_many', {
      docs: [
        {
          doctype: 'GP Team',
          title: 'Engineering',
        },
        {
          doctype: 'GP Project',
          title: 'Gameplan',
          team: 'engineering',
        },
        {
          doctype: 'GP Project',
          title: 'ERPNext',
          team: 'engineering',
        },
      ],
    })
      .its('body.message')
      .as('data')
      .then((data) => {
        cy.visit(`/g/space/${data[1]}`)
      })

    // publish draft discussion
    cy.intercept({
      method: 'POST',
      url: '/api/v2/document/GP%20Draft/*/method/publish',
      times: 1,
    }).as('discussionId')

    cy.contains('div', 'No discussions')

    // cy.button('View all').click()
    cy.button('Add new').click()
    cy.get('textarea').type('Starting a new discussion')
    cy.get('div[contenteditable=true]').click().type('This is content for new discussion{enter}')
    cy.get('button').contains('Publish').click()
    cy.wait('@discussionId')
      .its('response.body.data')
      .then((discussionId) => {
        cy.url().should('include', `/discussion/${discussionId}/starting-a-new-discussion`)
      })

    // add comment
    cy.intercept('POST', '/api/v2/document/GP%20Comment').as('comment')
    cy.button('Add a comment').click()
    cy.focused().type('This is the first comment{enter}')
    cy.button('Submit').click()
    cy.wait('@comment')
      .its('response.body.data')
      .then((comment) => {
        cy.get(`div[data-id="${comment.name}"]`).should('exist')
      })

    // edit title
    cy.selectDropdownOption('Discussion Options', 'Edit')
    cy.get('input[placeholder="Title"]')
      .type(' {selectall}', { delay: 200 })
      .type('Edited Discussion Title')
    cy.button('Submit').click()
    cy.get('h1:contains("Edited Discussion Title")').should('exist')
    cy.contains('changed the title from').should('exist')

    // edit content
    cy.selectDropdownOption('Discussion Options', 'Edit')
    cy.get('[contenteditable=true]')
      .type('{enter}{enter}', { delay: 200 })
      .type('adding more content')
    cy.button('Submit').click()
    cy.get('p:contains("adding more content")').should('exist')

    // move to another project
    cy.selectDropdownOption('Discussion Options', 'Move to...')
    cy.selectCombobox('Select a project', 'ERPNext')
    cy.button('Move to ERPNext').click()

    cy.get('@data').then((data) => {
      let erpnextProject = data[2]
      cy.get('@discussionId')
        .its('response.body.data')
        .then((discussionId) => {
          cy.url().should('include', `/g/space/${erpnextProject}/discussion/${discussionId}`)
        })
    })

    // close discussion
    cy.selectDropdownOption('Discussion Options', 'Close discussion')
    cy.dialog('button').contains('Close').click()
    cy.contains('closed this discussion').should('exist')
    cy.button('Add a comment').should('not.exist')
  })
})
