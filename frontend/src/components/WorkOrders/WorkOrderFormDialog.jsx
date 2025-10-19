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
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Paperclip } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import { workOrdersAPI, equipmentsAPI, locationsAPI, usersAPI } from '../../services/api';

const WorkOrderFormDialog = ({ open, onOpenChange, workOrder, onSuccess }) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [equipments, setEquipments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [users, setUsers] = useState([]);
  const [formData, setFormData] = useState({
    titre: '',
    description: '',
    statut: 'OUVERT',
    priorite: 'AUCUNE',
    equipement_id: '',
    assigne_a_id: '',
    emplacement_id: '',
    dateLimite: '',
    tempsEstime: ''
  });
  const [attachments, setAttachments] = useState([]);

  useEffect(() => {
    if (open) {
      loadData();
      if (workOrder) {
        setFormData({
          titre: workOrder.titre || '',
          description: workOrder.description || '',
          statut: workOrder.statut || 'OUVERT',
          priorite: workOrder.priorite || 'AUCUNE',
          equipement_id: workOrder.equipement?.id || '',
          assigne_a_id: workOrder.assigneA?.id || '',
          emplacement_id: workOrder.emplacement?.id || '',
          dateLimite: workOrder.dateLimite?.split('T')[0] || '',
          tempsEstime: workOrder.tempsEstime || ''
        });
      } else {
        setFormData({
          titre: '',
          description: '',
          statut: 'OUVERT',
          priorite: 'AUCUNE',
          equipement_id: '',
          assigne_a_id: '',
          emplacement_id: '',
          dateLimite: '',
          tempsEstime: ''
        });
        setAttachments([]);
      }
    }
  }, [open, workOrder]);

  const loadData = async () => {
    try {
      const [equipRes, locRes, userRes] = await Promise.all([
        equipmentsAPI.getAll(),
        locationsAPI.getAll(),
        usersAPI.getAll()
      ]);
      setEquipments(equipRes.data);
      setLocations(locRes.data);
      setUsers(userRes.data.filter(u => u.role === 'TECHNICIEN' || u.role === 'ADMIN'));
    } catch (error) {
      console.error('Erreur de chargement:', error);
    }
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files || []);
    const newAttachments = files.map(file => ({
      file,
      name: file.name,
      size: file.size
    }));
    setAttachments([...attachments, ...newAttachments]);
    event.target.value = ''; // Reset input
  };

  const handleRemoveAttachment = (index) => {
    setAttachments(attachments.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        tempsEstime: formData.tempsEstime ? parseFloat(formData.tempsEstime) : null,
        dateLimite: formData.dateLimite ? new Date(formData.dateLimite).toISOString() : null,
        equipement_id: formData.equipement_id || null,
        assigne_a_id: formData.assigne_a_id || null,
        emplacement_id: formData.emplacement_id || null
      };

      if (workOrder) {
        await workOrdersAPI.update(workOrder.id, submitData);
        
        // Upload des fichiers si présents
        if (attachments.length > 0) {
          for (const attachment of attachments) {
            try {
              await workOrdersAPI.addAttachment(workOrder.id, attachment.file);
            } catch (err) {
              console.error('Erreur upload fichier:', err);
            }
          }
        }
        
        toast({
          title: 'Succès',
          description: 'Ordre de travail modifié avec succès'
        });
      } else {
        const response = await workOrdersAPI.create(submitData);
        const newWorkOrderId = response.data.id;
        
        // Upload des fichiers si présents
        if (attachments.length > 0) {
          for (const attachment of attachments) {
            try {
              await workOrdersAPI.addAttachment(newWorkOrderId, attachment.file);
            } catch (err) {
              console.error('Erreur upload fichier:', err);
            }
          }
        }
        
        toast({
          title: 'Succès',
          description: 'Ordre de travail créé avec succès'
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
          <DialogTitle>{workOrder ? 'Modifier' : 'Nouvel'} ordre de travail</DialogTitle>
          <DialogDescription>
            Remplissez les informations de l'ordre de travail
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
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="statut">Statut</Label>
              <Select value={formData.statut} onValueChange={(value) => setFormData({ ...formData, statut: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="OUVERT">Ouvert</SelectItem>
                  <SelectItem value="EN_COURS">En cours</SelectItem>
                  <SelectItem value="EN_ATTENTE">En attente</SelectItem>
                  <SelectItem value="TERMINE">Terminé</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="priorite">Priorité</Label>
              <Select value={formData.priorite} onValueChange={(value) => setFormData({ ...formData, priorite: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="HAUTE">Haute</SelectItem>
                  <SelectItem value="MOYENNE">Moyenne</SelectItem>
                  <SelectItem value="BASSE">Basse</SelectItem>
                  <SelectItem value="AUCUNE">Normale</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="equipement_id">Équipement</Label>
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

          <div className="space-y-2">
            <Label htmlFor="assigne_a_id">Assigné à</Label>
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

          <div className="space-y-2">
            <Label htmlFor="emplacement_id">Emplacement</Label>
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
              <Label htmlFor="dateLimite">Date limite</Label>
              <Input
                id="dateLimite"
                type="date"
                value={formData.dateLimite}
                onChange={(e) => setFormData({ ...formData, dateLimite: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tempsEstime">Temps estimé (heures)</Label>
              <Input
                id="tempsEstime"
                type="number"
                step="0.5"
                value={formData.tempsEstime}
                onChange={(e) => setFormData({ ...formData, tempsEstime: e.target.value })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
              {loading ? 'Enregistrement...' : workOrder ? 'Modifier' : 'Créer'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default WorkOrderFormDialog;