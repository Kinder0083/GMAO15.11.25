import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { autorisationsAPI, documentationsAPI } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Save, Trash2, Plus, FileText, X } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const AutorisationParticuliereForm = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const { toast } = useToast();

  const [loading, setLoading] = useState(false);
  const [bonsTravail, setBonsTravail] = useState([]);
  const [selectedBonId, setSelectedBonId] = useState('');
  const [formData, setFormData] = useState({
    service_demandeur: '',
    responsable: '',
    personnel_autorise: [
      { nom: '', fonction: '' },
      { nom: '', fonction: '' },
      { nom: '', fonction: '' },
      { nom: '', fonction: '' }
    ],
    description_travaux: '',
    horaire_debut: '',
    horaire_fin: '',
    lieu_travaux: '',
    risques_potentiels: '',
    mesures_securite: '',
    equipements_protection: '',
    signature_demandeur: '',
    date_signature_demandeur: '',
    signature_responsable_securite: '',
    date_signature_responsable: '',
    bons_travail_ids: []
  });

  useEffect(() => {
    loadBonsTravail();
    if (isEdit) {
      loadAutorisation();
    }
  }, [id]);

  const loadBonsTravail = async () => {
    try {
      const data = await documentationsAPI.getBonsTravail();
      setBonsTravail(data);
    } catch (error) {
      console.error('Erreur chargement bons de travail:', error);
    }
  };

  const loadAutorisation = async () => {
    try {
      const data = await autorisationsAPI.getById(id);
      // Assurer que personnel_autorise a toujours 4 entrées
      const personnel = data.personnel_autorise || [];
      while (personnel.length < 4) {
        personnel.push({ nom: '', fonction: '' });
      }
      setFormData({
        ...data,
        personnel_autorise: personnel,
        bons_travail_ids: data.bons_travail_ids || []
      });
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Erreur lors du chargement de l\'autorisation',
        variant: 'destructive'
      });
      console.error(error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handlePersonnelChange = (index, field, value) => {
    const newPersonnel = [...formData.personnel_autorise];
    newPersonnel[index] = { ...newPersonnel[index], [field]: value };
    setFormData(prev => ({ ...prev, personnel_autorise: newPersonnel }));
  };

  const handleAddBonTravail = () => {
    if (selectedBonId && !formData.bons_travail_ids.includes(selectedBonId)) {
      setFormData(prev => ({
        ...prev,
        bons_travail_ids: [...prev.bons_travail_ids, selectedBonId]
      }));
      setSelectedBonId('');
    }
  };

  const handleRemoveBonTravail = (bonId) => {
    setFormData(prev => ({
      ...prev,
      bons_travail_ids: prev.bons_travail_ids.filter(id => id !== bonId)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Nettoyer les entrées personnel vides
      const cleanedData = {
        ...formData,
        personnel_autorise: formData.personnel_autorise.filter(
          p => p.nom.trim() !== '' || p.fonction.trim() !== ''
        )
      };

      if (isEdit) {
        await autorisationsAPI.update(id, cleanedData);
        toast({
          title: 'Succès',
          description: 'Autorisation mise à jour avec succès'
        });
      } else {
        await autorisationsAPI.create(cleanedData);
        toast({
          title: 'Succès',
          description: 'Autorisation créée avec succès'
        });
      }
      navigate('/autorisations-particulieres');
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Erreur lors de l\'enregistrement',
        variant: 'destructive'
      });
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette autorisation ?')) {
      return;
    }

    try {
      await autorisationsAPI.delete(id);
      toast({
        title: 'Succès',
        description: 'Autorisation supprimée'
      });
      navigate('/autorisations-particulieres');
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Erreur lors de la suppression',
        variant: 'destructive'
      });
      console.error(error);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/autorisations-particulieres')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-3xl font-bold">
            {isEdit ? 'Modifier l\'Autorisation Particulière' : 'Nouvelle Autorisation Particulière'}
          </h1>
        </div>
        {isEdit && (
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="h-4 w-4 mr-2" />
            Supprimer
          </Button>
        )}
      </div>

      {/* Formulaire */}
      <form onSubmit={handleSubmit}>
        <div className="space-y-6">
          {/* Informations principales */}
          <Card>
            <CardHeader>
              <CardTitle>Informations Principales</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="service_demandeur">Service Demandeur *</Label>
                  <Input
                    id="service_demandeur"
                    name="service_demandeur"
                    value={formData.service_demandeur}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="responsable">Responsable *</Label>
                  <Input
                    id="responsable"
                    name="responsable"
                    value={formData.responsable}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Bons de travail liés */}
          <Card>
            <CardHeader>
              <CardTitle>Bons de Travail Liés (optionnel)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {bonsTravail.length === 0 ? (
                <p className="text-sm text-gray-500">Aucun bon de travail disponible</p>
              ) : (
                <>
                  {/* Sélecteur */}
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <Select value={selectedBonId} onValueChange={setSelectedBonId}>
                        <SelectTrigger>
                          <SelectValue placeholder="Sélectionner un bon de travail" />
                        </SelectTrigger>
                        <SelectContent className="max-h-60">
                          {bonsTravail
                            .filter(bon => !formData.bons_travail_ids.includes(bon.id))
                            .map((bon) => (
                              <SelectItem key={bon.id} value={bon.id}>
                                N° {bon.numero} - {bon.titre || 'Sans titre'}
                                {bon.equipement && ` • ${bon.equipement}`}
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <Button 
                      type="button" 
                      onClick={handleAddBonTravail} 
                      disabled={!selectedBonId}
                      variant="outline"
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Liste des bons sélectionnés */}
                  {formData.bons_travail_ids.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-semibold">Bons sélectionnés :</Label>
                      <div className="flex flex-wrap gap-2">
                        {formData.bons_travail_ids.map((bonId) => {
                          const bon = bonsTravail.find(b => b.id === bonId);
                          if (!bon) return null;
                          return (
                            <Badge key={bonId} variant="secondary" className="flex items-center gap-1 px-3 py-1">
                              <span className="text-sm">
                                N° {bon.numero} - {bon.titre || 'Sans titre'}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleRemoveBonTravail(bonId)}
                                className="ml-1 hover:bg-gray-300 rounded-full p-0.5"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </Badge>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          {/* Personnel autorisé */}
          <Card>
            <CardHeader>
              <CardTitle>Personnel Autorisé</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {formData.personnel_autorise.map((person, index) => (
                  <div key={index} className="grid grid-cols-12 gap-3 items-center">
                    <div className="col-span-1 text-center font-bold">{index + 1}</div>
                    <div className="col-span-6">
                      <Input
                        placeholder="Nom et Prénom"
                        value={person.nom}
                        onChange={(e) => handlePersonnelChange(index, 'nom', e.target.value)}
                      />
                    </div>
                    <div className="col-span-5">
                      <Input
                        placeholder="Fonction"
                        value={person.fonction}
                        onChange={(e) => handlePersonnelChange(index, 'fonction', e.target.value)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Description des travaux */}
          <Card>
            <CardHeader>
              <CardTitle>Description des Travaux *</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                name="description_travaux"
                value={formData.description_travaux}
                onChange={handleChange}
                rows={5}
                required
              />
            </CardContent>
          </Card>

          {/* Horaires et lieu */}
          <Card>
            <CardHeader>
              <CardTitle>Horaires et Lieu</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="horaire_debut">Horaire Début *</Label>
                  <Input
                    id="horaire_debut"
                    name="horaire_debut"
                    type="time"
                    value={formData.horaire_debut}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="horaire_fin">Horaire Fin *</Label>
                  <Input
                    id="horaire_fin"
                    name="horaire_fin"
                    type="time"
                    value={formData.horaire_fin}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="lieu_travaux">Lieu des Travaux *</Label>
                <Input
                  id="lieu_travaux"
                  name="lieu_travaux"
                  value={formData.lieu_travaux}
                  onChange={handleChange}
                  required
                />
              </div>
            </CardContent>
          </Card>

          {/* Risques potentiels */}
          <Card>
            <CardHeader>
              <CardTitle>Risques Potentiels *</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                name="risques_potentiels"
                value={formData.risques_potentiels}
                onChange={handleChange}
                rows={4}
                placeholder="Liste des risques potentiels (un par ligne)"
                required
              />
            </CardContent>
          </Card>

          {/* Mesures de sécurité */}
          <Card>
            <CardHeader>
              <CardTitle>Mesures de Sécurité *</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                name="mesures_securite"
                value={formData.mesures_securite}
                onChange={handleChange}
                rows={4}
                placeholder="Liste des mesures de sécurité (une par ligne)"
                required
              />
            </CardContent>
          </Card>

          {/* Équipements de protection */}
          <Card>
            <CardHeader>
              <CardTitle>Équipements de Protection Individuelle (EPI) *</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                name="equipements_protection"
                value={formData.equipements_protection}
                onChange={handleChange}
                rows={4}
                placeholder="Liste des EPI requis (un par ligne)"
                required
              />
            </CardContent>
          </Card>

          {/* Signatures */}
          <Card>
            <CardHeader>
              <CardTitle>Signatures</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-3">
                  <h3 className="font-semibold">Demandeur</h3>
                  <div>
                    <Label htmlFor="signature_demandeur">Nom</Label>
                    <Input
                      id="signature_demandeur"
                      name="signature_demandeur"
                      value={formData.signature_demandeur}
                      onChange={handleChange}
                    />
                  </div>
                  <div>
                    <Label htmlFor="date_signature_demandeur">Date de signature</Label>
                    <Input
                      id="date_signature_demandeur"
                      name="date_signature_demandeur"
                      type="date"
                      value={formData.date_signature_demandeur}
                      onChange={handleChange}
                    />
                  </div>
                </div>
                <div className="space-y-3">
                  <h3 className="font-semibold">Responsable Sécurité</h3>
                  <div>
                    <Label htmlFor="signature_responsable_securite">Nom</Label>
                    <Input
                      id="signature_responsable_securite"
                      name="signature_responsable_securite"
                      value={formData.signature_responsable_securite}
                      onChange={handleChange}
                    />
                  </div>
                  <div>
                    <Label htmlFor="date_signature_responsable">Date de signature</Label>
                    <Input
                      id="date_signature_responsable"
                      name="date_signature_responsable"
                      type="date"
                      value={formData.date_signature_responsable}
                      onChange={handleChange}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={() => navigate('/autorisations-particulieres')}>
              Annuler
            </Button>
            <Button type="submit" disabled={loading}>
              <Save className="h-4 w-4 mr-2" />
              {loading ? 'Enregistrement...' : 'Enregistrer'}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default AutorisationParticuliereForm;