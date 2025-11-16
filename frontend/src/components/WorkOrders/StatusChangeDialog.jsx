import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

const StatusChangeDialog = ({ open, onOpenChange, currentStatus, onStatusChange, onSkip, workOrderId }) => {
  const [selectedStatus, setSelectedStatus] = useState(currentStatus || 'OUVERT');
  const [timeHours, setTimeHours] = useState('');
  const [timeMinutes, setTimeMinutes] = useState('');

  const statuses = [
    { value: 'OUVERT', label: 'Ouvert' },
    { value: 'EN_COURS', label: 'En cours' },
    { value: 'EN_ATTENTE', label: 'En attente' },
    { value: 'TERMINE', label: 'Terminé' }
  ];

  const handleConfirm = () => {
    const hours = parseInt(timeHours) || 0;
    const minutes = parseInt(timeMinutes) || 0;
    
    if (selectedStatus !== currentStatus) {
      onStatusChange(selectedStatus, hours, minutes);
    } else {
      onSkip();
    }
  };

  const handleSkip = () => {
    onSkip();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Changer le statut de l'ordre de travail</DialogTitle>
          <DialogDescription>
            Souhaitez-vous mettre à jour le statut de cet ordre de travail avant de fermer ?
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="status">Nouveau statut</Label>
            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger id="status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {statuses.map((status) => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Champ Temps Passé */}
          {selectedStatus === 'TERMINE' && (
            <div className="space-y-2 border-t pt-4">
              <Label>Temps passé sur cet ordre de travail</Label>
              <p className="text-xs text-gray-500 mb-2">
                Enregistrez le temps total passé avant de clôturer (optionnel)
              </p>
              <div className="flex gap-2 items-center">
                <div className="flex-1">
                  <Input
                    type="number"
                    min="0"
                    max="999"
                    placeholder="Heures"
                    value={timeHours}
                    onChange={(e) => setTimeHours(e.target.value)}
                  />
                  <p className="text-xs text-gray-500 mt-1">Heures</p>
                </div>
                <span className="text-2xl text-gray-400 pb-5">:</span>
                <div className="flex-1">
                  <Input
                    type="number"
                    min="0"
                    max="59"
                    placeholder="Minutes"
                    value={timeMinutes}
                    onChange={(e) => setTimeMinutes(e.target.value)}
                  />
                  <p className="text-xs text-gray-500 mt-1">Minutes</p>
                </div>
              </div>
            </div>
          )}
          
          {selectedStatus === currentStatus && (
            <p className="text-sm text-gray-500">
              Le statut actuel est déjà "{statuses.find(s => s.value === currentStatus)?.label}".
            </p>
          )}
        </div>

        <DialogFooter className="flex gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={handleSkip}
          >
            Ne rien changer
          </Button>
          <Button
            type="button"
            onClick={handleConfirm}
            disabled={selectedStatus === currentStatus}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Mettre à jour
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default StatusChangeDialog;
