param location string
param projectName string
param environment string
param tags object
param workloadPrincipalId string
param workspaceId string

var name = take(toLower(replace('${projectName}${environment}sa${uniqueString(resourceGroup().id)}', '-', '')), 24)

resource sa 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  sku: { name: 'Standard_GRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    allowSharedKeyAccess: false
    encryption: {
      keySource: 'Microsoft.Storage'
      services: {
        blob: { enabled: true, keyType: 'Account' }
        file: { enabled: true, keyType: 'Account' }
      }
      requireInfrastructureEncryption: true
    }
  }
}

resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: sa
  name: 'default'
  properties: {
    isVersioningEnabled: true
    changeFeed: { enabled: true }
    deleteRetentionPolicy: { enabled: true, days: 30 }
    containerDeleteRetentionPolicy: { enabled: true, days: 30 }
  }
}

var containers = [
  'evidence-raw'           // sealed raw artifacts (HSM-wrapped customer key in v1)
  'evidence-redacted'      // PII-redacted view
  'reports'                // generated PDFs / HTML
  'roe-documents'          // signed RoE JWS
  'tool-outputs'           // raw scanner outputs (short-lived)
  'sboms'                  // CycloneDX / SPDX
]

resource c 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [for n in containers: {
  parent: blobs
  name: n
  properties: {
    publicAccess: 'None'
    metadata: { product: 'AutoScan' }
  }
}]

// Storage Blob Data Contributor for the workload UAMI.
var roleStorageBlobDataContributor = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
resource blobAssign 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: sa
  name: guid(sa.id, workloadPrincipalId, roleStorageBlobDataContributor)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleStorageBlobDataContributor)
    principalId: workloadPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Diagnostic settings → Log Analytics
resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: blobs
  name: 'to-law'
  properties: {
    workspaceId: workspaceId
    logs: [
      { category: 'StorageRead',   enabled: true }
      { category: 'StorageWrite',  enabled: true }
      { category: 'StorageDelete', enabled: true }
    ]
    metrics: [{ category: 'Transaction', enabled: true }]
  }
}

output accountName string = sa.name
output accountId string = sa.id
output blobEndpoint string = sa.properties.primaryEndpoints.blob
