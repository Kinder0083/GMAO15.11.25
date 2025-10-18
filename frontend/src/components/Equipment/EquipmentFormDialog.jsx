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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { useToast } from '../../hooks/use-toast';
import { equipmentsAPI, locationsAPI } from '../../services/api';

const EquipmentFormDialog = ({ open, onOpenChange, equipment, onSuccess }) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [locations, setLocations] = useState([]);
  const [formData, setFormData] = useState({
    nom: '',
    categorie: '',
    emplacement_id: '',
    statut: 'OPERATIONNEL',
    dateAchat: '',
    coutAchat: '',
    numeroSerie: '',
    garantie: ''
  });

  useEffect(() => {
    if (open) {
      loadLocations();
      if (equipment) {
        setFormData({
          nom: equipment.nom || '',
          categorie: equipment.categorie || '',
          emplacement_id: equipment.emplacement?.id || '',
          statut: equipment.statut || 'OPERATIONNEL',
          dateAchat: equipment.dateAchat?.split('T')[0] || '',
          coutAchat: equipment.coutAchat || '',
          numeroSerie: equipment.numeroSerie || '',
          garantie: equipment.garantie || ''
        });
      } else {
        setFormData({
          nom: '',
          categorie: '',
          emplacement_id: '',
          statut: 'OPERATIONNEL',
          dateAchat: '',
          coutAchat: '',
          numeroSerie: '',
          garantie: ''
        });
      }
    }
  }, [open, equipment]);

  const loadLocations = async () => {
    try {
      const response = await locationsAPI.getAll();
      setLocations(response.data);
    } catch (error) {
      console.error('Erreur de chargement:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        coutAchat: parseFloat(formData.coutAchat),
        dateAchat: new Date(formData.dateAchat).toISOString()
      };

      if (equipment) {
        await equipmentsAPI.update(equipment.id, submitData);
        toast({
          title: 'Succès',
          description: 'Équipement modifié avec succès'
        });
      } else {
        await equipmentsAPI.create(submitData);
        toast({
          title: 'Succès',
          description: 'Équipement créé avec succès'
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
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{equipment ? 'Modifier' : 'Nouvel'} équipement</DialogTitle>
          <DialogDescription>
            Remplissez les informations de l'équipement
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="nom">Nom *</Label>
            <Input
              id="nom"
              value={formData.nom}
              onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="categorie">Catégorie *</Label>
              <Input
                id="categorie"
                value={formData.categorie}
                onChange={(e) => setFormData({ ...formData, categorie: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="statut">Statut</Label>
              <Select value={formData.statut} onValueChange={(value) => setFormData({ ...formData, statut: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="OPERATIONNEL">Opérationnel</SelectItem>
                  <SelectItem value="EN_MAINTENANCE">En maintenance</SelectItem>
                  <SelectItem value="HORS_SERVICE">Hors service</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="emplacement_id">Emplacement *</Label>
            <Select value={formData.emplacement_id} onValueChange={(value) => setFormData({ ...formData, emplacement_id: value })}>
              <SelectTrigger>
                <SelectValue placeholder="Sélectionner un emplacement" />
              </SelectTrigger>
              <SelectContent>
                {locations.map(loc => (
                  <SelectItem key={loc.id} value={loc.id}>{loc.nom}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="numeroSerie">Numéro de série *</Label>
              <Input
                id="numeroSerie"
                value={formData.numeroSerie}
                onChange={(e) => setFormData({ ...formData, numeroSerie: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="garantie">Garantie</Label>
              <Input
                id="garantie"
                placeholder="Ex: 2 ans"
                value={formData.garantie}
                onChange={(e) => setFormData({ ...formData, garantie: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="dateAchat">Date d'achat *</Label>
              <Input
                id="dateAchat"
                type="date"
                value={formData.dateAchat}
                onChange={(e) => setFormData({ ...formData, dateAchat: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="coutAchat">Coût d'achat (€) *</Label>
              <Input
                id="coutAchat"
                type="number"
                step="0.01"
                value={formData.coutAchat}
                onChange={(e) => setFormData({ ...formData, coutAchat: e.target.value })}
                required
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
              {loading ? 'Enregistrement...' : equipment ? 'Modifier' : 'Créer'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default EquipmentFormDialog;