@description('User-assigned managed identity used by all AutoScan workloads (workload identity on AKS, KV access, Cosmos DB data plane, Storage, Azure OpenAI).')
param location string
param projectName string
param environment string
param tags object

var name = '${projectName}-${environment}-uami'

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: name
  location: location
  tags: tags
}

output resourceId string = uami.id
output principalId string = uami.properties.principalId
output clientId string = uami.properties.clientId
output name string = uami.name
