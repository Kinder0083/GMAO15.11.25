# Correction des erreurs de validation Pydantic dans le frontend

## Problème
Les erreurs de validation Pydantic du backend retournent un tableau d'objets:
```json
[
  {"type": "...", "loc": [...], "msg": "...", "input": "...", "ctx": {...}, "url": "..."}
]
```

Quand ces erreurs sont affichées directement dans React avec `error.response?.data?.detail`, React essaie d'afficher l'objet et génère l'erreur:
"Objects are not valid as a React child"

## Solution
Utilisation de la fonction `formatErrorMessage()` qui:
1. Détecte si l'erreur est une string, un objet, ou un tableau
2. Formate les erreurs de validation Pydantic en messages lisibles
3. Retourne toujours une string valide pour React

## Fichiers à corriger
Tous les fichiers qui utilisent: `error.response?.data?.detail`

### Import nécessaire
```javascript
import { formatErrorMessage } from '../../utils/errorFormatter';
// ou
import { formatErrorMessage } from '../utils/errorFormatter';
```

### Remplacement
```javascript
// Avant
description: error.response?.data?.detail || 'Message par défaut'

// Après
description: formatErrorMessage(error, 'Message par défaut')
```

## Status
✅ WorkOrderFormDialog.jsx - Corrigé
⏳ 44 autres fichiers à corriger
