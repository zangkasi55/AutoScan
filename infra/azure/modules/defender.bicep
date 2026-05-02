// Microsoft Defender for Cloud subscription-scope plans.
// Deployed at subscription() scope from main.bicep.
targetScope = 'subscription'

var plans = [
  { name: 'CloudPosture',  tier: 'Standard', subPlan: '' }
  { name: 'VirtualMachines', tier: 'Standard', subPlan: '' }
  { name: 'StorageAccounts', tier: 'Standard', subPlan: '' }
  { name: 'SqlServers',    tier: 'Standard', subPlan: '' }
  { name: 'KeyVaults',     tier: 'Standard', subPlan: '' }
  { name: 'Containers',    tier: 'Standard', subPlan: '' }
  { name: 'AppServices',   tier: 'Standard', subPlan: '' }
  { name: 'Arm',           tier: 'Standard', subPlan: '' }
  { name: 'Api',           tier: 'Standard', subPlan: 'P1' }
  { name: 'CosmosDbs',     tier: 'Standard', subPlan: '' }
]

resource pricing 'Microsoft.Security/pricings@2024-01-01' = [for p in plans: {
  name: p.name
  properties: {
    pricingTier: p.tier
    subPlan: empty(p.subPlan) ? null : p.subPlan
  }
}]
