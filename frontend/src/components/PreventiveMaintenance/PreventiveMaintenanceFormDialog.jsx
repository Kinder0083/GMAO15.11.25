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
import { preventiveMaintenanceAPI, equipmentsAPI, usersAPI } from '../../services/api';

const PreventiveMaintenanceFormDialog = ({ open, onOpenChange, maintenance, onSuccess }) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [equipments, setEquipments] = useState([]);
  const [users, setUsers] = useState([]);
  const [formData, setFormData] = useState({
    titre: '',
    equipement_id: '',
    frequence: 'MENSUEL',
    prochaineMaintenance: '',
    assigne_a_id: '',
    duree: '',
    statut: 'ACTIF'
  });

  useEffect(() => {
    if (open) {
      loadData();
      if (maintenance) {
        setFormData({
          titre: maintenance.titre || '',
          equipement_id: maintenance.equipement?.id || '',
          frequence: maintenance.frequence || 'MENSUEL',
          prochaineMaintenance: maintenance.prochaineMaintenance?.split('T')[0] || '',
          assigne_a_id: maintenance.assigneA?.id || '',
          duree: maintenance.duree || '',
          statut: maintenance.statut || 'ACTIF'
        });
      } else {
        setFormData({
          titre: '',
          equipement_id: '',
          frequence: 'MENSUEL',
          prochaineMaintenance: '',
          assigne_a_id: '',
          duree: '',
          statut: 'ACTIF'
        });
      }
    }
  }, [open, maintenance]);

  const loadData = async () => {
    try {
      const [equipRes, userRes] = await Promise.all([
        equipmentsAPI.getAll(),
        usersAPI.getAll()
      ]);
      setEquipments(equipRes.data);
      setUsers(userRes.data);
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
        duree: parseFloat(formData.duree),
        prochaineMaintenance: new Date(formData.prochaineMaintenance).toISOString()
      };

      if (maintenance) {
        await preventiveMaintenanceAPI.update(maintenance.id, submitData);
        toast({
          title: 'Succès',
          description: 'Maintenance préventive modifiée avec succès'
        });
      } else {
        await preventiveMaintenanceAPI.create(submitData);
        toast({
          title: 'Succès',
          description: 'Maintenance préventive créée avec succès'
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
          <DialogTitle>{maintenance ? 'Modifier' : 'Nouvelle'} maintenance préventive</DialogTitle>
          <DialogDescription>
            Remplissez les informations de la maintenance préventive
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="titre">Titre *</Label>
            <Input
              id="titre"
              value={formData.titre}
              onChange={(e) => setFormData({ ...formData, titre: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="equipement_id">Équipement *</Label>
            <Select value={formData.equipement_id} onValueChange={(value) => setFormData({ ...formData, equipement_id: value })}>
              <SelectTrigger>
                <SelectValue placeholder="Sélectionner un équipement" />
              </SelectTrigger>
              <SelectContent>
                {equipments.map(eq => (
                  <SelectItem key={eq.id} value={eq.id}>{eq.nom}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="frequence">Fréquence *</Label>
              <Select value={formData.frequence} onValueChange={(value) => setFormData({ ...formData, frequence: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="HEBDOMADAIRE">Hebdomadaire</SelectItem>
                  <SelectItem value="MENSUEL">Mensuel</SelectItem>
                  <SelectItem value="TRIMESTRIEL">Trimestriel</SelectItem>
                  <SelectItem value="ANNUEL">Annuel</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="statut">Statut</Label>
              <Select value={formData.statut} onValueChange={(value) => setFormData({ ...formData, statut: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ACTIF">Actif</SelectItem>
                  <SelectItem value="INACTIF">Inactif</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="assigne_a_id">Assigné à *</Label>
            <Select value={formData.assigne_a_id} onValueChange={(value) => setFormData({ ...formData, assigne_a_id: value })}>
              <SelectTrigger>
                <SelectValue placeholder="Sélectionner un technicien" />
              </SelectTrigger>
              <SelectContent>
                {users.map(user => (
                  <SelectItem key={user.id} value={user.id}>
                    {user.prenom} {user.nom}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="prochaineMaintenance">Prochaine maintenance *</Label>
              <Input
                id="prochaineMaintenance"
                type="date"
                value={formData.prochaineMaintenance}
                onChange={(e) => setFormData({ ...formData, prochaineMaintenance: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="duree">Durée estimée (heures) *</Label>
              <Input
                id="duree"
                type="number"
                step="0.5"
                value={formData.duree}
                onChange={(e) => setFormData({ ...formData, duree: e.target.value })}
                required
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
              {loading ? 'Enregistrement...' : maintenance ? 'Modifier' : 'Créer'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default PreventiveMaintenanceFormDialog;