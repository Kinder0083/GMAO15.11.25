import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { surveillanceAPI } from '../../services/api';
import { useToast } from '../../hooks/use-toast';

function SurveillanceItemForm({ open, item, onClose }) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [existingCategories, setExistingCategories] = useState([]);
  const [formData, setFormData] = useState({
    classe_type: '',
    category: '',
    batiment: '',
    periodicite: '',
    responsable: '',
    executant: '',
    description: '',
    derniere_visite: '',
    prochain_controle: '',
    commentaire: '',
    duree_rappel_echeance: 30
  });

  useEffect(() => {
    if (open) {
      loadExistingCategories();
    }
    if (item) {
      setFormData({
        classe_type: item.classe_type || '',
        category: item.category || '',
        batiment: item.batiment || '',
        periodicite: item.periodicite || '',
        responsable: item.responsable || '',
        executant: item.executant || '',
        description: item.description || '',
        derniere_visite: item.derniere_visite ? item.derniere_visite.split('T')[0] : '',
        prochain_controle: item.prochain_controle ? item.prochain_controle.split('T')[0] : '',
        commentaire: item.commentaire || '',
        duree_rappel_echeance: item.duree_rappel_echeance || 30
      });
    }
  }, [item, open]);

  const loadExistingCategories = async () => {
    try {
      const items = await surveillanceAPI.getItems();
      // Extraire toutes les catégories uniques
      const categories = [...new Set(items.map(i => i.category))].filter(Boolean).sort();
      setExistingCategories(categories);
    } catch (error) {
      console.error('Erreur chargement catégories:', error);
      // Catégories par défaut en cas d'erreur
      setExistingCategories(['INCENDIE', 'ELECTRIQUE', 'MMRI', 'SECURITE_ENVIRONNEMENT']);
    }
  };

  const handleSubmit = async () => {
    if (!formData.classe_type || !formData.category || !formData.batiment || !formData.periodicite || !formData.responsable || !formData.executant) {
      toast({ title: 'Erreur', description: 'Champs obligatoires manquants', variant: 'destructive' });
      return;
    }

    setLoading(true);
    try {
      const apiData = { ...formData };
      if (item) {
        await surveillanceAPI.updateItem(item.id, apiData);
        toast({ title: 'Succès', description: 'Item mis à jour' });
      } else {
        await surveillanceAPI.createItem(apiData);
        toast({ title: 'Succès', description: 'Item créé' });
      }
      onClose(true);
    } catch (error) {
      toast({ title: 'Erreur', description: 'Erreur enregistrement', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={() => onClose(false)}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{item ? 'Éditer le contrôle' : 'Nouveau contrôle'}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div>
            <Label>Type de contrôle *</Label>
            <Input value={formData.classe_type} onChange={(e) => setFormData({...formData, classe_type: e.target.value})} placeholder="Ex: Protection incendie" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Catégorie *</Label>
              <Input 
                value={formData.category} 
                onChange={(e) => setFormData({...formData, category: e.target.value.toUpperCase()})} 
                placeholder="Ex: INCENDIE, ELECTRIQUE, NOUVELLE_CATEGORIE..."
                list="categories-list"
              />
              <datalist id="categories-list">
                {existingCategories.map(cat => (
                  <option key={cat} value={cat} />
                ))}
              </datalist>
              <p className="text-xs text-gray-500 mt-1">
                💡 Tapez le nom de la catégorie (ex: INCENDIE) ou créez-en une nouvelle
              </p>
            </div>
            <div>
              <Label>Bâtiment *</Label>
              <Input value={formData.batiment} onChange={(e) => setFormData({...formData, batiment: e.target.value})} placeholder="Ex: BATIMENT 1" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Périodicité *</Label>
              <Input value={formData.periodicite} onChange={(e) => setFormData({...formData, periodicite: e.target.value})} placeholder="Ex: 6 mois" />
            </div>
            <div>
              <Label>Responsable *</Label>
              <Select value={formData.responsable} onValueChange={(val) => setFormData({...formData, responsable: val})}>
                <SelectTrigger><SelectValue placeholder="Sélectionner" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="MAINT">MAINT</SelectItem>
                  <SelectItem value="PROD">PROD</SelectItem>
                  <SelectItem value="QHSE">QHSE</SelectItem>
                  <SelectItem value="EXTERNE">EXTERNE</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label>Exécutant *</Label>
            <Input value={formData.executant} onChange={(e) => setFormData({...formData, executant: e.target.value})} placeholder="Ex: DESAUTEL" />
          </div>

          <div>
            <Label>Description</Label>
            <Textarea value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} rows={2} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Dernière visite</Label>
              <Input type="date" value={formData.derniere_visite} onChange={(e) => setFormData({...formData, derniere_visite: e.target.value})} />
            </div>
            <div>
              <Label>Prochain contrôle</Label>
              <Input type="date" value={formData.prochain_controle} onChange={(e) => setFormData({...formData, prochain_controle: e.target.value})} />
            </div>
          </div>

          <div>
            <Label>Durée de rappel d'échéance (jours)</Label>
            <Input 
              type="number" 
              min="1" 
              max="365" 
              value={formData.duree_rappel_echeance} 
              onChange={(e) => setFormData({...formData, duree_rappel_echeance: parseInt(e.target.value) || 30})} 
              placeholder="30"
            />
            <p className="text-xs text-gray-500 mt-1">Nombre de jours avant l'échéance pour recevoir un rappel</p>
          </div>

          <div>
            <Label>Commentaire</Label>
            <Textarea value={formData.commentaire} onChange={(e) => setFormData({...formData, commentaire: e.target.value})} rows={2} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onClose(false)} disabled={loading}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={loading}>{loading ? 'Enregistrement...' : (item ? 'Mettre à jour' : 'Créer')}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default SurveillanceItemForm;
