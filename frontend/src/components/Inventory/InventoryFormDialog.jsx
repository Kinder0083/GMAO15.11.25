import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { useToast } from '../../hooks/use-toast';
import { inventoryAPI } from '../../services/api';

const InventoryFormDialog = ({ open, onOpenChange, item, onSuccess }) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nom: '',
    reference: '',
    categorie: '',
    quantite: '',
    quantiteMin: '',
    prixUnitaire: '',
    fournisseur: '',
    emplacement: ''
  });

  useEffect(() => {
    if (open) {
      if (item) {
        setFormData({
          nom: item.nom || '',
          reference: item.reference || '',
          categorie: item.categorie || '',
          quantite: item.quantite || '',
          quantiteMin: item.quantiteMin || '',
          prixUnitaire: item.prixUnitaire || '',
          fournisseur: item.fournisseur || '',
          emplacement: item.emplacement || ''
        });
      } else {
        setFormData({
          nom: '',
          reference: '',
          categorie: '',
          quantite: '',
          quantiteMin: '',
          prixUnitaire: '',
          fournisseur: '',
          emplacement: ''
        });
      }
    }
  }, [open, item]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        quantite: parseInt(formData.quantite),
        quantiteMin: parseInt(formData.quantiteMin),
        prixUnitaire: parseFloat(formData.prixUnitaire)
      };

      if (item) {
        await inventoryAPI.update(item.id, submitData);
        toast({
          title: 'Succès',
          description: 'Article modifié avec succès'
        });
      } else {
        await inventoryAPI.create(submitData);
        toast({
          title: 'Succès',
          description: 'Article créé avec succès'
        });
      }

      onSuccess();
      onOpenChange(false);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Une erreur est survenue',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{item ? 'Modifier' : 'Nouvel'} article</DialogTitle>
          <DialogDescription>
            Remplissez les informations de l'article
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="nom">Nom *</Label>
              <Input
                id="nom"
                value={formData.nom}
                onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="reference">Référence *</Label>
              <Input
                id="reference"
                value={formData.reference}
                onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="categorie">Catégorie *</Label>
            <Input
              id="categorie"
              value={formData.categorie}
              onChange={(e) => setFormData({ ...formData, categorie: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="quantite">Quantité *</Label>
              <Input
                id="quantite"
                type="number"
                value={formData.quantite}
                onChange={(e) => setFormData({ ...formData, quantite: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="quantiteMin">Quantité min *</Label>
              <Input
                id="quantiteMin"
                type="number"
                value={formData.quantiteMin}
                onChange={(e) => setFormData({ ...formData, quantiteMin: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="prixUnitaire">Prix unitaire (€) *</Label>
              <Input
                id="prixUnitaire"
                type="number"
                step="0.01"
                value={formData.prixUnitaire}
                onChange={(e) => setFormData({ ...formData, prixUnitaire: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="fournisseur">Fournisseur *</Label>
              <Input
                id="fournisseur"
                value={formData.fournisseur}
                onChange={(e) => setFormData({ ...formData, fournisseur: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="emplacement">Emplacement *</Label>
              <Input
                id="emplacement"
                placeholder="Ex: Entrepôt - Étagère A3"
                value={formData.emplacement}
                onChange={(e) => setFormData({ ...formData, emplacement: e.target.value })}
                required
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
              {loading ? 'Enregistrement...' : item ? 'Modifier' : 'Créer'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default InventoryFormDialog;