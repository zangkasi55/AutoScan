@description('Front Door Standard for the Web UI / API gateway. Origin wired in Phase 2 once Ingress IP is allocated.')
param projectName string
param environment string
param tags object

var profile = '${projectName}-${environment}-fd'

resource fd 'Microsoft.Cdn/profiles@2024-09-01' = {
  name: profile
  location: 'global'
  tags: tags
  sku: { name: 'Standard_AzureFrontDoor' }
  properties: {}
}

resource ep 'Microsoft.Cdn/profiles/afdEndpoints@2024-09-01' = {
  parent: fd
  name: 'autoscan'
  location: 'global'
  properties: { enabledState: 'Enabled' }
}

output endpointHostname string = ep.properties.hostName
