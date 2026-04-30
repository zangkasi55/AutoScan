param location string
param projectName string
param environment string
param tags object
param existingLogAnalyticsId string = ''
param enableSentinel bool = true

var workspaceName = '${projectName}-${environment}-law'
var createNew = empty(existingLogAnalyticsId)

resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = if (createNew) {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 90
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
  }
}

// Microsoft Sentinel on top of the workspace (enables SecurityInsights solution).
resource sentinel 'Microsoft.OperationsManagement/solutions@2015-11-01' = if (createNew && enableSentinel) {
  name: 'SecurityInsights(${workspaceName})'
  location: location
  tags: tags
  plan: {
    name: 'SecurityInsights(${workspaceName})'
    publisher: 'Microsoft'
    product: 'OMSGallery/SecurityInsights'
    promotionCode: ''
  }
  properties: {
    workspaceResourceId: law.id
  }
}

output workspaceId string = createNew ? law.id : existingLogAnalyticsId
output workspaceName string = createNew ? law.name : last(split(existingLogAnalyticsId, '/'))
