# Azure Infrastructure Guide — SharePoint List AI Assistant

Step-by-step guide to provisioning every Azure resource via the **Azure Portal** (portal.azure.com). Follow the sections in order — each one tells you which `.env` value to copy at the end.

**Before you start**
- Sign in to [portal.azure.com](https://portal.azure.com) with an account that has **Owner** or **Contributor + User Access Administrator** on the subscription.
- Have a Microsoft 365 / SharePoint Online tenant in the same Entra ID directory.

**Reference files**
- `.env` template: `apps/backend/.env.example`
- Architecture: `docs/Architecture-SharePoint-List-AI-Assistant.md`

---

## 1. Resource Group

All resources live in one resource group.

1. In the portal search bar type **Resource groups** and select it.
2. Click **+ Create**.
3. Fill in:
   - **Subscription** — select yours
   - **Resource group name** — `rg-group-one-rtp`
   - **Region** — choose the region closest to your users (e.g. Australia East)
4. Click **Review + create** → **Create**.

> Use the same region for all resources below unless a service isn't available there.

---

## 2 & 3. Entra ID App Registrations & Graph Permissions

The Entra ID setup (for both the backend service and the frontend client) has been extracted to a separate guide.

👉 **Please complete the setup in [Azure Entra ID App Registrations](./azure-entra-id-setup.md) before continuing.**

Once you have completed that guide and copied the required `.env` values, return here to continue with Section 4.

---

## 4. Azure OpenAI

The agent's LLM runs on **Azure OpenAI** inside your tenant (not public OpenAI). In production the backend authenticates with the Container App's **managed identity** (no key); a key is only used for local development.

### 4.1 Create the Azure OpenAI resource

1. Search for **Azure OpenAI** and select it.
2. Click **+ Create**.
3. Fill in:
   - **Subscription** — select yours
   - **Resource group** — `rg-group-one-rtp`
   - **Region** — a region that offers your chosen model (e.g. Sweden Central, East US)
   - **Name** — `aoai-group-one-rtp`
   - **Pricing tier** — Standard S0
4. Click **Review + create** → **Create**.

### 4.2 Deploy a model

1. Open the resource and click **Go to Azure AI Foundry portal** (or **Model deployments**).
2. Select **Deployments** → **+ Deploy model** → **Deploy base model**.
3. Choose a chat model with tool/function-calling support (e.g. **gpt-4o**).
4. Set a **Deployment name** (e.g. `gpt-4o`) and deploy. **Note this name** — it is `AZURE_OPENAI_DEPLOYMENT` and may differ from the underlying model id.

### 4.3 Copy the endpoint and key

1. On the resource, select **Keys and Endpoint**.
2. Copy the **Endpoint** and **KEY 1**.

> The endpoint is the **base host only** — e.g. `https://aoai-group-one-rtp.openai.azure.com` (classic) or `https://<resource>.cognitiveservices.azure.com` (Azure AI Foundry). Drop any `/openai/...` path or `?api-version=...` query the portal/playground may show.

### 4.4 Pin an API version

Use a known-good GA version rather than tracking latest: `2024-10-21`.

> **.env mapping after §4**
> ```
> AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
> AZURE_OPENAI_DEPLOYMENT=<deployment name from §4.2>
> AZURE_OPENAI_API_VERSION=2024-10-21
> AZURE_OPENAI_API_KEY=<KEY 1>   # local dev only — leave empty in Azure (managed identity)
> ```

---

## 5. Azure Key Vault

In production, all secrets come from Key Vault via the container's managed identity — never from environment variables or code.

### 5.1 Create the vault

1. Search for **Key vaults** and select it.
2. Click **+ Create**.
3. Fill in:
   - **Subscription** — select yours
   - **Resource group** — `rg-group-one-rtp`
   - **Key vault name** — `kv-group-one-rtp`
   - **Region** — same as resource group
   - **Pricing tier** — Standard
4. On the **Access configuration** tab:
   - **Permission model** — select **Azure role-based access control**
5. Click **Review + create** → **Create**.

### 5.2 Add yourself as Key Vault Administrator

1. Go to the Key Vault resource.
2. In the left menu select **Access control (IAM)** → **+ Add** → **Add role assignment**.
3. Select role **Key Vault Administrator** → **Next**.
4. Click **+ Select members**, search for your own account, select it → **Review + assign**.

### 5.3 Add all secrets

1. In the left menu select **Secrets** → **+ Generate/Import** for each secret below.
2. Set **Upload options** to **Manual**, enter the **Name** and **Value**, click **Create**.

| Secret name | Value |
|---|---|
| `AZURE-TENANT-ID` | your tenant ID (from §2.1) |
| `AZURE-CLIENT-ID` | your client ID (from §2.1) |
| `AZURE-CLIENT-SECRET` | your client secret (from §2.2) |
| `AZURE-OPENAI-ENDPOINT` | your Azure OpenAI endpoint (from §4.3) |
| `AZURE-OPENAI-DEPLOYMENT` | your model deployment name (from §4.2) |
| `SHAREPOINT-SITE-URL` | your SharePoint site URL |
| `SHAREPOINT-LIST-ID` | your list GUID (see tip below) |

> **No Azure OpenAI key in production.** The backend reaches Azure OpenAI with the Container App's managed identity (see §7.6), so `AZURE-OPENAI-API-KEY` is **not** stored here. Only set `AZURE_OPENAI_API_KEY` locally for development.

> **Finding your List ID:** Go to the SharePoint site → open the list → **Settings** (gear icon) → **List settings**. The URL contains `List=%7B<guid>%7D` — URL-decode the braces (`%7B` = `{`, `%7D` = `}`) to get the GUID.

---

## 6. Azure Container Registry

The backend container image is stored here before being deployed to Container Apps.

### 6.1 Create the registry

1. Search for **Container registries** and select it.
2. Click **+ Create**.
3. Fill in:
   - **Subscription** — select yours
   - **Resource group** — `rg-group-one-rtp`
   - **Registry name** — `acrGroupOneRtp` (must be globally unique, lowercase/numbers only)
   - **Location** — same as resource group
   - **Pricing plan** — Basic
4. Click **Review + create** → **Create**.

### 6.2 Push the backend image

You need to build the Docker image for Linux (since Azure Container Apps runs Linux containers) and push it to your registry.

1. Set the environment variables in your terminal for the registry name and image tag (use lowercase for the registry name):
   ```bash
   export ACR="acrgrouponertp"
   export IMAGE_TAG="backend:latest"
   ```
2. Log in to the registry via the Azure CLI:
   ```bash
   az acr login --name $ACR
   ```
3. Build the Docker image. **Important:** If you are on an Apple Silicon Mac (M1/M2/M3), you must build it for the `linux/amd64` platform. Run this from the root of the repository:
   ```bash
   docker build --platform linux/amd64 -t $ACR.azurecr.io/$IMAGE_TAG -f apps/backend/Dockerfile .
   ```
4. Push the image to the registry:
   ```bash
   docker push $ACR.azurecr.io/$IMAGE_TAG
   ```

---

## 7. Azure Container Apps (Backend)

### 7.1 Create a Container Apps environment

1. Search for **Container Apps Environments** and select it.
2. Click **+ Create**.
3. Fill in:
   - **Subscription** — select yours
   - **Resource group** — `rg-group-one-rtp`
   - **Name** — `cae-group-one-rtp`
   - **Region** — same as resource group
4. Click **Review + create** → **Create**.

### 7.2 Create the Container App

1. Search for **Container Apps** and select it.
2. Click **+ Create**.
3. **Basics** tab:
   - **Subscription** — select yours
   - **Resource group** — `rg-group-one-rtp`
   - **Container app name** — `ca-group-one-rtp-backend`
   - **Region** — same as resource group
   - **Container Apps Environment** — select `cae-group-one-rtp`
4. **Container** tab:
   - Uncheck **Use quickstart image**
   - **Image source** — Azure Container Registry
   - **Registry** — `acrGroupOneRtp`
   - **Image** — select `backend` and tag `latest` (pushed in §6.2)
   - **CPU and memory** — 0.5 CPU / 1 Gi (sufficient for dev)
5. **Ingress** tab:
   - Enable ingress: **On**
   - Ingress traffic: **Accepting traffic from anywhere**
   - Target port: `8000`
6. Click **Review + create** → **Create**.

### 7.3 Enable system-assigned managed identity

1. Go to the Container App resource.
2. In the left menu select **Identity**.
3. On the **System assigned** tab, toggle **Status** to **On** → **Save** → **Yes**.
4. Copy the **Object (principal) ID** that appears — you need it in §7.4.

### 7.4 Grant the identity access to Key Vault

1. Go to the **Key Vault** (`kv-group-one-rtp`).
2. In the left menu select **Access control (IAM)** → **+ Add** → **Add role assignment**.
3. Select role **Key Vault Secrets User** → **Next**.
4. **Assign access to** — select **Managed identity**.
5. Click **+ Select members** → **Managed identity** dropdown → **Container App** → select `ca-group-one-rtp-backend` → **Select** → **Review + assign**.

### 7.5 Grant the identity pull access to the Container Registry

1. Go to the **Container Registry** (`acrGroupOneRtp`).
2. In the left menu select **Access control (IAM)** → **+ Add** → **Add role assignment**.
3. Select role **AcrPull** → **Next**.
4. **Assign access to** — **Managed identity** → select `ca-group-one-rtp-backend` → **Review + assign**.

### 7.6 Grant the identity access to Azure OpenAI

The backend calls Azure OpenAI with its managed identity, so the identity needs a data-plane role on the Azure OpenAI resource.

1. Go to the **Azure OpenAI** resource (`aoai-group-one-rtp`).
2. In the left menu select **Access control (IAM)** → **+ Add** → **Add role assignment**.
3. Select role **Cognitive Services OpenAI User** → **Next**.
4. **Assign access to** — **Managed identity** → select `ca-group-one-rtp-backend` → **Review + assign**.

> This is what lets the app omit `AZURE_OPENAI_API_KEY` in production — it requests an Entra token for `https://cognitiveservices.azure.com/.default` instead.

### 7.7 Configure Environment Variables

Link the Key Vault secrets to the Container App's environment variables.

1. First, import the secrets:
   - Go to the **Container App** (`ca-group-one-rtp-backend`).
   - In the left menu select **Secrets**.
   - Click **+ Add** and select **Key Vault reference**.
   - Fill in the details to point to your `kv-group-one-rtp` Key Vault and select the corresponding secret (e.g., `AZURE-TENANT-ID`). Repeat this for all secrets listed in §5.3.
2. Next, map them to environment variables:
   - In the left menu, select **Containers**.
   - Click **Edit and deploy** → select the container image → click **Edit**.
   - Under the **Environment variables** section, add the required `.env` keys (e.g., `AZURE_TENANT_ID`).
   - For the **Source**, select **Secret reference** and map it to the secret you imported in step 1.
   - Click **Save**, then **Create** to deploy the new revision.

---

## 8. Entra ID — End-User Sign-In

The frontend client application registration and redirect URIs are now covered in the [Azure Entra ID App Registrations](./azure-entra-id-setup.md) guide.

---

## 9. Azure Static Web Apps (Frontend)

### 9.1 Create the Static Web App

1. Search for **Static Web Apps** and select it.
2. Click **+ Create**.
3. Fill in:
   - **Subscription** — select yours
   - **Resource group** — `rg-group-one-rtp`
   - **Name** — `swa-group-one-rtp`
   - **Plan type** — Free
   - **Region** — choose the closest available (options are limited; East Asia and East US 2 are broadly available)
   - **Deployment source** — **GitHub** (connect your repo and branch) or **Other** for manual deploy
4. Click **Review + create** → **Create**.

### 9.2 Copy the deployment token (for CI)

1. Go to the Static Web App resource.
2. In the left menu select **Manage deployment token**.
3. Copy the token and save it as a GitHub Actions secret named `AZURE_STATIC_WEB_APPS_API_TOKEN`.

### 9.3 Set the backend API URL

1. In the left menu select **Configuration** → **+ Add**.
2. Add the application setting:
   - **Name** — `NEXT_PUBLIC_API_URL`
   - **Value** — the Container App FQDN from §7.2 (find it on the Container App overview page under **Application URL**)
3. Click **OK** → **Save**.

### 9.4 Update the Entra redirect URI

1. Go back to the app registration (§8.1) and update the production redirect URI with the actual Static Web App URL now that you have it.

---

## Summary — resource checklist

| Resource | Name | Section |
|---|---|---|
| Resource Group | `rg-group-one-rtp` | §1 |
| Entra App Registration | `group-one-rtp-backend` | §2 |
| Graph permission | `Sites.Selected` or `Sites.Read.All` | §3 |
| Azure OpenAI | `aoai-group-one-rtp` | §4 |
| Azure Key Vault | `kv-group-one-rtp` | §5 |
| Container Registry | `acrGroupOneRtp` | §6 |
| Container Apps Environment | `cae-group-one-rtp` | §7 |
| Container App (backend) | `ca-group-one-rtp-backend` | §7 |
| Static Web App (frontend) | `swa-group-one-rtp` | §9 |

## Summary — .env mapping

| `.env` key | Source |
|---|---|
| `AZURE_TENANT_ID` | §2.1 — Directory (tenant) ID |
| `AZURE_CLIENT_ID` | §2.1 — Application (client) ID |
| `AZURE_CLIENT_SECRET` | §2.2 — secret Value |
| `AZURE_OPENAI_ENDPOINT` | §4.3 — resource Endpoint (base host) |
| `AZURE_OPENAI_DEPLOYMENT` | §4.2 — model deployment name |
| `AZURE_OPENAI_API_VERSION` | `2024-10-21` (default) |
| `AZURE_OPENAI_API_KEY` | §4.3 — KEY 1 (local dev only; omit in Azure) |
| `SHAREPOINT_SITE_URL` | your SharePoint site URL |
| `SHAREPOINT_LIST_ID` | §5.3 tip — list GUID from list settings URL |
| `CACHE_TTL_SECONDS` | default `60` |
| `LIST_ROW_THRESHOLD` | default `1000` |
