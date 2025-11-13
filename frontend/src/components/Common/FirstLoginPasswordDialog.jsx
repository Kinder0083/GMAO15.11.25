import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { PasswordInput } from '../ui/password-input';
import { Label } from '../ui/label';
import { authAPI } from '../../services/api';
import { useToast } from '../../hooks/use-toast';
import { Loader2, Lock, AlertCircle } from 'lucide-react';

const FirstLoginPasswordDialog = ({ open, onOpenChange, onSuccess }) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({});

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.oldPassword) {
      newErrors.oldPassword = 'Le mot de passe actuel est requis';
    }

    if (!formData.newPassword) {
      newErrors.newPassword = 'Le nouveau mot de passe est requis';
    } else if (formData.newPassword.length < 8) {
      newErrors.newPassword = 'Le mot de passe doit contenir au moins 8 caractères';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Veuillez confirmer le mot de passe';
    } else if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Les mots de passe ne correspondent pas';
    }

    if (formData.oldPassword && formData.newPassword && formData.oldPassword === formData.newPassword) {
      newErrors.newPassword = 'Le nouveau mot de passe doit être différent de l\'ancien';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      await authAPI.changePasswordFirstLogin({
        old_password: formData.oldPassword,
        new_password: formData.newPassword
      });
      
      toast({
        title: 'Mot de passe changé !',
        description: 'Votre mot de passe a été mis à jour avec succès.',
      });

      // Reset form
      setFormData({
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      });

      onOpenChange(false);
      if (onSuccess) onSuccess();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Impossible de changer le mot de passe',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSkipPasswordChange = async () => {
    // Confirmer avec l'utilisateur
    const confirmed = window.confirm(
      "⚠️ ATTENTION ⚠️\n\n" +
      "Vous êtes sur le point de conserver votre mot de passe temporaire.\n\n" +
      "Cela représente un risque de sécurité car d'autres personnes peuvent connaître ce mot de passe.\n\n" +
      "Êtes-vous sûr de vouloir continuer à vos risques et périls ?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setLoading(true);
      await authAPI.skipPasswordChange();
      
      toast({
        title: 'Mot de passe conservé',
        description: 'Vous avez choisi de garder votre mot de passe temporaire.',
        variant: 'default'
      });

      onOpenChange(false);
      if (onSuccess) onSuccess();
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
      <DialogContent className="sm:max-w-[450px]" onInteractOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="bg-amber-100 p-2 rounded-full">
              <AlertCircle className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <DialogTitle>Changement de mot de passe requis</DialogTitle>
              <DialogDescription className="mt-1">
                Pour des raisons de sécurité, vous devez changer votre mot de passe temporaire.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="oldPassword">Mot de passe actuel *</Label>
              <PasswordInput
                id="oldPassword"
                value={formData.oldPassword}
                onChange={(e) => handleChange('oldPassword', e.target.value)}
                className={errors.oldPassword ? 'border-red-500' : ''}
              />
              {errors.oldPassword && (
                <p className="text-xs text-red-500">{errors.oldPassword}</p>
              )}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="newPassword">Nouveau mot de passe *</Label>
              <PasswordInput
                id="newPassword"
                value={formData.newPassword}
                onChange={(e) => handleChange('newPassword', e.target.value)}
                className={errors.newPassword ? 'border-red-500' : ''}
              />
              {errors.newPassword && (
                <p className="text-xs text-red-500">{errors.newPassword}</p>
              )}
              <p className="text-xs text-gray-500">Minimum 8 caractères</p>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="confirmPassword">Confirmer le nouveau mot de passe *</Label>
              <PasswordInput
                id="confirmPassword"
                value={formData.confirmPassword}
                onChange={(e) => handleChange('confirmPassword', e.target.value)}
                className={errors.confirmPassword ? 'border-red-500' : ''}
              />
              {errors.confirmPassword && (
                <p className="text-xs text-red-500">{errors.confirmPassword}</p>
              )}
            </div>
          </div>

          <DialogFooter className="flex-col gap-2 sm:flex-col">
            <Button type="submit" disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Changement en cours...
                </>
              ) : (
                <>
                  <Lock className="mr-2 h-4 w-4" />
                  Changer le mot de passe
                </>
              )}
            </Button>
            
            <Button
              type="button"
              onClick={handleSkipPasswordChange}
              disabled={loading}
              variant="destructive"
              className="w-full bg-red-600 hover:bg-red-700 text-white"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  En cours...
                </>
              ) : (
                <>
                  <AlertCircle className="mr-2 h-4 w-4" />
                  Ne pas changer le mot de passe à vos risques
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default FirstLoginPasswordDialog;
