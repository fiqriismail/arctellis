# Azure Infrastructure Guide — SharePoint List AI Assistant

This guide walks through every Azure resource the application needs, in the order they should be created. Each section maps back to the architecture and tells you which `.env` key to fill in from each step.

**Tools required**
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) (`az`) — install and run `az login` before starting
- An Azure subscription with Owner or Contributor + User Access Administrator roles
- A Microsoft 365 / SharePoint Online tenant

**Reference files**
- `.env` template: `apps/backend/.env.example`
- Architecture: `docs/Architecture-SharePoint-List-AI-Assistant.md`

---

## 1. Resource Group

All resources for this app live in a single resource group. Create it once.

```bash
az group create \
  --name rg-group-one-rtp \
  --location australiaeast
```

> Change `australiaeast` to your preferred region. Use the same region for all resources below to minimise latency and egress costs.

---

## 2. Entra ID App Registration

The backend uses a **client-credentials** identity to read SharePoint on the app's own behalf. This is separate from end-user sign-in (covered in §7).

### 2.1 Create the app registration

```bash
az ad app create \
  --display-name "group-one-rtp-backend" \
  --sign-in-audience AzureADMyOrg
```

Copy the `appId` from the output — this is your `AZURE_CLIENT_ID`.

```bash
# Save the app ID to a shell variable for use in later steps
APP_ID=<appId from above>
```

### 2.2 Create a service principal

```bash
az ad sp create --id $APP_ID
```

### 2.3 Get your Tenant ID

```bash
az account show --query tenantId -o tsv
```

Copy this value — this is your `AZURE_TENANT_ID`.

### 2.4 Create a client secret

```bash
az ad app credential reset \
  --id $APP_ID \
  --years 1
```

Copy the `password` from the output — this is your `AZURE_CLIENT_SECRET`. This is the **only time** it is shown.

> **.env mapping**
> ```
> AZURE_TENANT_ID=<tenant ID from 2.3>
> AZURE_CLIENT_ID=<appId from 2.1>
> AZURE_CLIENT_SECRET=<password from 2.4>
> ```

---

## 3. Microsoft Graph Permissions

The app needs read access to SharePoint via Microsoft Graph. Prefer `Sites.Selected` (scoped to one site) over `Sites.Read.All` (entire tenant).

### Option A — Sites.Selected (recommended)

#### 3A.1 Grant the application permission

```bash
# Get the Graph API service principal object ID
GRAPH_SP_ID=$(az ad sp show --id 00000003-0000-0000-c000-000000000000 --query id -o tsv)

# Get the Sites.Selected app role ID
SITES_SELECTED_ID=$(az ad sp show \
  --id 00000003-0000-0000-c000-000000000000 \
  --query "appRoles[?value=='Sites.Selected'].id" -o tsv)

# Add the permission to the app registration
az ad app permission add \
  --id $APP_ID \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions $SITES_SELECTED_ID=Role
```

#### 3A.2 Grant admin consent

```bash
az ad app permission admin-consent --id $APP_ID
```

#### 3A.3 Grant the app access to the specific SharePoint site

`Sites.Selected` permission alone is not enough — you must also explicitly grant the app access to the target site. This requires a Graph API call using a token with `Sites.FullControl.All` (i.e., a Global Admin token).

```bash
# Get an admin access token
ADMIN_TOKEN=$(az account get-access-token \
  --resource https://graph.microsoft.com \
  --query accessToken -o tsv)

# Get the site ID (replace with your SharePoint site URL)
SITE_HOST=<tenant>.sharepoint.com
SITE_PATH=/sites/<site-name>

SITE_ID=$(curl -s \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://graph.microsoft.com/v1.0/sites/$SITE_HOST:$SITE_PATH" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Site ID: $SITE_ID"

# Grant the app read access to that site
curl -s -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"roles\":[\"read\"],\"grantedToIdentities\":[{\"application\":{\"id\":\"$APP_ID\",\"displayName\":\"group-one-rtp-backend\"}}]}" \
  "https://graph.microsoft.com/v1.0/sites/$SITE_ID/permissions"
```

Expected response: a permission object with `"roles": ["read"]`.

---

### Option B — Sites.Read.All (simpler for initial dev)

Use this during development if the target site is not yet finalised.

```bash
SITES_READ_ALL_ID=$(az ad sp show \
  --id 00000003-0000-0000-c000-000000000000 \
  --query "appRoles[?value=='Sites.Read.All'].id" -o tsv)

az ad app permission add \
  --id $APP_ID \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions $SITES_READ_ALL_ID=Role

az ad app permission admin-consent --id $APP_ID
```

> Switch to `Sites.Selected` before going to production.

---

## 4. Azure OpenAI

### 4.1 Create the Azure OpenAI resource

```bash
az cognitiveservices account create \
  --name aoai-group-one-rtp \
  --resource-group rg-group-one-rtp \
  --kind OpenAI \
  --sku S0 \
  --location australiaeast
```

### 4.2 Deploy a chat model

```bash
az cognitiveservices account deployment create \
  --name aoai-group-one-rtp \
  --resource-group rg-group-one-rtp \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-11-20" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name GlobalStandard
```

> `--sku-capacity` is in thousands of tokens per minute. Adjust based on your quota.

### 4.3 Get the endpoint and key

```bash
# Endpoint
az cognitiveservices account show \
  --name aoai-group-one-rtp \
  --resource-group rg-group-one-rtp \
  --query properties.endpoint -o tsv

# API key
az cognitiveservices account keys list \
  --name aoai-group-one-rtp \
  --resource-group rg-group-one-rtp \
  --query key1 -o tsv
```

> **.env mapping**
> ```
> AZURE_OPENAI_ENDPOINT=<endpoint from above>
> AZURE_OPENAI_API_KEY=<key1 from above>
> AZURE_OPENAI_DEPLOYMENT=gpt-4o
> ```

---

## 5. Azure Key Vault

In production, secrets are read from Key Vault via the container's managed identity — never from environment variables or code.

### 5.1 Create the Key Vault

```bash
az keyvault create \
  --name kv-group-one-rtp \
  --resource-group rg-group-one-rtp \
  --location australiaeast \
  --sku standard \
  --enable-rbac-authorization true
```

### 5.2 Add secrets

```bash
az keyvault secret set --vault-name kv-group-one-rtp --name AZURE-TENANT-ID       --value "<your tenant id>"
az keyvault secret set --vault-name kv-group-one-rtp --name AZURE-CLIENT-ID       --value "<your client id>"
az keyvault secret set --vault-name kv-group-one-rtp --name AZURE-CLIENT-SECRET   --value "<your client secret>"
az keyvault secret set --vault-name kv-group-one-rtp --name AZURE-OPENAI-ENDPOINT --value "<your openai endpoint>"
az keyvault secret set --vault-name kv-group-one-rtp --name AZURE-OPENAI-API-KEY  --value "<your openai key>"
az keyvault secret set --vault-name kv-group-one-rtp --name SHAREPOINT-SITE-URL   --value "<your site url>"
az keyvault secret set --vault-name kv-group-one-rtp --name SHAREPOINT-LIST-ID    --value "<your list id>"
```

> The managed identity grant (step 6.4) allows the container to read these secrets at runtime — no secret is ever baked into the container image or passed as a plain environment variable in production.

---

## 6. Azure Container Apps (Backend)

### 6.1 Create a Container Apps environment

```bash
az containerapp env create \
  --name cae-group-one-rtp \
  --resource-group rg-group-one-rtp \
  --location australiaeast
```

### 6.2 Create a Container Registry (to host the backend image)

```bash
az acr create \
  --name acrGroupOneRtp \
  --resource-group rg-group-one-rtp \
  --sku Basic \
  --admin-enabled false
```

### 6.3 Create the Container App with a system-assigned managed identity

```bash
az containerapp create \
  --name ca-group-one-rtp-backend \
  --resource-group rg-group-one-rtp \
  --environment cae-group-one-rtp \
  --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --system-assigned
```

> The placeholder image is used for initial provisioning. It will be replaced when the real image is pushed in Phase 5.

### 6.4 Grant the managed identity access to Key Vault

```bash
# Get the managed identity principal ID
PRINCIPAL_ID=$(az containerapp show \
  --name ca-group-one-rtp-backend \
  --resource-group rg-group-one-rtp \
  --query identity.principalId -o tsv)

# Get the Key Vault resource ID
KV_ID=$(az keyvault show \
  --name kv-group-one-rtp \
  --resource-group rg-group-one-rtp \
  --query id -o tsv)

# Assign Key Vault Secrets User role
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Key Vault Secrets User" \
  --scope $KV_ID
```

### 6.5 Grant the managed identity pull access to the Container Registry

```bash
ACR_ID=$(az acr show \
  --name acrGroupOneRtp \
  --resource-group rg-group-one-rtp \
  --query id -o tsv)

az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role AcrPull \
  --scope $ACR_ID
```

---

## 7. Entra ID — End-User Sign-In (separate from app identity)

The backend validates end-user tokens on every request. This requires a **separate** app registration (or the same one with a redirect URI added) for the web frontend.

> This is distinct from §2 — §2 is the app's own identity for reading SharePoint; this section is for authenticating human users.

### 7.1 Add a redirect URI to the existing app registration

```bash
az ad app update \
  --id $APP_ID \
  --web-redirect-uris "http://localhost:3000/api/auth/callback" \
                      "https://<your-static-web-app>.azurestaticapps.net/api/auth/callback"
```

### 7.2 Enable ID tokens

```bash
az ad app update \
  --id $APP_ID \
  --enable-id-token-issuance true
```

### 7.3 Note the values for the frontend

> **.env.local mapping (frontend)**
> ```
> NEXT_PUBLIC_ENTRA_TENANT_ID=<AZURE_TENANT_ID>
> NEXT_PUBLIC_ENTRA_CLIENT_ID=<AZURE_CLIENT_ID>
> ```

---

## 8. Azure Static Web Apps (Frontend)

### 8.1 Create the Static Web App

```bash
az staticwebapp create \
  --name swa-group-one-rtp \
  --resource-group rg-group-one-rtp \
  --location eastasia \
  --sku Free
```

> Static Web Apps has a limited set of supported regions. `eastasia` and `eastus2` are the most broadly available. Check `az staticwebapp list-locations` for current options.

### 8.2 Get the deployment token (for CI)

```bash
az staticwebapp secrets list \
  --name swa-group-one-rtp \
  --resource-group rg-group-one-rtp \
  --query properties.apiKey -o tsv
```

Store this token in your CI/CD system (e.g. GitHub Actions secret `AZURE_STATIC_WEB_APPS_API_TOKEN`). It is used by the deployment action, not by the running app.

### 8.3 Set the backend API URL

In the Static Web App settings → Configuration → Add application setting:

| Name | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<containerapp-fqdn>` |

Get the container app FQDN:
```bash
az containerapp show \
  --name ca-group-one-rtp-backend \
  --resource-group rg-group-one-rtp \
  --query properties.configuration.ingress.fqdn -o tsv
```

---

## Summary — resource checklist

| Resource | Name | Created |
|---|---|---|
| Resource Group | `rg-group-one-rtp` | §1 |
| Entra App Registration | `group-one-rtp-backend` | §2 |
| Graph permissions (Sites.Selected) | — | §3 |
| Azure OpenAI | `aoai-group-one-rtp` | §4 |
| Azure Key Vault | `kv-group-one-rtp` | §5 |
| Container Apps Environment | `cae-group-one-rtp` | §6 |
| Container Registry | `acrGroupOneRtp` | §6 |
| Container App (backend) | `ca-group-one-rtp-backend` | §6 |
| Static Web App (frontend) | `swa-group-one-rtp` | §8 |

## Summary — .env mapping

| `.env` key | Source |
|---|---|
| `AZURE_TENANT_ID` | §2.3 |
| `AZURE_CLIENT_ID` | §2.1 |
| `AZURE_CLIENT_SECRET` | §2.4 |
| `AZURE_OPENAI_ENDPOINT` | §4.3 |
| `AZURE_OPENAI_API_KEY` | §4.3 |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o` (hardcoded default) |
| `SHAREPOINT_SITE_URL` | your SharePoint site URL |
| `SHAREPOINT_LIST_ID` | your list GUID (from Graph or site settings) |
| `CACHE_TTL_SECONDS` | default `60` |
| `LIST_ROW_THRESHOLD` | default `1000` |
