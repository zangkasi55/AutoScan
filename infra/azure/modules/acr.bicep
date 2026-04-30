param location string
param projectName string
param environment string
param tags object
param workloadPrincipalId string

var name = take(toLower(replace('${projectName}${environment}acr${uniqueString(resourceGroup().id)}', '-', '')), 50)

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: { name: 'Premium' }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: 'Disabled'
    policies: {
      retentionPolicy: { status: 'enabled', days: 30 }
      trustPolicy:    { type: 'Notary', status: 'enabled' }
      quarantinePolicy:{ status: 'enabled' }
    }
  }
}

var roleAcrPull = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
resource pullAssign 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, workloadPrincipalId, roleAcrPull)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleAcrPull)
    principalId: workloadPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output acrId string = acr.id
output loginServer string = acr.properties.loginServer
