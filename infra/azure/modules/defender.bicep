// Microsoft Defender for Cloud subscription-scope plans.
// Deployed at subscription() scope from main.bicep.
targetScope = 'subscription'

@description('Log Analytics workspace resource ID for security data.')
param workspaceId string

var plans = [
  { name: 'CloudPosture',          tier: 'Standard' }
  { name: 'VirtualMachines',       tier: 'Standard' }
  { name: 'StorageAccounts',       tier: 'Standard' }
  { name: 'SqlServers',            tier: 'Standard' }
  { name: 'KeyVaults',             tier: 'Standard' }
  { name: 'Containers',            tier: 'Standard' }
  { name: 'AppServices',           tier: 'Standard' }
  { name: 'Arm',                   tier: 'Standard' }
  { name: 'Api',                   tier: 'Standard' }
  { name: 'CosmosDbs',             tier: 'Standard' }
]

resource pricing 'Microsoft.Security/pricings@2024-01-01' = [for p in plans: {
  name: p.name
  properties: { pricingTier: p.tier }
}]

// Auto-provision Defender agent / MMA on VMs (legacy still applies for some plans).
resource autoProv 'Microsoft.Security/autoProvisioningSettings@2017-08-01-preview' = {
  name: 'default'
  properties: { autoProvision: 'On' }
}

// Configure default workspace for security data collection.
resource workspaceSetting 'Microsoft.Security/workspaceSettings@2017-08-01-preview' = {
  name: 'default'
  properties: {
    workspaceId: workspaceId
    scope: subscription().id
  }
}
