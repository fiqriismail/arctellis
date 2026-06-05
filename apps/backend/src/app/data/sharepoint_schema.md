# SharePoint List Schema

_Generated 2026-06-05 16:50 UTC_

Use **Internal Name** when building OData filters or reading `fields` in tool results.
Always prefix with `fields/` in OData expressions (e.g. `fields/InternalName eq 'value'`).

| Display Name | Internal Name | Type | Notes |
|---|---|---|---|
| App Created By | `AppAuthor` | lookup | Lookup — fields dict contains {LookupValue} — ⚠ not in sample item |
| App Modified By | `AppEditor` | lookup | Lookup — fields dict contains {LookupValue} — ⚠ not in sample item |
| Attachments | `Attachments` | text | Plain text |
| Brand | `Brand` | text | Plain text — ⚠ not in sample item |
| Brief Description | `Description` | text | Plain text — ⚠ not in sample item |
| Budget Comments | `BudgetComments` | text | Plain text — ⚠ not in sample item |
| Budget Decision | `BudgetDecision` | choice | Choice — one of the configured options — ⚠ not in sample item |
| Budget Decision Date | `BudgetDecisionDate` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| Budget Owner | `BudgetOwner` | person | Person/group — fields dict contains {LookupValue, Email} — ⚠ not in sample item |
| Color Tag | `_ColorTag` | text | Plain text — ⚠ not in sample item |
| Compliance Asset Id | `ComplianceAssetId` | text | Plain text — ⚠ not in sample item |
| Content Type | `ContentType` | text | Plain text |
| Cost Center | `CostCenter` | choice | Choice — one of the configured options |
| Created | `Created` | dateTime | ISO-8601 datetime string |
| Created By | `Author` | person | Person/group — fields dict contains {LookupValue, Email} |
| Division | `Division` | text | Plain text |
| Edit | `Edit` | text | Plain text |
| ExceptionComments | `ExceptionComments` | text | Plain text — ⚠ not in sample item |
| ExceptionDecision | `ExceptionDecision` | choice | Choice — one of the configured options — ⚠ not in sample item |
| ExceptionDecisionBy | `ExceptionDecisionBy` | person | Person/group — fields dict contains {LookupValue, Email} — ⚠ not in sample item |
| ExceptionDecisionDate | `ExceptionDecisionDate` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| Folder Child Count | `FolderChildCount` | lookup | Lookup — fields dict contains {LookupValue} |
| ID | `ID` | text | Plain text — ⚠ not in sample item |
| Infosec Review Required | `InfoSecReviewRequired` | boolean | true/false |
| InfosecComments | `InfosecComments` | text | Plain text — ⚠ not in sample item |
| InfosecDecision | `InfosecDecision` | choice | Choice — one of the configured options — ⚠ not in sample item |
| InfosecDecisionBy | `InfosecDecisionBy` | text | Plain text — ⚠ not in sample item |
| InfosecDecisionDate | `InfosecDecisionDate` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| Intercompany | `Intercompany` | lookup | Lookup — fields dict contains {LookupValue} — ⚠ not in sample item |
| Item Child Count | `ItemChildCount` | lookup | Lookup — fields dict contains {LookupValue} |
| Item is a Record | `_IsRecord` | text | Plain text — ⚠ not in sample item |
| Label applied by | `_ComplianceTagUserId` | lookup | Lookup — fields dict contains {LookupValue} |
| Label setting | `_ComplianceFlags` | lookup | Lookup — fields dict contains {LookupValue} |
| Legal Review Required | `LegalReviewRequired` | boolean | true/false |
| LegalComments | `LegalComments` | text | Plain text — ⚠ not in sample item |
| LegalDecision | `LegalDecision` | choice | Choice — one of the configured options — ⚠ not in sample item |
| LegalDecisionBy | `LegalDecisionBy` | text | Plain text — ⚠ not in sample item |
| LegalDecisionDate | `LegalDecisionDate` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| Main Category | `MainCategory` | choice | Choice — one of the configured options — ⚠ not in sample item |
| Modified | `Modified` | dateTime | ISO-8601 datetime string |
| Modified By | `Editor` | person | Person/group — fields dict contains {LookupValue, Email} |
| OriginalBudgetOwner | `OriginalBudgetOwner` | text | Plain text — ⚠ not in sample item |
| PO Comments | `POComments` | text | Plain text — ⚠ not in sample item |
| PO Issue Date | `POIssueDate` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| PO Number | `PONumber` | text | Plain text — ⚠ not in sample item |
| Requester | `Requester` | person | Person/group — fields dict contains {LookupValue, Email} — ⚠ not in sample item |
| RerouteBudgetOwnerRole | `RerouteBudgetOwnerRole` | text | Plain text — ⚠ not in sample item |
| ReroutedBy | `ReroutedBy` | text | Plain text — ⚠ not in sample item |
| ReroutedOn | `ReroutedOn` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| Retention label | `_ComplianceTag` | lookup | Lookup — fields dict contains {LookupValue} |
| Retention label Applied | `_ComplianceTagWrittenTime` | lookup | Lookup — fields dict contains {LookupValue} |
| RTP Closed By | `RTPClosedBy` | person | Person/group — fields dict contains {LookupValue, Email} — ⚠ not in sample item |
| RTP Closed Date | `RTPClosedDate` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| RTP ID | `RTPID` | text | Plain text |
| RTP Requested Date | `RTPRequestedDate` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| SME | `SMEEmail` | person | Person/group — fields dict contains {LookupValue, Email} |
| SME Comments | `SMEComments` | text | Plain text — ⚠ not in sample item |
| SME Decision | `SMEDecision` | choice | Choice — one of the configured options — ⚠ not in sample item |
| SME Decision By  | `SMEDecisionBy` | person | Person/group — fields dict contains {LookupValue, Email} — ⚠ not in sample item |
| SME Decision Date & Time | `SMEDecisionDateTime` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| SME Notified | `SMENotified` | boolean | true/false |
| Sourcing Comments | `SourcingComments` | text | Plain text — ⚠ not in sample item |
| Sourcing Completed | `SourcingCompleted` | boolean | true/false |
| Sourcing Completed By | `SourcingCompletedBy` | person | Person/group — fields dict contains {LookupValue, Email} — ⚠ not in sample item |
| Sourcing Completed Date | `SourcingCompletedDate` | dateTime | ISO-8601 datetime string — ⚠ not in sample item |
| ThresholdFlag | `ThresholdFlag` | boolean | true/false |
| Type | `DocIcon` | text | Plain text — ⚠ not in sample item |
| Version | `_UIVersionString` | text | Plain text |
| 🏢 Department | `Department` | choice | Choice — one of the configured options |
| 💶 Estimated Amount (€) | `EstimatedAmount` | text | Plain text |
| 📝 Title | `Title` | text | Plain text |
| 📝 Title | `LinkTitleNoMenu` | text | Plain text |
| 📝 Title | `LinkTitle` | text | Plain text |
| 🔖 Status | `Status` | choice | Choice — one of the configured options |
| 🗂️ Category | `_x0001f5c2__xfe0f_Category` | lookup | Lookup — fields dict contains {LookupValue} — ⚠ not in sample item |

## Person column structure

When a row is fetched, person/group columns are normalised to:
```json
{ "LookupValue": "Jane Smith", "Email": "jane@example.com" }
```
Filter by name → match `LookupValue`. Filter by email → match `Email`.

## OData filter examples

```
fields/Department eq 'CIO'
fields/Status eq 'Active'
```

Datetime values must be quoted ISO-8601 strings. Match a single day with a half-open range (not `eq`):
```
fields/Created ge '2026-05-26T00:00:00Z' and fields/Created lt '2026-05-27T00:00:00Z'
```
