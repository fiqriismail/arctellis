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

## 2. Entra ID App Registration

The backend uses a **client-credentials** identity to read SharePoint on the app's own behalf. This is distinct from end-user sign-in (covered in §7).

### 2.1 Create the registration

1. Search for **Microsoft Entra ID** and select it.
2. In the left menu select **App registrations** → **+ New registration**.
3. Fill in:
   - **Name** — `group-one-rtp-backend`
   - **Supported account types** — *Accounts in this organizational directory only (Single tenant)*
   - **Redirect URI** — leave blank for now
4. Click **Register**.

You are taken to the app's Overview page. Copy two values:

| Value | Where | `.env` key |
|---|---|---|
| **Application (client) ID** | Overview page | `AZURE_CLIENT_ID` |
| **Directory (tenant) ID** | Overview page | `AZURE_TENANT_ID` |

### 2.2 Create a client secret

1. In the left menu select **Certificates & secrets**.
2. Click **+ New client secret**.
3. Fill in:
   - **Description** — `backend-secret`
   - **Expires** — 12 months (or your org policy)
4. Click **Add**.
5. **Copy the Value immediately** — it is only shown once.

| Value | `.env` key |
|---|---|
| Secret **Value** | `AZURE_CLIENT_SECRET` |

> **.env mapping after §2**
> ```
> AZURE_TENANT_ID=<Directory (tenant) ID>
> AZURE_CLIENT_ID=<Application (client) ID>
> AZURE_CLIENT_SECRET=<secret value>
> ```

---

## 3. Microsoft Graph Permissions

The app needs read access to SharePoint via Microsoft Graph.

### 3.1 Add the permission

1. Still on the app registration, select **API permissions** in the left menu.
2. Click **+ Add a permission** → **Microsoft Graph** → **Application permissions**.
3. Search for and tick one of:
   - **`Sites.Selected`** — recommended (scoped to one site only)
   - **`Sites.Read.All`** — simpler for initial dev if the target site is not yet finalised
4. Click **Add permissions**.

### 3.2 Grant admin consent

1. Back on the API permissions page, click **Grant admin consent for \<your org\>**.
2. Click **Yes** to confirm.
3. The Status column should show a green tick ✓ next to the permission.

> If you chose `Sites.Selected` in step 3.1, the permission alone is not enough — you also need to grant the app access to the specific SharePoint site. This cannot be done in the Portal and requires a Graph API call. See the note at the end of §3.

### 3.3 Sites.Selected — grant access to the specific site (Graph API call)

Skip this if you used `Sites.Read.All`.

You need to make a POST request to Graph. The easiest way is to use [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer):

1. Go to **Graph Explorer** and sign in with a **Global Admin** account.
2. First, look up your site ID:
   - Method: **GET**
   - URL: `https://graph.microsoft.com/v1.0/sites/<tenant>.sharepoint.com:/sites/<site-name>`
   - Click **Run query**. Copy the `id` field from the response — this is your **site ID**.
3. Grant the app read access to that site:
   - Method: **POST**
   - URL: `https://graph.microsoft.com/v1.0/sites/<site-id>/permissions`
   - Request body:
     ```json
     {
       "roles": ["read"],
       "grantedToIdentities": [
         {
           "application": {
             "id": "<AZURE_CLIENT_ID>",
             "displayName": "group-one-rtp-backend"
           }
         }
       ]
     }
     ```
   - Click **Run query**. The response should contain `"roles": ["read"]`.

> Switch from `Sites.Read.All` to `Sites.Selected` before going to production.

---

## 4. OpenAI API Key

The app uses the OpenAI API directly (not Azure OpenAI). No Azure resource is needed for this.

### 4.1 Get your API key

1. Go to [platform.openai.com](https://platform.openai.com) and sign in.
2. Click your profile → **API keys** → **+ Create new secret key**.
3. Give it a name (e.g. `group-one-rtp`), click **Create secret key**.
4. **Copy the key immediately** — it is only shown once.

### 4.2 Choose a model

The default model is `gpt-4o`. Ensure your account has access to it under **Settings → Limits**. Any model with tool/function calling support works.

> **.env mapping after §4**
> ```
> OPENAI_API_KEY=sk-...
> OPENAI_MODEL=gpt-4o
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
| `OPENAI-API-KEY` | your OpenAI API key (from §4.1) |
| `SHAREPOINT-SITE-URL` | your SharePoint site URL |
| `SHAREPOINT-LIST-ID` | your list GUID (see tip below) |

> **Finding your List ID:** Go to the SharePoint site → open the list → **Settings** (gear icon) → **List settings**. The URL contains `List=%7B<guid>%7D` — URL-decode the braces (`%7B` = `{`, `%7D` = `}`) to get the GUID.

---

## 6. Azure Container Registry

The backend container image is stored here before being deployed to Container Apps.

1. Search for **Container registries** and select it.
2. Click **+ Create**.
3. Fill in:
   - **Subscription** — select yours
   - **Resource group** — `rg-group-one-rtp`
   - **Registry name** — `acrGroupOneRtp` (must be globally unique, lowercase/numbers only)
   - **Location** — same as resource group
   - **Pricing plan** — Basic
4. Click **Review + create** → **Create**.

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
   - **Image** — leave as placeholder for now; a real image is pushed in Phase 5
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

---

## 8. Entra ID — End-User Sign-In

End users sign in with Entra ID before they can use the chat. This uses the **same app registration** from §2 but needs a redirect URI added.

### 8.1 Add redirect URIs

1. Go to **Microsoft Entra ID** → **App registrations** → select `group-one-rtp-backend`.
2. In the left menu select **Authentication** → **+ Add a platform** → **Web**.
3. Add the following redirect URIs:
   - `http://localhost:3000/api/auth/callback` (local dev)
   - `https://<your-static-web-app>.azurestaticapps.net/api/auth/callback` (production — fill in after §9)
4. Under **Implicit grant and hybrid flows** tick **ID tokens**.
5. Click **Save**.

### 8.2 Frontend .env values

> **.env.local mapping (frontend)**
> ```
> NEXT_PUBLIC_ENTRA_TENANT_ID=<AZURE_TENANT_ID from §2.1>
> NEXT_PUBLIC_ENTRA_CLIENT_ID=<AZURE_CLIENT_ID from §2.1>
> ```

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
| OpenAI API key | — (platform.openai.com) | §4 |
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
| `OPENAI_API_KEY` | §4.1 — platform.openai.com API key |
| `OPENAI_MODEL` | `gpt-4o` (default) |
| `SHAREPOINT_SITE_URL` | your SharePoint site URL |
| `SHAREPOINT_LIST_ID` | §5.3 tip — list GUID from list settings URL |
| `CACHE_TTL_SECONDS` | default `60` |
| `LIST_ROW_THRESHOLD` | default `1000` |
