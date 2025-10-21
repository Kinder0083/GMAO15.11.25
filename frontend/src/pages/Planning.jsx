import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Calendar, ChevronLeft, ChevronRight, UserCheck, UserX, Users } from 'lucide-react';
import { usersAPI } from '../services/api';
import axios from 'axios';
import { useToast } from '../hooks/use-toast';
import { useAutoRefresh } from '../hooks/useAutoRefresh';

const Planning = () => {
  const { toast } = useToast();
  const [users, setUsers] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [availabilities, setAvailabilities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
    loadAvailabilities();
    
    // Rafraîchissement automatique toutes les 5 secondes
    const interval = setInterval(() => {
      loadUsers();
      loadAvailabilities();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [currentDate]);

  const loadUsers = async () => {
    try {
      const response = await usersAPI.getAll();
      // Filtrer le compte de secours du planning
      const filteredUsers = response.data.filter(u => u.email !== 'buenogy@gmail.com');
      setUsers(filteredUsers);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les utilisateurs',
        variant: 'destructive'
      });
    }
  };

  const loadAvailabilities = async () => {
    try {
      setLoading(true);
      const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
      const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
      
      const backend_url = process.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');
      
      const response = await axios.get(`${backend_url}/api/availabilities`, {
        params: {
          start_date: startOfMonth.toISOString(),
          end_date: endOfMonth.toISOString()
        },
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setAvailabilities(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des disponibilités:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleAvailability = async (userId, date) => {
    try {
      const dateStr = date.toISOString().split('T')[0];
      const existing = availabilities.find(
        a => a.user_id === userId && a.date.split('T')[0] === dateStr
      );

      const backend_url = process.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');

      if (existing) {
        await axios.put(
          `${backend_url}/api/availabilities/${existing.id}`,
          { disponible: !existing.disponible },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      } else {
        await axios.post(
          `${backend_url}/api/availabilities`,
          {
            user_id: userId,
            date: date.toISOString(),
            disponible: false
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }

      loadAvailabilities();
      toast({
        title: 'Succès',
        description: 'Disponibilité mise à jour'
      });
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de mettre à jour la disponibilité',
        variant: 'destructive'
      });
    }
  };

  const isAvailable = (userId, date) => {
    const dateStr = date.toISOString().split('T')[0];
    const avail = availabilities.find(
      a => a.user_id === userId && a.date.split('T')[0] === dateStr
    );
    return avail ? avail.disponible : true;
  };

  const getDaysInMonth = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days = [];

    for (let d = 1; d <= lastDay.getDate(); d++) {
      days.push(new Date(year, month, d));
    }

    return days;
  };

  const goToPreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const monthNames = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
  ];

  const days = getDaysInMonth();
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Planning du Personnel</h1>
          <p className="text-gray-600 mt-1">Gérez la disponibilité de votre équipe</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={goToToday}>
          <Calendar size={20} className="mr-2" />
          Aujourd'hui
        </Button>
      </div>

      {/* Month Navigation */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-6">
            <Button variant="outline" onClick={goToPreviousMonth}>
              <ChevronLeft size={20} />
            </Button>
            <h2 className="text-2xl font-bold text-gray-900">
              {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
            </h2>
            <Button variant="outline" onClick={goToNextMonth}>
              <ChevronRight size={20} />
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Personnel total</p>
                  <p className="text-2xl font-bold text-blue-700">{users.length}</p>
                </div>
                <Users size={32} className="text-blue-600" />
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Disponibles aujourd'hui</p>
                  <p className="text-2xl font-bold text-green-700">
                    {users.filter(u => isAvailable(u.id, new Date())).length}
                  </p>
                </div>
                <UserCheck size={32} className="text-green-600" />
              </div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Indisponibles aujourd'hui</p>
                  <p className="text-2xl font-bold text-red-700">
                    {users.filter(u => !isAvailable(u.id, new Date())).length}
                  </p>
                </div>
                <UserX size={32} className="text-red-600" />
              </div>
            </div>
          </div>

          {/* Calendar Grid */}
          {loading ? (
            <div className="text-center py-8">
              <p className="text-gray-500">Chargement...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="border p-2 bg-gray-100 sticky left-0 z-10 min-w-[150px]">
                      Personnel
                    </th>
                    {days.map((day, index) => {
                      const isToday = day.toISOString().split('T')[0] === today;
                      const isWeekend = day.getDay() === 0 || day.getDay() === 6;
                      return (
                        <th
                          key={index}
                          className={`border p-2 text-center min-w-[50px] ${
                            isToday ? 'bg-blue-100' : isWeekend ? 'bg-gray-50' : 'bg-white'
                          }`}
                        >
                          <div className="text-xs text-gray-500">
                            {['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'][day.getDay()]}
                          </div>
                          <div className="font-semibold">{day.getDate()}</div>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.id}>
                      <td className="border p-2 bg-gray-50 sticky left-0 z-10">
                        <div className="font-medium text-sm">{user.prenom} {user.nom}</div>
                        {user.service && (
                          <div className="text-xs text-gray-600">{user.service}</div>
                        )}
                      </td>
                      {days.map((day, index) => {
                        const available = isAvailable(user.id, day);
                        const isToday = day.toISOString().split('T')[0] === today;
                        const isWeekend = day.getDay() === 0 || day.getDay() === 6;
                        return (
                          <td
                            key={index}
                            className={`border p-1 text-center cursor-pointer hover:bg-gray-100 ${
                              isToday ? 'bg-blue-50' : isWeekend ? 'bg-gray-50' : 'bg-white'
                            }`}
                            onClick={() => toggleAvailability(user.id, day)}
                          >
                            {available ? (
                              <UserCheck size={20} className="text-green-600 mx-auto" />
                            ) : (
                              <UserX size={20} className="text-red-600 mx-auto" />
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="mt-4 text-sm text-gray-600 flex items-center gap-4">
            <div className="flex items-center gap-2">
              <UserCheck size={16} className="text-green-600" />
              <span>Disponible</span>
            </div>
            <div className="flex items-center gap-2">
              <UserX size={16} className="text-red-600" />
              <span>Indisponible</span>
            </div>
            <span className="text-gray-500">• Cliquez pour changer la disponibilité</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Planning;
