import { Routes, Route, NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, LayoutDashboard, FileSignature, Activity, Bug, FileText, Settings } from 'lucide-react';
import { Dashboard } from './pages/Dashboard';
import { Scopes } from './pages/Scopes';
import { Scans } from './pages/Scans';
import { Findings } from './pages/Findings';
import { Reports } from './pages/Reports';
import { SettingsPage } from './pages/Settings';
import i18n from './i18n';

export function App() {
  const { t } = useTranslation();
  const toggleLang = () => {
    const next = i18n.language === 'th' ? 'en' : 'th';
    i18n.changeLanguage(next);
    localStorage.setItem('avs.lang', next);
  };
  return (
    <div className="grid h-full grid-cols-[240px_1fr]">
      <aside className="bg-avs-ink text-white p-4 flex flex-col gap-1">
        <div className="flex items-center gap-2 mb-6 text-lg font-bold">
          <Shield className="text-avs-pulse" />
          <span>{t('common.appName')}</span>
        </div>
        <NavItem to="/" icon={<LayoutDashboard size={18} />} label={t('nav.dashboard')} />
        <NavItem to="/scopes" icon={<FileSignature size={18} />} label={t('nav.scopes')} />
        <NavItem to="/scans" icon={<Activity size={18} />} label={t('nav.scans')} />
        <NavItem to="/findings" icon={<Bug size={18} />} label={t('nav.findings')} />
        <NavItem to="/reports" icon={<FileText size={18} />} label={t('nav.reports')} />
        <NavItem to="/settings" icon={<Settings size={18} />} label={t('nav.settings')} />
        <div className="mt-auto pt-4 border-t border-white/10 text-xs text-white/60">
          <button className="hover:text-white" onClick={toggleLang}>
            {i18n.language === 'th' ? 'EN' : 'ไทย'}
          </button>
          <p className="mt-2">{t('common.tagline')}</p>
        </div>
      </aside>
      <main className="overflow-auto p-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scopes" element={<Scopes />} />
          <Route path="/scans" element={<Scans />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}

function NavItem({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <NavLink to={to} end
      className={({ isActive }) =>
        `flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
          isActive ? 'bg-avs-shield text-white' : 'text-white/80 hover:bg-white/5'
        }`
      }
    >{icon}{label}</NavLink>
  );
}
