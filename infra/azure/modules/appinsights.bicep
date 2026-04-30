param location string
param projectName string
param environment string
param tags object
param workspaceId string

resource ai 'Microsoft.Insights/components@2020-02-02' = {
  name: '${projectName}-${environment}-appi'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspaceId
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output appInsightsId string = ai.id
output connectionString string = ai.properties.ConnectionString
