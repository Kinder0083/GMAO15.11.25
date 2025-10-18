import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "./components/ui/toaster";

// Layout
import MainLayout from "./components/Layout/MainLayout";

// Pages
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import WorkOrders from "./pages/WorkOrders";
import Assets from "./pages/Assets";
import EquipmentDetail from "./pages/EquipmentDetail";
import Inventory from "./pages/Inventory";
import Locations from "./pages/Locations";
import PreventiveMaintenance from "./pages/PreventiveMaintenance";
import Reports from "./pages/Reports";
import People from "./pages/People";
import Planning from "./pages/Planning";
import Vendors from "./pages/Vendors";
import Settings from "./pages/Settings";

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="work-orders" element={<WorkOrders />} />
            <Route path="assets" element={<Assets />} />
            <Route path="assets/:id" element={<EquipmentDetail />} />
            <Route path="inventory" element={<Inventory />} />
            <Route path="locations" element={<Locations />} />
            <Route path="preventive-maintenance" element={<PreventiveMaintenance />} />
            <Route path="reports" element={<Reports />} />
            <Route path="people" element={<People />} />
            <Route path="planning" element={<Planning />} />
            <Route path="vendors" element={<Vendors />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;
