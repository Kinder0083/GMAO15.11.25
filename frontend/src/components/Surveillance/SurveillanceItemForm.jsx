import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  MenuItem,
  CircularProgress
} from '@mui/material';
import { surveillanceAPI } from '../../services/api';
import { toast } from 'react-toastify';

function SurveillanceItemForm({ open, item, onClose }) {
  const [loading, setLoading] = useState(false);
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
    commentaire: ''
  });

  useEffect(() => {
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
        commentaire: item.commentaire || ''
      });
    }
  }, [item]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    // Validation
    if (!formData.classe_type || !formData.category || !formData.batiment || 
        !formData.periodicite || !formData.responsable || !formData.executant) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setLoading(true);
    try {
      // Préparer les données pour l'API
      const apiData = {
        classe_type: formData.classe_type,
        category: formData.category,
        batiment: formData.batiment,
        periodicite: formData.periodicite,
        responsable: formData.responsable,
        executant: formData.executant,
        description: formData.description || undefined,
        derniere_visite: formData.derniere_visite || undefined,
        prochain_controle: formData.prochain_controle || undefined,
        commentaire: formData.commentaire || undefined
      };

      if (item) {
        // Mise à jour
        await surveillanceAPI.updateItem(item.id, apiData);
        toast.success('Item mis à jour avec succès');
      } else {
        // Création
        await surveillanceAPI.createItem(apiData);
        toast.success('Item créé avec succès');
      }
      onClose(true);
    } catch (error) {
      console.error('Erreur:', error);
      toast.error('Erreur lors de l\'enregistrement');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={() => onClose(false)} maxWidth="md" fullWidth>
      <DialogTitle>
        {item ? 'Éditer le contrôle' : 'Nouveau contrôle'}
      </DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              label="Type de contrôle"
              value={formData.classe_type}
              onChange={(e) => handleChange('classe_type', e.target.value)}
              placeholder="Ex: Protection incendie"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              required
              select
              label="Catégorie"
              value={formData.category}
              onChange={(e) => handleChange('category', e.target.value)}
            >
              <MenuItem value="MMRI">MMRI</MenuItem>
              <MenuItem value="INCENDIE">Incendie</MenuItem>
              <MenuItem value="SECURITE_ENVIRONNEMENT">Sécurité/Environnement</MenuItem>
              <MenuItem value="ELECTRIQUE">Électrique</MenuItem>
              <MenuItem value="MANUTENTION">Manutention</MenuItem>
              <MenuItem value="EXTRACTION">Extraction</MenuItem>
              <MenuItem value="AUTRE">Autre</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              required
              label="Bâtiment"
              value={formData.batiment}
              onChange={(e) => handleChange('batiment', e.target.value)}
              placeholder="Ex: BATIMENT 1"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              required
              label="Périodicité"
              value={formData.periodicite}
              onChange={(e) => handleChange('periodicite', e.target.value)}
              placeholder="Ex: 6 mois, 1 an"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              required
              select
              label="Responsable"
              value={formData.responsable}
              onChange={(e) => handleChange('responsable', e.target.value)}
            >
              <MenuItem value="MAINT">MAINT</MenuItem>
              <MenuItem value="PROD">PROD</MenuItem>
              <MenuItem value="QHSE">QHSE</MenuItem>
              <MenuItem value="EXTERNE">EXTERNE</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              label="Exécutant"
              value={formData.executant}
              onChange={(e) => handleChange('executant', e.target.value)}
              placeholder="Ex: DESAUTEL, APAVE"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Description"
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Description détaillée du contrôle"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="date"
              label="Dernière visite"
              value={formData.derniere_visite}
              onChange={(e) => handleChange('derniere_visite', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="date"
              label="Prochain contrôle"
              value={formData.prochain_controle}
              onChange={(e) => handleChange('prochain_controle', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Commentaire"
              value={formData.commentaire}
              onChange={(e) => handleChange('commentaire', e.target.value)}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => onClose(false)} disabled={loading}>
          Annuler
        </Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading}>
          {loading ? <CircularProgress size={24} /> : (item ? 'Mettre à jour' : 'Créer')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default SurveillanceItemForm;
