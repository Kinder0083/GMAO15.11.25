# Corrections de Permissions Restantes

## Endpoints à corriger (35 restants)

### Work Orders (comments, parts)
- `POST /work-orders/{work_order_id}/comments` → `require_permission("workOrders", "edit")`
- `GET /work-orders/{work_order_id}/comments` → `require_permission("workOrders", "view")`
- `POST /work-orders/{work_order_id}/parts-used` → `require_permission("workOrders", "edit")`

### Meters (lecture)
- `PUT /meters/{meter_id}` → `require_permission("meters", "edit")`
- `POST /meters/{meter_id}/readings` → `require_permission("meters", "edit")`
- `GET /meters/{meter_id}/readings` → `require_permission("meters", "view")`
- `GET /meters/{meter_id}/statistics` → `require_permission("meters", "view")`
- `DELETE /readings/{reading_id}` → `require_permission("meters", "delete")`

### Intervention Requests
- `PUT /intervention-requests/{request_id}` → `require_permission("interventionRequests", "edit")`
- `POST /intervention-requests/{request_id}/convert-to-work-order` → `require_permission("interventionRequests", "edit")`

### Improvement Requests
- `POST /improvement-requests` → `require_permission("improvementRequests", "edit")`
- `PUT /improvement-requests/{request_id}` → `require_permission("improvementRequests", "edit")`
- `POST /improvement-requests/{request_id}/convert-to-improvement` → `require_permission("improvementRequests", "edit")`
- `POST /improvement-requests/{request_id}/attachments` → `require_permission("improvementRequests", "edit")`
- `GET /improvement-requests/{request_id}/attachments/{filename}` → `require_permission("improvementRequests", "view")`

### Purchase History
- `GET /purchase-history/stats` → `require_permission("purchaseHistory", "view")`
- `GET /purchase-history/template` → `require_permission("purchaseHistory", "view")`

### Admin Only
- `POST /users/{user_id}/set-password-permanent` → `get_current_admin_user`

### Auth Légitime (à garder tel quel)
- `POST /support/request-help` → Peut rester avec `get_current_user`
- Tous les endpoints `/auth/*` → Garder `get_current_user`
- Tous les endpoints `/user-preferences` → Garder `get_current_user`

## Status
- ✅ Corrigés : 23 endpoints critiques
- 🔄 Restants : ~35 endpoints
- ⏳ Estimation : 2-3 heures pour tout corriger
