param location string
param projectName string
param environment string
param tags object
param tenantId string
param adminPrincipalObjectId string = ''
param workloadPrincipalId string

var kvName = take(toLower(replace('${projectName}-${environment}-kv-${uniqueString(resourceGroup().id)}', '_', '-')), 24)

resource kv 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: kvName
  location: location
  tags: tags
  properties: {
    tenantId: tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Built-in role IDs
var roleKeyVaultAdmin           = '00482a5a-887f-4fb3-b363-3b7fe8e74483'
var roleKeyVaultSecretsUser     = '4633458b-17de-408a-b874-0445c86b69e6'

resource adminAssign 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(adminPrincipalObjectId)) {
  scope: kv
  name: guid(kv.id, adminPrincipalObjectId, roleKeyVaultAdmin)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleKeyVaultAdmin)
    principalId: adminPrincipalObjectId
    principalType: 'User'
  }
}

resource workloadAssign 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: kv
  name: guid(kv.id, workloadPrincipalId, roleKeyVaultSecretsUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleKeyVaultSecretsUser)
    principalId: workloadPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output keyVaultName string = kv.name
output keyVaultId string = kv.id
output keyVaultUri string = kv.properties.vaultUri
