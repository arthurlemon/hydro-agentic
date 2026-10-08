// Search Free uniquement. Entra ID; aucune clé ni capacité payante.
param serviceName string = 'hydro-search-c80f4df6'
param location string = 'canadacentral'
param principalId string
param createRoleAssignments bool = false

resource search 'Microsoft.Search/searchServices@2025-05-01' = {
  name: serviceName
  location: location
  tags: { project: 'hydro-agentic', environment: 'poc' }
  sku: { name: 'free' }
  properties: {
    replicaCount: 1
    partitionCount: 1
    disableLocalAuth: true
    publicNetworkAccess: 'enabled'
    semanticSearch: 'disabled'
  }
}

var roles = [
  '7ca78c08-252a-4471-8644-bb5ff32d4ba0' // Search Service Contributor : administrer l’index
  '8ebe5a00-799e-43f5-93ac-243d3dce84a7' // Search Index Data Contributor : indexer et lire
]

resource grants 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for role in roles: if (createRoleAssignments) {
  name: guid(search.id, principalId, role)
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', role)
    principalId: principalId
    principalType: 'User'
  }
}]

output endpoint string = 'https://${search.name}.search.windows.net'
