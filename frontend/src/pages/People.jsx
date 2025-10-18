import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { mockUsers } from '../mock/mockData';
import { Plus, Search, Users as UsersIcon, Mail, Phone } from 'lucide-react';

const People = () => {
  const [users] = useState(mockUsers);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('ALL');

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.prenom.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = filterRole === 'ALL' || user.role === filterRole;
    return matchesSearch && matchesRole;
  });

  const getRoleBadge = (role) => {
    const badges = {
      'ADMIN': { bg: 'bg-purple-100', text: 'text-purple-700', label: 'Administrateur' },
      'TECHNICIEN': { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Technicien' },
      'VISUALISEUR': { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Visualiseur' }
    };
    const badge = badges[role] || badges['VISUALISEUR'];
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  const roles = [
    { value: 'ALL', label: 'Tous', count: users.length },
    { value: 'ADMIN', label: 'Administrateurs', count: users.filter(u => u.role === 'ADMIN').length },
    { value: 'TECHNICIEN', label: 'Techniciens', count: users.filter(u => u.role === 'TECHNICIEN').length },
    { value: 'VISUALISEUR', label: 'Visualiseurs', count: users.filter(u => u.role === 'VISUALISEUR').length }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Équipes</h1>
          <p className="text-gray-600 mt-1">Gérez les membres de votre équipe</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white">
          <Plus size={20} className="mr-2" />
          Inviter un membre
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {roles.map((role, index) => {
          const colors = ['blue', 'purple', 'green', 'gray'];
          const color = colors[index % colors.length];
          return (
            <Card key={role.value} className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setFilterRole(role.value)}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{role.label}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{role.count}</p>
                  </div>
                  <div className={`bg-${color}-100 p-3 rounded-xl`}>
                    <UsersIcon size={24} className={`text-${color}-600`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <Input
                  placeholder="Rechercher par nom ou email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              {roles.map(role => (
                <Button
                  key={role.value}
                  variant={filterRole === role.value ? 'default' : 'outline'}
                  onClick={() => setFilterRole(role.value)}
                  size="sm"
                  className={filterRole === role.value ? 'bg-blue-600 hover:bg-blue-700' : ''}
                >
                  {role.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredUsers.map((user) => (
          <Card key={user.id} className="hover:shadow-xl transition-all duration-300">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                {/* Avatar */}
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center mb-4 shadow-lg">
                  <span className="text-white text-2xl font-bold">
                    {user.prenom[0]}{user.nom[0]}
                  </span>
                </div>

                {/* Name */}
                <h3 className="text-xl font-bold text-gray-900 mb-1">
                  {user.prenom} {user.nom}
                </h3>

                {/* Role Badge */}
                <div className="mb-4">
                  {getRoleBadge(user.role)}
                </div>

                {/* Contact Info */}
                <div className="space-y-2 w-full">
                  <div className="flex items-center gap-2 text-sm text-gray-600 justify-center">
                    <Mail size={16} />
                    <span className="truncate">{user.email}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600 justify-center">
                    <Phone size={16} />
                    <span>{user.telephone}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-6 w-full">
                  <Button variant="outline" className="flex-1 hover:bg-blue-50 hover:text-blue-600">
                    Voir profil
                  </Button>
                  <Button variant="outline" className="flex-1 hover:bg-gray-100">
                    Contacter
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default People;