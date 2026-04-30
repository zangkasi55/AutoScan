@description('Azure OpenAI account + per-model deployments used by specialist agents and report writer.')
param location string
param projectName string
param environment string
param tags object
param workloadPrincipalId string
param deployments array
param existingOpenAIId string = ''

var createNew = empty(existingOpenAIId)
var name = take(toLower('${projectName}-${environment}-aoai-${uniqueString(resourceGroup().id)}'), 60)

resource aoai 'Microsoft.CognitiveServices/accounts@2024-10-01' = if (createNew) {
  name: name
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
    networkAcls: { defaultAction: 'Allow' }
  }
}

@batchSize(1)
resource d 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [for dep in deployments: if (createNew) {
  parent: aoai
  name: dep.name
  sku: { name: dep.sku, capacity: dep.capacity }
  properties: {
    model: { format: 'OpenAI', name: dep.name, version: dep.version }
    raiPolicyName: 'Microsoft.DefaultV2'
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}]

// Cognitive Services OpenAI User role for the workload UAMI.
var roleOpenAIUser = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
resource userAssign 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (createNew) {
  scope: aoai
  name: guid(aoai.id, workloadPrincipalId, roleOpenAIUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleOpenAIUser)
    principalId: workloadPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output endpoint string = createNew ? aoai.properties.endpoint : ''
output resourceId string = createNew ? aoai.id : existingOpenAIId
