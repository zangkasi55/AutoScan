@description('Managed AKS cluster running orchestrator, specialists, MCP servers, and policy engine. Workload identity + OIDC issuer enabled.')
param location string
param projectName string
param environment string
param tags object
param workspaceId string
param workloadIdentityClientId string
param workloadIdentityResourceId string
param acrId string
param kubernetesVersion string = '1.30.5'

var name = '${projectName}-${environment}-aks'

resource aks 'Microsoft.ContainerService/managedClusters@2024-09-01' = {
  name: name
  location: location
  tags: tags
  sku: { name: 'Base', tier: 'Standard' }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${workloadIdentityResourceId}': {} }
  }
  properties: {
    kubernetesVersion: kubernetesVersion
    dnsPrefix: '${projectName}-${environment}'
    enableRBAC: true
    oidcIssuerProfile: { enabled: true }
    securityProfile: {
      workloadIdentity: { enabled: true }
      defender: {
        logAnalyticsWorkspaceResourceId: workspaceId
        securityMonitoring: { enabled: true }
      }
      imageCleaner: { enabled: true, intervalHours: 168 }
    }
    addonProfiles: {
      omsagent: {
        enabled: true
        config: { logAnalyticsWorkspaceResourceID: workspaceId }
      }
      azurepolicy: { enabled: true }
      azureKeyvaultSecretsProvider: {
        enabled: true
        config: { enableSecretRotation: 'true' }
      }
    }
    agentPoolProfiles: [
      {
        name: 'system'
        mode: 'System'
        count: 2
        vmSize: 'Standard_D4ds_v5'
        osDiskType: 'Ephemeral'
        osType: 'Linux'
        type: 'VirtualMachineScaleSets'
        availabilityZones: ['1','2','3']
        upgradeSettings: { maxSurge: '33%' }
      }
      {
        name: 'workload'
        mode: 'User'
        count: 2
        vmSize: 'Standard_D4ds_v5'
        osDiskType: 'Ephemeral'
        osType: 'Linux'
        nodeLabels: { workload: 'autoscan' }
        nodeTaints: ['workload=autoscan:NoSchedule']
        type: 'VirtualMachineScaleSets'
        availabilityZones: ['1','2','3']
        enableAutoScaling: true
        minCount: 2
        maxCount: 10
        upgradeSettings: { maxSurge: '33%' }
      }
      {
        name: 'sandbox'
        mode: 'User'
        count: 0
        vmSize: 'Standard_D4ds_v5'
        osDiskType: 'Ephemeral'
        osType: 'Linux'
        nodeLabels: { workload: 'sandbox', isolation: 'gvisor' }
        nodeTaints: ['workload=sandbox:NoSchedule']
        type: 'VirtualMachineScaleSets'
        enableAutoScaling: true
        minCount: 0
        maxCount: 20
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      networkPolicy: 'cilium'
      networkDataplane: 'cilium'
      loadBalancerSku: 'standard'
      serviceCidr: '10.250.0.0/16'
      dnsServiceIP: '10.250.0.10'
    }
    autoUpgradeProfile: {
      upgradeChannel: 'patch'
      nodeOSUpgradeChannel: 'NodeImage'
    }
  }
}

// AcrPull for kubelet identity to ACR
var roleAcrPull = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
resource acrPullAssign 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aks.id, acrId, 'acr-pull')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleAcrPull)
    principalId: aks.properties.identityProfile.kubeletidentity.objectId
    principalType: 'ServicePrincipal'
  }
}

output aksName string = aks.name
output oidcIssuer string = aks.properties.oidcIssuerProfile.issuerURL
output kubeletIdentity string = aks.properties.identityProfile.kubeletidentity.objectId
