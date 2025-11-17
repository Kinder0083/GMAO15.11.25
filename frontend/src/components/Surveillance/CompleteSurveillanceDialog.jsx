import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  CircularProgress
} from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { surveillanceAPI } from '../../services/api';
import { toast } from 'react-toastify';

function CompleteSurveillanceDialog({ open, item, onClose }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    date_realisation: new Date().toISOString().split('T')[0],
    commentaire: '',
    status: 'REALISE'
  });
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // 1. Mettre à jour le statut et les infos
      await surveillanceAPI.updateItem(item.id, {
        status: formData.status,
        date_realisation: formData.date_realisation,
        commentaire: formData.commentaire
      });

      // 2. Uploader le fichier si présent
      if (selectedFile) {
        await surveillanceAPI.uploadFile(item.id, selectedFile);
      }

      toast.success('Contrôle marqué comme réalisé');
      onClose(true);
    } catch (error) {
      console.error('Erreur:', error);
      toast.error('Erreur lors de la mise à jour');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={() => onClose(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Marquer comme réalisé</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Contrôle:</strong> {item?.classe_type}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            <strong>Bâtiment:</strong> {item?.batiment}
          </Typography>

          <TextField
            fullWidth
            type="date"
            label="Date de réalisation"
            value={formData.date_realisation}
            onChange={(e) => setFormData(prev => ({ ...prev, date_realisation: e.target.value }))}
            sx={{ mt: 3 }}
            InputLabelProps={{ shrink: true }}
          />

          <TextField
            fullWidth
            multiline
            rows={3}
            label="Commentaire"
            value={formData.commentaire}
            onChange={(e) => setFormData(prev => ({ ...prev, commentaire: e.target.value }))}
            placeholder="Observations, remarques..."
            sx={{ mt: 2 }}
          />

          <Box sx={{ mt: 2 }}>
            <Button
              variant="outlined"
              component="label"
              startIcon={<CloudUpload />}
              fullWidth
            >
              {selectedFile ? selectedFile.name : 'Joindre un fichier (optionnel)'}
              <input
                type="file"
                hidden
                onChange={handleFileChange}
              />
            </Button>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => onClose(false)} disabled={loading}>
          Annuler
        </Button>
        <Button onClick={handleSubmit} variant="contained" color="success" disabled={loading}>
          {loading ? <CircularProgress size={24} /> : 'Valider'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default CompleteSurveillanceDialog;
