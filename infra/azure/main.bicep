// AutoScan / Sentry-AI — root infrastructure (subscription scope)
// Creates RG 'AutoScan' and deploys all platform services.
// PRD §02-prd.md, Architecture §05-architecture.md

targetScope = 'subscription'

@description('Azure region for all resources.')
param location string = 'eastus'

@description('Environment name (dev, staging, prod).')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Resource group name. Per user requirement: AutoScan.')
param resourceGroupName string = 'AutoScan'

@description('Short project name used as resource-name prefix.')
@maxLength(10)
param projectName string = 'autoscan'

@description('Object ID of the user/group that gets initial Key Vault Admin + Cosmos DB Operator. Replace via parameters file.')
param adminPrincipalObjectId string = ''

@description('Azure AD tenant id for OIDC AuthN on the API gateway.')
param tenantId string = subscription().tenantId

@description('Optional: existing Log Analytics workspace resource ID to reuse. Leave empty to create new.')
param existingLogAnalyticsId string = ''

@description('Optional: existing Azure OpenAI resource id (in same sub) to reuse. Leave empty to create new.')
param existingOpenAIId string = ''

@description('Optional: enable Microsoft Defender for Cloud plans (CSPM + Servers + Containers + Storage + KeyVault + Databases + AppServices).')
param enableDefenderPlans bool = true

@description('Deploy the Microsoft Sentinel solution onto the Log Analytics workspace.')
param enableSentinel bool = true

@description('Models to deploy in Azure OpenAI. Each entry: { name, version, sku, capacity }.')
param openAIDeployments array = [
  { name: 'gpt-4o',                version: '2024-11-20', sku: 'GlobalStandard', capacity: 50 }
  { name: 'gpt-4o-mini',           version: '2024-07-18', sku: 'GlobalStandard', capacity: 100 }
  { name: 'o1-mini',               version: '2024-09-12', sku: 'GlobalStandard', capacity: 30 }
  { name: 'text-embedding-3-large', version: '1',         sku: 'Standard',       capacity: 50 }
]

var tags = {
  project: 'AutoScan'
  product: 'Sentry-AI'
  environment: environment
  managedBy: 'bicep'
  costCenter: 'security'
}

// ───────────────────────── Resource Group ─────────────────────────
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// ───────────────────────── Modules ─────────────────────────
module identity 'modules/identity.bicep' = {
  scope: rg
  name: 'identity'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
  }
}

module logs 'modules/loganalytics.bicep' = {
  scope: rg
  name: 'logs'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
    existingLogAnalyticsId: existingLogAnalyticsId
    enableSentinel: enableSentinel
  }
}

module insights 'modules/appinsights.bicep' = {
  scope: rg
  name: 'insights'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
    workspaceId: logs.outputs.workspaceId
  }
}

module kv 'modules/keyvault.bicep' = {
  scope: rg
  name: 'kv'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
    tenantId: tenantId
    adminPrincipalObjectId: adminPrincipalObjectId
    workloadPrincipalId: identity.outputs.principalId
  }
}

module storage 'modules/storage.bicep' = {
  scope: rg
  name: 'storage'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
    workloadPrincipalId: identity.outputs.principalId
    workspaceId: logs.outputs.workspaceId
  }
}

module acr 'modules/acr.bicep' = {
  scope: rg
  name: 'acr'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
    workloadPrincipalId: identity.outputs.principalId
  }
}

module postgres 'modules/postgres.bicep' = {
  scope: rg
  name: 'postgres'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
    keyVaultName: kv.outputs.keyVaultName
  }
}

module cosmos 'modules/cosmos.bicep' = {
  scope: rg
  name: 'cosmos'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
    workloadPrincipalId: identity.outputs.principalId
  }
}

module openai 'modules/openai.bicep' = {
  scope: rg
  name: 'openai'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
    workloadPrincipalId: identity.outputs.principalId
    deployments: openAIDeployments
    existingOpenAIId: existingOpenAIId
  }
}

module aks 'modules/aks.bicep' = {
  scope: rg
  name: 'aks'
  params: {
    location: location
    projectName: projectName
    environment: environment
    tags: tags
    workspaceId: logs.outputs.workspaceId
    workloadIdentityResourceId: identity.outputs.resourceId
    acrId: acr.outputs.acrId
  }
}

module frontdoor 'modules/frontdoor.bicep' = {
  scope: rg
  name: 'frontdoor'
  params: {
    projectName: projectName
    environment: environment
    tags: tags
  }
}

module defender 'modules/defender.bicep' = if (enableDefenderPlans) {
  name: 'defender'
  scope: subscription()
  params: {
    workspaceId: logs.outputs.workspaceId
  }
}

// ───────────────────────── Outputs ─────────────────────────
output resourceGroupName string = rg.name
output workspaceId string = logs.outputs.workspaceId
output keyVaultUri string = kv.outputs.keyVaultUri
output acrLoginServer string = acr.outputs.loginServer
output aksName string = aks.outputs.aksName
output openAIEndpoint string = openai.outputs.endpoint
output postgresFqdn string = postgres.outputs.fqdn
output cosmosEndpoint string = cosmos.outputs.endpoint
output storageAccountName string = storage.outputs.accountName
output managedIdentityClientId string = identity.outputs.clientId
output frontDoorEndpoint string = frontdoor.outputs.endpointHostname
