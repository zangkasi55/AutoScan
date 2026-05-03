@description('Postgres Flexible Server for the Evidence Ledger (append-only, hash-chained) and findings store.')
param location string
param projectName string
param environment string
param tags object
param keyVaultName string

@secure()
@description('Initial Postgres admin password. Stored to Key Vault secret evidence-pg-admin-password.')
param adminPassword string = newGuid()

var serverName = take(toLower('${projectName}-${environment}-pgsql-${uniqueString(resourceGroup().id)}'), 60)
var dbName = 'evidence'

resource pg 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: serverName
  location: location
  tags: tags
  sku: { name: 'Standard_D2ds_v5', tier: 'GeneralPurpose' }
  properties: {
    administratorLogin: 'avsadmin'
    administratorLoginPassword: adminPassword
    version: '16'
    storage: { storageSizeGB: 128, autoGrow: 'Enabled' }
    backup: { backupRetentionDays: 35, geoRedundantBackup: 'Enabled' }
    highAvailability: { mode: 'Disabled' }
    network: { publicNetworkAccess: 'Enabled' }
  }
}

resource db 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: pg
  name: dbName
  properties: { charset: 'UTF8', collation: 'en_US.utf8' }
}

resource fwAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = {
  parent: pg
  name: 'allow-azure-services'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}

// Required pgcrypto extension for hash chain
resource ext 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = {
  parent: pg
  name: 'azure.extensions'
  properties: { value: 'PGCRYPTO,UUID-OSSP', source: 'user-override' }
}

resource kv 'Microsoft.KeyVault/vaults@2024-11-01' existing = { name: keyVaultName }
resource secret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: kv
  name: 'evidence-pg-admin-password'
  properties: { value: adminPassword }
}
resource secretConn 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: kv
  name: 'evidence-pg-connection'
  properties: { value: 'host=${pg.properties.fullyQualifiedDomainName} port=5432 user=avsadmin password=${adminPassword} dbname=${dbName} sslmode=require' }
}

output fqdn string = pg.properties.fullyQualifiedDomainName
output databaseName string = dbName
