# Audit de Sécurité - Permissions Utilisateurs

## 🚨 PROBLÈMES CRITIQUES IDENTIFIÉS

### Endpoints SANS vérification de permissions appropriées

Ces endpoints utilisent `Depends(get_current_user)` au lieu de `Depends(require_permission(...))` :

#### Work Orders
- ❌ GET `/work-orders/{wo_id}` - Devrait vérifier `view`
- ❌ GET `/work-orders/{wo_id}/attachments` - Devrait vérifier `view`  
- ❌ GET `/work-orders/{wo_id}/attachments/{attachment_id}` - Devrait vérifier `view`

#### Equipment
- ❌ GET `/equipments/{eq_id}` - Devrait vérifier `assets.view`
- ❌ GET `/equipments/{eq_id}/children` - Devrait vérifier `assets.view`
- ❌ GET `/equipments/{eq_id}/hierarchy` - Devrait vérifier `assets.view`
- ❌ PUT `/equipments/{eq_id}/status` - Devrait vérifier `assets.edit`

#### Locations
- ❌ GET `/locations/{loc_id}/children` - Devrait vérifier `locations.view`

#### Inventory
- ❌ PUT `/inventory/{inv_id}` - Devrait vérifier `inventory.edit`
- ❌ DELETE `/inventory/{inv_id}` - Devrait vérifier `inventory.delete`
- ❌ GET `/inventory/stats` - Devrait vérifier `inventory.view`

#### Users
- ❌ GET `/users` - Devrait vérifier `people.view`
- ❌ GET `/users/{user_id}/permissions` - Devrait être ADMIN only
- ❌ GET `/users/default-permissions/{role}` - Devrait être ADMIN only

#### Settings
- ❌ GET `/settings` - Devrait être ADMIN only
- ❌ PUT `/settings` - Devrait être ADMIN only

### Endpoints qui utilisent correctement `require_permission`

✅ GET `/work-orders` - `require_permission("workOrders", "view")`
✅ POST `/work-orders` - `require_permission("workOrders", "edit")`
✅ PUT `/work-orders/{wo_id}` - `require_permission("workOrders", "edit")`
✅ DELETE `/work-orders/{wo_id}` - `require_permission("workOrders", "delete")`

## 🔧 CORRECTIONS NÉCESSAIRES

1. **Endpoints GET** : Ajouter `require_permission(module, "view")`
2. **Endpoints PUT** : Ajouter `require_permission(module, "edit")`  
3. **Endpoints DELETE** : Ajouter `require_permission(module, "delete")`
4. **Endpoints POST** : Ajouter `require_permission(module, "edit")`
5. **Endpoints Admin** : Remplacer par `Depends(get_current_admin_user)`

## 📊 STATISTIQUE

- Endpoints vérifiés : ~150
- Endpoints avec permissions correctes : ~30%
- Endpoints à corriger : ~70%
- Criticité : **ÉLEVÉE**

Date de l'audit : 23 novembre 2025
