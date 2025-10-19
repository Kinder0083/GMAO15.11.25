import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from '../ui/dialog';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { Calendar, Clock, User, MapPin, Wrench, FileText } from 'lucide-react';
import AttachmentsList from './AttachmentsList';
import AttachmentUploader from './AttachmentUploader';

const WorkOrderDialog = ({ open, onOpenChange, workOrder }) => {
  const [refreshAttachments, setRefreshAttachments] = useState(0);
  
  if (!workOrder) return null;

  const handleUploadComplete = () => {
    setRefreshAttachments(prev => prev + 1);
  };

  const getStatusBadge = (statut) => {
    const badges = {
      'OUVERT': { variant: 'secondary', label: 'Ouvert' },
      'EN_COURS': { variant: 'default', label: 'En cours' },
      'EN_ATTENTE': { variant: 'outline', label: 'En attente' },
      'TERMINE': { variant: 'success', label: 'Terminé' }
    };
    const badge = badges[statut] || badges['OUVERT'];
    return <Badge variant={badge.variant}>{badge.label}</Badge>;
  };

  const getPriorityBadge = (priorite) => {
    const badges = {
      'HAUTE': { variant: 'destructive', label: 'Haute' },
      'MOYENNE': { variant: 'default', label: 'Moyenne' },
      'BASSE': { variant: 'secondary', label: 'Basse' },
      'AUCUNE': { variant: 'outline', label: 'Normale' }
    };
    const badge = badges[priorite] || badges['AUCUNE'];
    return <Badge variant={badge.variant}>{badge.label}</Badge>;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-2xl">Ordre de travail #{workOrder.id}</DialogTitle>
            <div className="flex gap-2">
              {getStatusBadge(workOrder.statut)}
              {getPriorityBadge(workOrder.priorite)}
            </div>
          </div>
          <DialogDescription className="text-lg font-medium text-gray-700 mt-2">
            {workOrder.titre}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Description */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <FileText size={18} className="text-gray-600" />
              <h3 className="font-semibold text-gray-900">Description</h3>
            </div>
            <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">{workOrder.description}</p>
          </div>

          <Separator />

          {/* Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Date de création */}
            <div className="flex items-start gap-3">
              <Calendar size={18} className="text-blue-600 mt-1" />
              <div>
                <p className="text-sm text-gray-600">Date de création</p>
                <p className="font-medium text-gray-900">{workOrder.dateCreation}</p>
              </div>
            </div>

            {/* Date limite */}
            <div className="flex items-start gap-3">
              <Calendar size={18} className="text-red-600 mt-1" />
              <div>
                <p className="text-sm text-gray-600">Date limite</p>
                <p className="font-medium text-gray-900">{workOrder.dateLimite}</p>
              </div>
            </div>

            {/* Temps estimé */}
            <div className="flex items-start gap-3">
              <Clock size={18} className="text-green-600 mt-1" />
              <div>
                <p className="text-sm text-gray-600">Temps estimé</p>
                <p className="font-medium text-gray-900">{workOrder.tempsEstime}h</p>
              </div>
            </div>

            {/* Temps réel */}
            <div className="flex items-start gap-3">
              <Clock size={18} className="text-orange-600 mt-1" />
              <div>
                <p className="text-sm text-gray-600">Temps réel</p>
                <p className="font-medium text-gray-900">
                  {workOrder.tempsReel ? `${workOrder.tempsReel}h` : 'Non démarré'}
                </p>
              </div>
            </div>

            {/* Assigné à */}
            {workOrder.assigneA && (
              <div className="flex items-start gap-3">
                <User size={18} className="text-purple-600 mt-1" />
                <div>
                  <p className="text-sm text-gray-600">Assigné à</p>
                  <p className="font-medium text-gray-900">
                    {workOrder.assigneA.prenom} {workOrder.assigneA.nom}
                  </p>
                  <p className="text-xs text-gray-500">{workOrder.assigneA.email}</p>
                </div>
              </div>
            )}

            {/* Emplacement */}
            {workOrder.emplacement && (
              <div className="flex items-start gap-3">
                <MapPin size={18} className="text-indigo-600 mt-1" />
                <div>
                  <p className="text-sm text-gray-600">Emplacement</p>
                  <p className="font-medium text-gray-900">{workOrder.emplacement.nom}</p>
                </div>
              </div>
            )}

            {/* Équipement */}
            {workOrder.equipement && (
              <div className="flex items-start gap-3 md:col-span-2">
                <Wrench size={18} className="text-amber-600 mt-1" />
                <div>
                  <p className="text-sm text-gray-600">Équipement</p>
                  <p className="font-medium text-gray-900">{workOrder.equipement.nom}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default WorkOrderDialog;