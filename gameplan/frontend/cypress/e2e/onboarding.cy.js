describe('Onboarding', () => {
  it('onboarding works', () => {
    cy.login()
    cy.request({
      method: 'POST',
      url: '/api/method/gameplan.test_api.clear_data',
    })
    cy.visit('/g')
    cy.url().should('include', '/onboarding')

    cy.get('input[placeholder*=Townhall]').type('Marketing')
    cy.get('button').contains('Continue').click()
    cy.get('a:contains("Marketing")').should('exist')
  })
})
