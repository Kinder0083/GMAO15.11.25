import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Checkbox } from '../ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Card, CardContent } from '../ui/card';
import { equipmentsAPI, workOrdersAPI, preventiveMaintenanceAPI, usersAPI, demandesArretAPI } from '../../services/api';
import { useToast } from '../../hooks/use-toast';
import { Calendar, Clock } from 'lucide-react';

const DemandeArretDialog = ({ open, onOpenChange, onSuccess }) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [equipments, setEquipments] = useState([]);
  const [workOrders, setWorkOrders] = useState([]);
  const [preventiveMaintenances, setPreventiveMaintenances] = useState([]);
  const [users, setUsers] = useState([]);
  const [rspProdUser, setRspProdUser] = useState(null);

  const [formData, setFormData] = useState({
    date_debut: '',
    date_fin: '',
    periode_debut: 'JOURNEE_COMPLETE',
    periode_fin: 'JOURNEE_COMPLETE',
    equipement_ids: [],
    work_order_id: null,
    maintenance_preventive_id: null,
    commentaire: '',
    destinataire_id: ''
  });

  useEffect(() => {
    if (open) {
      loadData();
    }
  }, [open]);

  const loadData = async () => {
    try {
      // Charger équipements
      const eqResponse = await equipmentsAPI.getAll();
      setEquipments(eqResponse.data || []);

      // Charger work orders
      const woResponse = await workOrdersAPI.getAll();
      setWorkOrders(woResponse.data || []);

      // Charger maintenances préventives
      const pmResponse = await preventiveMaintenanceAPI.getAll();
      setPreventiveMaintenances(pmResponse.data || []);

      // Charger utilisateurs
      const usersResponse = await usersAPI.getAll();
      setUsers(usersResponse.data || []);

      // Trouver l'utilisateur avec le rôle RSP_PROD
      const rspProd = (usersResponse.data || []).find(user => user.role === 'RSP_PROD');
      if (rspProd) {
        setRspProdUser(rspProd);
        setFormData(prev => ({ ...prev, destinataire_id: rspProd.id }));
      }
    } catch (error) {
      console.error('Erreur chargement données:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les données',
        variant: 'destructive'
      });
    }
  };

  const handleEquipmentToggle = (equipmentId) => {
    setFormData(prev => {
      const isSelected = prev.equipement_ids.includes(equipmentId);
      return {
        ...prev,
        equipement_ids: isSelected
          ? prev.equipement_ids.filter(id => id !== equipmentId)
          : [...prev.equipement_ids, equipmentId]
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.date_debut || !formData.date_fin) {
      toast({
        title: 'Erreur',
        description: 'Les dates de début et fin sont obligatoires',
        variant: 'destructive'
      });
      return;
    }

    if (formData.equipement_ids.length === 0) {
      toast({
        title: 'Erreur',
        description: 'Veuillez sélectionner au moins un équipement',
        variant: 'destructive'
      });
      return;
    }

    if (!formData.destinataire_id) {
      toast({
        title: 'Erreur',
        description: 'Veuillez sélectionner un destinataire',
        variant: 'destructive'
      });
      return;
    }

    try {
      setLoading(true);
      await demandesArretAPI.create(formData);
      
      toast({
        title: 'Succès',
        description: 'Demande d\'arrêt envoyée avec succès'
      });
      
      // Réinitialiser le formulaire
      setFormData({
        date_debut: '',
        date_fin: '',
        periode_debut: 'JOURNEE_COMPLETE',
        periode_fin: 'JOURNEE_COMPLETE',
        equipement_ids: [],
        work_order_id: null,
        maintenance_preventive_id: null,
        commentaire: '',
        destinataire_id: rspProdUser?.id || ''
      });
      
      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('Erreur création demande:', error);
      toast({
        title: 'Erreur',
        description: 'Erreur lors de l\'envoi de la demande',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Demande d'Arrêt pour Maintenance</DialogTitle>
          <DialogDescription>
            Remplissez le formulaire pour demander l'arrêt d'un ou plusieurs équipements pour maintenance.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-6 py-4">
            {/* Période d'arrêt */}
            <Card>
              <CardContent className="pt-6 space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Période d'Arrêt Demandée *
                </h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="date_debut">Date de début *</Label>
                    <Input
                      id="date_debut"
                      type="date"
                      value={formData.date_debut}
                      onChange={(e) => setFormData(prev => ({ ...prev, date_debut: e.target.value }))}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="date_fin">Date de fin *</Label>
                    <Input
                      id="date_fin"
                      type="date"
                      value={formData.date_fin}
                      onChange={(e) => setFormData(prev => ({ ...prev, date_fin: e.target.value }))}
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Période début</Label>
                    <RadioGroup
                      value={formData.periode_debut}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, periode_debut: value }))}
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="JOURNEE_COMPLETE" id="debut_journee" />
                        <label htmlFor="debut_journee" className="text-sm cursor-pointer">Journée complète</label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="MATIN" id="debut_matin" />
                        <label htmlFor="debut_matin" className="text-sm cursor-pointer">Matin (8h-12h)</label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="APRES_MIDI" id="debut_aprem" />
                        <label htmlFor="debut_aprem" className="text-sm cursor-pointer">Après-midi (13h-17h)</label>
                      </div>
                    </RadioGroup>
                  </div>
                  <div>
                    <Label>Période fin</Label>
                    <RadioGroup
                      value={formData.periode_fin}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, periode_fin: value }))}
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="JOURNEE_COMPLETE" id="fin_journee" />
                        <label htmlFor="fin_journee" className="text-sm cursor-pointer">Journée complète</label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="MATIN" id="fin_matin" />
                        <label htmlFor="fin_matin" className="text-sm cursor-pointer">Matin (8h-12h)</label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="APRES_MIDI" id="fin_aprem" />
                        <label htmlFor="fin_aprem" className="text-sm cursor-pointer">Après-midi (13h-17h)</label>
                      </div>
                    </RadioGroup>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Équipements */}
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-3">Équipements concernés *</h3>
                <div className="max-h-60 overflow-y-auto space-y-2 border rounded p-3">
                  {equipments.length === 0 ? (
                    <p className="text-sm text-gray-500">Aucun équipement disponible</p>
                  ) : (
                    equipments.map((equipment) => (
                      <div key={equipment.id} className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded">
                        <Checkbox
                          id={`eq-${equipment.id}`}
                          checked={formData.equipement_ids.includes(equipment.id)}
                          onCheckedChange={() => handleEquipmentToggle(equipment.id)}
                        />
                        <label htmlFor={`eq-${equipment.id}`} className="text-sm cursor-pointer flex-1">
                          <span className="font-medium">{equipment.name}</span>
                          {equipment.category && <span className="text-gray-500 ml-2">• {equipment.category}</span>}
                        </label>
                      </div>
                    ))
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {formData.equipement_ids.length} équipement(s) sélectionné(s)
                </p>
              </CardContent>
            </Card>

            {/* Ordre de travail / Maintenance préventive */}
            <Card>
              <CardContent className="pt-6 space-y-4">
                <h3 className="font-semibold">Lier à un document (optionnel)</h3>
                
                <div>
                  <Label htmlFor="work_order">Ordre de Travail</Label>
                  <Select
                    value={formData.work_order_id || 'none'}
                    onValueChange={(value) => setFormData(prev => ({
                      ...prev,
                      work_order_id: value === 'none' ? null : value,
                      maintenance_preventive_id: null // Reset l'autre
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Sélectionner un ordre de travail" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Aucun</SelectItem>
                      {workOrders.filter(wo => wo.id && wo.id !== '').map(wo => (
                        <SelectItem key={wo.id} value={wo.id}>
                          {wo.title || wo.titre || `Ordre ${wo.order_number || wo.numero}`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="maintenance_preventive">Maintenance Préventive</Label>
                  <Select
                    value={formData.maintenance_preventive_id || 'none'}
                    onValueChange={(value) => setFormData(prev => ({
                      ...prev,
                      maintenance_preventive_id: value === 'none' ? null : value,
                      work_order_id: null // Reset l'autre
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Sélectionner une maintenance préventive" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Aucune</SelectItem>
                      {preventiveMaintenances.filter(pm => pm.id && pm.id !== '').map(pm => (
                        <SelectItem key={pm.id} value={pm.id}>
                          {pm.title || pm.titre || pm.name || pm.nom}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Commentaire */}
            <div>
              <Label htmlFor="commentaire">Commentaire</Label>
              <Textarea
                id="commentaire"
                placeholder="Ajoutez des détails sur la demande d'arrêt..."
                value={formData.commentaire}
                onChange={(e) => setFormData(prev => ({ ...prev, commentaire: e.target.value }))}
                rows={4}
              />
            </div>

            {/* Destinataire */}
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-3">Destinataire de la demande *</h3>
                <Select
                  value={formData.destinataire_id}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, destinataire_id: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner le destinataire" />
                  </SelectTrigger>
                  <SelectContent>
                    {users.filter(user => user.id && user.id !== '').map(user => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.first_name || user.prenom} {user.last_name || user.nom} 
                        {user.role === 'RSP_PROD' && ' (Resp. Production - Par défaut)'}
                        {user.email && ` - ${user.email}`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {rspProdUser && (
                  <p className="text-xs text-gray-500 mt-2">
                    Par défaut : {rspProdUser.first_name} {rspProdUser.last_name} (Responsable Production)
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Envoi...' : 'Envoyer la demande'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default DemandeArretDialog;
