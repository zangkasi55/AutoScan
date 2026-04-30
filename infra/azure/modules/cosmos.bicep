@description('Cosmos DB (Gremlin API) for the Asset Graph. Neo4j is deferred to Phase 2 per architecture §3.6.')
param location string
param projectName string
param environment string
param tags object
param workloadPrincipalId string

var account = take(toLower('${projectName}-${environment}-cosmos-${uniqueString(resourceGroup().id)}'), 44)

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' = {
  name: account
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    capabilities: [
      { name: 'EnableGremlin' }
      { name: 'EnableServerless' }
    ]
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    locations: [{ locationName: location, failoverPriority: 0 }]
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    minimalTlsVersion: 'Tls12'
  }
}

resource gremlinDb 'Microsoft.DocumentDB/databaseAccounts/gremlinDatabases@2024-11-15' = {
  parent: cosmos
  name: 'asset-graph'
  properties: { resource: { id: 'asset-graph' } }
}

resource graph 'Microsoft.DocumentDB/databaseAccounts/gremlinDatabases/graphs@2024-11-15' = {
  parent: gremlinDb
  name: 'assets'
  properties: {
    resource: {
      id: 'assets'
      partitionKey: { paths: ['/tenantId'], kind: 'Hash' }
      indexingPolicy: { indexingMode: 'consistent', automatic: true }
    }
  }
}

// Cosmos DB built-in Data Contributor for the workload UAMI (data plane).
resource dataAssign 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = {
  parent: cosmos
  name: guid(cosmos.id, workloadPrincipalId, 'data-contributor')
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: workloadPrincipalId
    scope: cosmos.id
  }
}

output endpoint string = cosmos.properties.documentEndpoint
output accountName string = cosmos.name
