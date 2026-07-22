targetScope = 'resourceGroup'

@description('Azure region for the synthetic portfolio demo resources.')
param location string = resourceGroup().location

@description('Short name prefix for non-productive portfolio resources.')
param namePrefix string

@description('Container image for the synthetic FastAPI demo.')
param containerImage string

@description('Container port exposed by the FastAPI demo image.')
param containerPort int = 8000

@description('Minimum replicas. Keep 0 as the cost off switch.')
@minValue(0)
param minReplicas int = 0

@description('Maximum replicas for portfolio testing.')
@minValue(1)
param maxReplicas int = 1

@description('Azure Key Vault name placeholder. Must be globally unique.')
param keyVaultName string

@description('Tags applied to all Azure resources.')
param tags object = {
  project: 'steuerberater-copilot'
  purpose: 'synthetic-portfolio-demo'
  data: 'synthetic-only'
}

var normalizedName = toLower(namePrefix)
var workspaceName = '${normalizedName}-logs'
var environmentName = '${normalizedName}-env'
var appName = '${normalizedName}-api'

resource logWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logWorkspace.properties.customerId
        sharedKey: logWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: containerPort
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'api'
          image: containerImage
          env: [
            {
              name: 'STEUERBERATER_COPILOT_MODE'
              value: 'synthetic-demo'
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

output containerAppName string = containerApp.name
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output keyVaultResourceId string = keyVault.id
