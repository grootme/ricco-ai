describe('Project', () => {
  it('project creation, move to team and archive', () => {
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
          doctype: 'GP Team',
          title: 'DevOps',
        },
      ],
    })

    cy.visit('/g/spaces')

    cy.intercept('POST', '/api/v2/document/GP%20Project').as('project')
    cy.button('Add new').click()
    cy.get('input[placeholder="Space name"]').type('Project 1')
    cy.get('button').contains('Submit').click()
    cy.get('a:contains("Project 1")').click()
    cy.get('header a:contains("Project 1")').should('exist')
    cy.wait('@project')
      .its('response.body.data')
      .then((project) => {
        cy.url().should('include', `/g/space/${project.name}`)

        // move to category
        cy.visit('/g/spaces')
        cy.selectDropdownOption(`${project.title} Space Options`, 'Change Category')
        cy.selectCombobox('Select a category', 'DevOps')
        cy.button('Move to DevOps').click()
        cy.scope('body').find('a:contains("Project 1")').click()
        cy.get('header a:contains("DevOps")').should('exist')

        // archive
        cy.visit('/g/spaces')
        cy.selectDropdownOption(`${project.title} Space Options`, 'Archive')
        cy.scope('dialog').button('Archive').click()
        cy.contains('div', 'Archived').should('exist')
        cy.visit('/g/spaces')
        cy.contains('a', 'Project 1').should('not.exist')
        cy.get('button:contains("Archived")').click()
        cy.contains('a', 'Project 1').should('exist')
      })
  })
})
