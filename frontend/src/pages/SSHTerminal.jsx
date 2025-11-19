import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Terminal, AlertTriangle } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

function SSHTerminal() {
  const { toast } = useToast();
  const [connected, setConnected] = useState(false);
  const [output, setOutput] = useState([]);
  const [command, setCommand] = useState('');
  const terminalRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom when new output
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output]);

  const addOutput = (text, type = 'output') => {
    setOutput(prev => [...prev, { text, type, timestamp: new Date() }]);
  };

  const handleConnect = () => {
    addOutput('🔌 Connexion au terminal SSH...', 'info');
    addOutput('✅ Connecté au container', 'success');
    addOutput('💡 Utilisez les commandes Linux standard', 'info');
    addOutput('⚠️  Soyez prudent avec les commandes système', 'warning');
    setConnected(true);
  };

  const handleDisconnect = () => {
    addOutput('🔌 Déconnexion...', 'info');
    setConnected(false);
    toast({ title: 'Déconnecté', description: 'Session SSH fermée' });
  };

  const executeCommand = async () => {
    if (!command.trim()) return;

    addOutput(`$ ${command}`, 'command');
    setCommand('');

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || window.location.origin}/api/ssh/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ command })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'exécution');
      }

      const data = await response.json();
      
      if (data.stdout) {
        addOutput(data.stdout, 'output');
      }
      if (data.stderr) {
        addOutput(data.stderr, 'error');
      }
    } catch (error) {
      addOutput(`❌ Erreur: ${error.message}`, 'error');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      executeCommand();
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Terminal className="h-8 w-8" />
            Terminal SSH
          </h1>
          <p className="text-gray-500">Console d'administration du container</p>
        </div>
        <div className="flex gap-2">
          {!connected ? (
            <Button onClick={handleConnect}>
              Connecter
            </Button>
          ) : (
            <Button variant="destructive" onClick={handleDisconnect}>
              Déconnecter
            </Button>
          )}
        </div>
      </div>

      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          <strong>ATTENTION :</strong> Cette interface donne un accès direct au système.
          Utilisez les commandes avec précaution. Un usage inapproprié peut endommager l'application.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Terminal</span>
            {connected && (
              <span className="text-sm font-normal text-green-600 flex items-center gap-2">
                <span className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></span>
                Connecté
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            ref={terminalRef}
            className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm h-96 overflow-y-auto"
          >
            {output.length === 0 ? (
              <div className="text-gray-500">
                Terminal prêt. Cliquez sur "Connecter" pour démarrer une session SSH.
              </div>
            ) : (
              output.map((line, index) => (
                <div
                  key={index}
                  className={`mb-1 ${
                    line.type === 'command'
                      ? 'text-white font-bold'
                      : line.type === 'error'
                      ? 'text-red-400'
                      : line.type === 'success'
                      ? 'text-green-400'
                      : line.type === 'warning'
                      ? 'text-yellow-400'
                      : line.type === 'info'
                      ? 'text-blue-400'
                      : 'text-green-400'
                  }`}
                >
                  {line.text}
                </div>
              ))
            )}
          </div>

          {connected && (
            <div className="mt-4 flex gap-2">
              <input
                type="text"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Entrez une commande Linux..."
                className="flex-1 px-4 py-2 bg-gray-900 text-green-400 border border-gray-700 rounded-lg font-mono focus:outline-none focus:border-green-500"
              />
              <Button onClick={executeCommand} disabled={!command.trim()}>
                Exécuter
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default SSHTerminal;
