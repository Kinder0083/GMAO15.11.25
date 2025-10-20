import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Plus, Search, Building, Mail, Phone, MapPin, Pencil, Trash2, LayoutGrid, List } from 'lucide-react';
import VendorFormDialog from '../components/Vendors/VendorFormDialog';
import { vendorsAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';

const Vendors = () => {
  const { toast } = useToast();
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' ou 'list'
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [selectedVendor, setSelectedVendor] = useState(null);

  useEffect(() => {
    loadVendors();
  }, []);

  const loadVendors = async () => {
    try {
      setLoading(true);
      const response = await vendorsAPI.getAll();
      setVendors(response.data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les fournisseurs',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce fournisseur ?')) {
      try {
        await vendorsAPI.delete(id);
        toast({
          title: 'Succès',
          description: 'Fournisseur supprimé'
        });
        loadVendors();
      } catch (error) {
        toast({
          title: 'Erreur',
          description: 'Impossible de supprimer le fournisseur',
          variant: 'destructive'
        });
      }
    }
  };

  const filteredVendors = vendors.filter(vendor => {
    return vendor.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
           vendor.contact.toLowerCase().includes(searchTerm.toLowerCase()) ||
           vendor.specialite.toLowerCase().includes(searchTerm.toLowerCase());
  });

  // Calculer les fournisseurs créés ce mois
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const createdThisMonth = vendors.filter(v => {
    const createdDate = new Date(v.dateCreation);
    return createdDate >= startOfMonth;
  }).length;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Fournisseurs</h1>
          <p className="text-gray-600 mt-1">Gérez vos fournisseurs et sous-traitants</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={() => {
          setSelectedVendor(null);
          setFormDialogOpen(true);
        }}>
          <Plus size={20} className="mr-2" />
          Nouveau fournisseur
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center">
              <p className="text-sm font-medium text-gray-600">Total fournisseurs</p>
              <p className="text-4xl font-bold text-blue-600 mt-2">{vendors.length}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center">
              <p className="text-sm font-medium text-gray-600">Créés ce mois</p>
              <p className="text-4xl font-bold text-green-600 mt-2">{createdThisMonth}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <Input
              placeholder="Rechercher par nom, contact ou spécialité..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Vendors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-8">
            <p className="text-gray-500">Chargement...</p>
          </div>
        ) : filteredVendors.length === 0 ? (
          <div className="col-span-full text-center py-8">
            <p className="text-gray-500">Aucun fournisseur trouvé</p>
          </div>
        ) : (
          filteredVendors.map((vendor) => (
            <Card key={vendor.id} className="hover:shadow-xl transition-all duration-300">
              <CardHeader>
                <div className="flex items-start gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center shadow-md">
                    <Building size={24} className="text-white" />
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-lg">{vendor.nom}</CardTitle>
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium mt-1 inline-block">
                      {vendor.specialite}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Contact Person */}
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Contact principal</p>
                    <p className="font-medium text-gray-900">{vendor.contact}</p>
                  </div>

                  {/* Email */}
                  <div className="flex items-center gap-2 text-sm text-gray-700">
                    <Mail size={16} className="text-gray-500" />
                    <a href={`mailto:${vendor.email}`} className="hover:text-blue-600 truncate">
                      {vendor.email}
                    </a>
                  </div>

                  {/* Phone */}
                  <div className="flex items-center gap-2 text-sm text-gray-700">
                    <Phone size={16} className="text-gray-500" />
                    <a href={`tel:${vendor.telephone}`} className="hover:text-blue-600">
                      {vendor.telephone}
                    </a>
                  </div>

                  {/* Address */}
                  <div className="flex items-start gap-2 text-sm text-gray-700">
                    <MapPin size={16} className="text-gray-500 mt-0.5" />
                    <span className="flex-1">{vendor.adresse}</span>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-3 border-t">
                    <Button 
                      variant="outline" 
                      className="flex-1 hover:bg-green-50 hover:text-green-600"
                      onClick={() => {
                        setSelectedVendor(vendor);
                        setFormDialogOpen(true);
                      }}
                    >
                      <Pencil size={16} className="mr-1" />
                      Modifier
                    </Button>
                    <Button 
                      variant="outline" 
                      className="hover:bg-red-50 hover:text-red-600"
                      onClick={() => handleDelete(vendor.id)}
                    >
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <VendorFormDialog
        open={formDialogOpen}
        onOpenChange={setFormDialogOpen}
        vendor={selectedVendor}
        onSuccess={loadVendors}
      />
    </div>
  );
};

export default Vendors;