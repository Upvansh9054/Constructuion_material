import React, { useState, useEffect } from 'react';
import { PageLayout } from './components/layout/PageLayout';
import { NavScreenId } from './components/layout/Sidebar';
import {
  DEV_PROJECTS,
  DEV_MATERIALS,
  DEV_LISTINGS,
  DEV_NOTIFICATIONS,
} from './mock/fixtures';
import { DemolitionSite } from './types/site';
import { MaterialItem, ValuationSummary } from './types/material';
import { MarketplaceListing } from './types/marketplace';

// Import All 15 Screens
import { LandingPage } from './screens/1_LandingPage';
import { AuthScreen } from './screens/2_AuthScreen';
import { DashboardScreen } from './screens/3_DashboardScreen';
import { ProjectManagementScreen } from './screens/4_ProjectManagementScreen';
import { CreateProjectScreen } from './screens/5_CreateProjectScreen';
import { SiteUploadScreen } from './screens/6_SiteUploadScreen';
import { AiAnalysisScreen } from './screens/7_AiAnalysisScreen';
import { MaterialInventoryScreen } from './screens/8_MaterialInventoryScreen';
import { QuantityConditionScreen } from './screens/9_QuantityConditionScreen';
import { RecoveryValueScreen } from './screens/10_RecoveryValueScreen';
import { MarketplaceScreen } from './screens/11_MarketplaceScreen';
import { BuyerRecyclerScreen } from './screens/12_BuyerRecyclerScreen';
import { RecoveryReportsScreen } from './screens/13_RecoveryReportsScreen';
import { NotificationsScreen } from './screens/14_NotificationsScreen';
import { SettingsScreen } from './screens/15_SettingsScreen';

export const App: React.FC = () => {
  // Navigation & Authentication State
  const [activeScreen, setActiveScreen] = useState<NavScreenId>('dashboard');
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [user, setUser] = useState({
    email: 'contractor@apexdemo.com',
    role: 'CONTRACTOR',
    name: 'Marcus Vance',
  });

  // Domain State (Initialized with Development Fixtures)
  const [projects, setProjects] = useState<DemolitionSite[]>(DEV_PROJECTS);
  const [materials, setMaterials] = useState<MaterialItem[]>(DEV_MATERIALS);
  const [listings, setListings] = useState<MarketplaceListing[]>(DEV_LISTINGS);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('prj-101');
  const [selectedMaterialId, setSelectedMaterialId] = useState<string>('mat-001');

  // Sync hash routing for deep-linking
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '') as NavScreenId;
      const validScreens: NavScreenId[] = [
        'landing',
        'auth',
        'dashboard',
        'projects',
        'create-project',
        'upload',
        'analysis',
        'inventory',
        'assessment',
        'recovery',
        'marketplace',
        'buyers',
        'reports',
        'notifications',
        'settings',
      ];
      if (validScreens.includes(hash)) {
        setActiveScreen(hash);
      }
    };

    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigateTo = (screen: string, contextId?: string) => {
    if (contextId) {
      if (contextId.startsWith('prj-')) setSelectedProjectId(contextId);
      if (contextId.startsWith('mat-')) setSelectedMaterialId(contextId);
    }
    setActiveScreen(screen as NavScreenId);
    window.location.hash = `#${screen}`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Dynamically compute valuation summary
  const calculateDynamicSummary = (): ValuationSummary => {
    const catMap: Record<string, any> = {};
    for (const m of materials) {
      if (!catMap[m.category]) {
        catMap[m.category] = {
          category: m.category,
          total_volume_m3: 0,
          total_weight_tonnes: 0,
          estimated_value_usd: 0,
          carbon_offset_kg_co2e: 0,
          item_count: 0,
        };
      }
      catMap[m.category].total_volume_m3 += m.estimated_volume_m3;
      catMap[m.category].total_weight_tonnes += m.estimated_weight_tonnes;
      catMap[m.category].estimated_value_usd += m.estimated_market_value_usd;
      catMap[m.category].carbon_offset_kg_co2e += m.embodied_carbon_offset_kg;
      catMap[m.category].item_count += 1;
    }

    const categories = Object.values(catMap);
    return {
      total_estimated_value_usd: categories.reduce((sum, c) => sum + c.estimated_value_usd, 0),
      total_recoverable_tonnes: Math.round(categories.reduce((sum, c) => sum + c.total_weight_tonnes, 0) * 10) / 10,
      total_carbon_offset_kg_co2e: Math.round(categories.reduce((sum, c) => sum + c.carbon_offset_kg_co2e, 0) * 10) / 10,
      categories,
    };
  };

  const summary = calculateDynamicSummary();
  const unreadCount = DEV_NOTIFICATIONS.filter((n) => !n.is_read).length;

  // Handlers for state updates
  const handleProjectCreated = (newProject: DemolitionSite) => {
    setProjects((prev) => [newProject, ...prev]);
    setSelectedProjectId(newProject.id);
    navigateTo('upload', newProject.id);
  };

  const handleUpdateMaterial = (updatedItem: MaterialItem) => {
    setMaterials((prev) => prev.map((m) => (m.id === updatedItem.id ? updatedItem : m)));
  };

  const handleCreateListing = (newListing: MarketplaceListing) => {
    setListings((prev) => [newListing, ...prev]);
  };

  // Standalone Fullscreen Views (Landing Page and Auth Screen)
  if (activeScreen === 'landing') {
    return (
      <LandingPage
        onEnterApp={() => navigateTo('dashboard')}
        onGoToAuth={(mode) => {
          setAuthMode(mode || 'login');
          navigateTo('auth');
        }}
        onNavigateToScreen={navigateTo}
      />
    );
  }

  if (activeScreen === 'auth') {
    return (
      <AuthScreen
        initialMode={authMode}
        onLoginSuccess={(userData) => {
          setUser(userData);
          navigateTo('dashboard');
        }}
        onBackToLanding={() => navigateTo('landing')}
      />
    );
  }

  // Enterprise Application Shell for Screens 3 through 15
  return (
    <PageLayout
      activeScreen={activeScreen}
      onSelectScreen={navigateTo}
      unreadCount={unreadCount}
      user={user}
      onLogout={() => navigateTo('landing')}
    >
      {/* 3. Main Dashboard */}
      {activeScreen === 'dashboard' && (
        <DashboardScreen
          projects={projects}
          summary={summary}
          onNavigateToScreen={navigateTo}
        />
      )}

      {/* 4. Demolition Project Management */}
      {activeScreen === 'projects' && (
        <ProjectManagementScreen
          projects={projects}
          onNavigateToScreen={navigateTo}
        />
      )}

      {/* 5. Create New Demolition Project */}
      {activeScreen === 'create-project' && (
        <CreateProjectScreen
          onProjectCreated={handleProjectCreated}
          onCancel={() => navigateTo('projects')}
        />
      )}

      {/* 6. Site Image and Video Upload */}
      {activeScreen === 'upload' && (
        <SiteUploadScreen
          projectId={selectedProjectId}
          onUploadComplete={() => navigateTo('analysis')}
          onCancel={() => navigateTo('projects')}
        />
      )}

      {/* 7. AI Material Analysis */}
      {activeScreen === 'analysis' && (
        <AiAnalysisScreen
          onProceedToInventory={() => navigateTo('inventory')}
          onNavigateToScreen={navigateTo}
        />
      )}

      {/* 8. Material Inventory */}
      {activeScreen === 'inventory' && (
        <MaterialInventoryScreen
          materials={materials}
          onUpdateMaterial={handleUpdateMaterial}
          onNavigateToScreen={navigateTo}
        />
      )}

      {/* 9. Quantity and Condition Assessment */}
      {activeScreen === 'assessment' && (
        <QuantityConditionScreen
          materials={materials}
          selectedMaterialId={selectedMaterialId}
          onSaveAssessment={handleUpdateMaterial}
          onCancel={() => navigateTo('inventory')}
        />
      )}

      {/* 10. Recovery Value Analysis */}
      {activeScreen === 'recovery' && (
        <RecoveryValueScreen
          summary={summary}
          onNavigateToScreen={navigateTo}
        />
      )}

      {/* 11. Material Marketplace */}
      {activeScreen === 'marketplace' && (
        <MarketplaceScreen
          listings={listings}
          materials={materials}
          onCreateListing={handleCreateListing}
          onNavigateToScreen={navigateTo}
        />
      )}

      {/* 12. Buyer and Recycler Management */}
      {activeScreen === 'buyers' && (
        <BuyerRecyclerScreen
          onNavigateToScreen={navigateTo}
        />
      )}

      {/* 13. Recovery Reports */}
      {activeScreen === 'reports' && (
        <RecoveryReportsScreen
          onNavigateToScreen={navigateTo}
        />
      )}

      {/* 14. Notifications */}
      {activeScreen === 'notifications' && (
        <NotificationsScreen
          onNavigateToScreen={navigateTo}
        />
      )}

      {/* 15. User Profile and Settings */}
      {activeScreen === 'settings' && (
        <SettingsScreen
          user={user}
          onUpdateUser={setUser}
        />
      )}
    </PageLayout>
  );
};
