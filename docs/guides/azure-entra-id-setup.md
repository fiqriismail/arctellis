# Azure Entra ID App Registrations

This guide covers the creation of the Entra ID application registrations for both the backend service and the frontend client.

---

## Part 1: Backend App Registration

The backend uses a **client-credentials** identity to read SharePoint on the app's own behalf. This is distinct from end-user sign-in.

### 1.1 Create the registration

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

### 1.2 Create a client secret

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

### 1.3 Microsoft Graph Permissions

The app needs read access to SharePoint via Microsoft Graph.

1. Still on the app registration, select **API permissions** in the left menu.
2. Click **+ Add a permission** → **Microsoft Graph** → **Application permissions**.
3. Search for and tick one of:
   - **`Sites.Selected`** — recommended (scoped to one site only)
   - **`Sites.Read.All`** — simpler for initial dev if the target site is not yet finalised
4. Click **Add permissions**.
5. Back on the API permissions page, click **Grant admin consent for \<your org\>**.
6. Click **Yes** to confirm. The Status column should show a green tick ✓.

> **Sites.Selected (Graph API call)**
> If you chose `Sites.Selected`, you must also grant the app access to the specific SharePoint site using Graph Explorer:
> 1. Look up your site ID: `GET https://graph.microsoft.com/v1.0/sites/<tenant>.sharepoint.com:/sites/<site-name>`
> 2. Grant access: `POST https://graph.microsoft.com/v1.0/sites/<site-id>/permissions` with body:
>    ```json
>    {
>      "roles": ["read"],
>      "grantedToIdentities": [{ "application": { "id": "<AZURE_CLIENT_ID>" } }]
>    }
>    ```

### 1.3.1 Additional permission for M365 Group Membership Check

If you plan to restrict the assistant to a specific Microsoft 365 Group, add the following **Application** permission (not Delegated):

1. Still on the API permissions page, click **+ Add a permission** → **Microsoft Graph** → **Application permissions**.
2. Search for and tick:
   - **`GroupMember.Read.All`** — allows the backend to verify group membership via Microsoft Graph
3. Click **Add permissions**.
4. Back on the API permissions page, click **Grant admin consent for \<your org\>**.
5. Click **Yes** to confirm. The Status column should show a green tick ✓.

| Permission | Type | Purpose |
|---|---|---|
| `GroupMember.Read.All` | Application | Allows the backend to call `POST /v1.0/users/{oid}/checkMemberObjects` to verify group membership |

Also add to your backend `.env` (or Key Vault secret in production):
```
ALLOWED_GROUP_ID=<entra-object-id-of-m365-group>
```

Replace `<entra-object-id-of-m365-group>` with the Object ID of the M365 Group. Find this in Microsoft Entra ID → Groups → select your group → Object ID.

### 1.4 Expose the backend API

First, configure the backend app registration to accept tokens from the client:

1. Go to **Microsoft Entra ID** → **App registrations** → select `group-one-rtp-backend`.
2. In the left menu, select **Expose an API**.
3. Next to **Application ID URI**, click **Add** and save the default value (usually `api://<backend-client-id>`).
4. Under **Scopes defined by this API**, click **+ Add a scope**:
   - **Scope name** — `access_as_user`
   - **Who can consent?** — **Admins and users**
   - **Admin consent display name** — `Access backend as user`
   - **Admin consent description** — `Allows the frontend client to access the backend API on behalf of the user.`
   - Ensure **State** is **Enabled** and click **Add scope**.

---

## Part 2: Frontend App Registration (Client)

End users sign in with Entra ID via the Next.js frontend before they can use the chat. For security and proper separation of concerns, the frontend uses its own client app registration, which requests permission to access the backend API.

### 2.1 Create the client registration

1. Go back to **App registrations** → **+ New registration**.
2. Fill in:
   - **Name** — `group-one-rtp-client`
   - **Supported account types** — *Accounts in this organizational directory only (Single tenant)*
   - **Redirect URI** — select **Web** and add `http://localhost:3000/api/auth/callback` (you will add the production URL later)
3. Click **Register**.

Copy these values from the Overview page:

| Value | Where | `.env.local` key |
|---|---|---|
| **Application (client) ID** | Overview page | `NEXT_PUBLIC_ENTRA_CLIENT_ID` |
| **Directory (tenant) ID** | Overview page | `NEXT_PUBLIC_ENTRA_TENANT_ID` |

### 2.2 Grant the client access to the backend

1. Still in the `group-one-rtp-client` registration, select **API permissions** in the left menu.
2. Click **+ Add a permission** → **My APIs** tab.
3. Select `group-one-rtp-backend`.
4. Select **Delegated permissions**, tick the `access_as_user` scope you created earlier, and click **Add permissions**.
5. Click **Grant admin consent for \<your org\>** and confirm.

### 2.3 Client Secret (If required)

If your frontend uses a library (like MSAL Node or NextAuth.js) that requires a client secret for the authorization code flow:
1. Select **Certificates & secrets** → **+ New client secret**.
2. Add a description (`frontend-secret`), click **Add**, and copy the value immediately. Use this for `ENTRA_CLIENT_SECRET` in your frontend `.env.local`.

### 2.4 Frontend .env values

> **.env.local mapping (frontend)**
> ```
> NEXT_PUBLIC_ENTRA_TENANT_ID=<Directory (tenant) ID from step 2.1>
> NEXT_PUBLIC_ENTRA_CLIENT_ID=<Application (client) ID from step 2.1>
> ENTRA_CLIENT_SECRET=<secret value from step 2.3 if applicable>
> NEXT_PUBLIC_BACKEND_SCOPE=api://<backend-client-id>/access_as_user
> ```
