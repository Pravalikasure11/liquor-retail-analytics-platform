import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "./store/authStore";
import Layout from "./components/layout/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import InventoryPage from "./pages/InventoryPage";
import SalesPage from "./pages/SalesPage";
import ExpensesPage from "./pages/ExpensesPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import SeasonalPage from "./pages/SeasonalPage";
import AlertsPage from "./pages/AlertsPage";
import DealsPage from "./pages/DealsPage";
import SuppliersPage from "./pages/SuppliersPage";
import PromotionsPage from "./pages/PromotionsPage";
import SettingsPage from "./pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } }
});

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster position="top-right" toastOptions={{
          style: { fontSize: 13, fontFamily: "system-ui" },
          success: { iconTheme: { primary: "#639922", secondary: "#fff" } },
          error:   { iconTheme: { primary: "#E24B4A", secondary: "#fff" } },
        }} />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard"   element={<DashboardPage />} />
            <Route path="inventory"   element={<InventoryPage />} />
            <Route path="sales"       element={<SalesPage />} />
            <Route path="expenses"    element={<ExpensesPage />} />
            <Route path="analytics"   element={<AnalyticsPage />} />
            <Route path="seasonal"    element={<SeasonalPage />} />
            <Route path="alerts"      element={<AlertsPage />} />
            <Route path="deals"       element={<DealsPage />} />
            <Route path="promotions"  element={<PromotionsPage />} />
            <Route path="suppliers"   element={<SuppliersPage />} />
            <Route path="settings"    element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
