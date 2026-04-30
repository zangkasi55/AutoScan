import { useTranslation } from 'react-i18next';

export function Dashboard() {
  const { t } = useTranslation();
  const tiles = [
    { label: t('dashboard.criticalChains'), value: 0, accent: 'sev-critical' },
    { label: t('dashboard.openCriticals'),  value: 0, accent: 'sev-high' },
    { label: t('dashboard.kevListedOpen'),  value: 0, accent: 'sev-medium' },
    { label: t('dashboard.fpRate'),         value: '—', accent: 'avs-pulse' },
  ];
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">{t('dashboard.title')}</h1>
      <div className="grid grid-cols-4 gap-4 mb-8">
        {tiles.map((tile) => (
          <div key={tile.label} className="rounded-lg bg-white shadow p-4">
            <div className="text-sm text-gray-500">{tile.label}</div>
            <div className={`text-3xl font-extrabold mt-2 text-${tile.accent}`}>{tile.value}</div>
          </div>
        ))}
      </div>
      <section className="rounded-lg bg-white shadow p-6">
        <h2 className="font-semibold mb-2">{t('dashboard.topChains')}</h2>
        <p className="text-sm text-gray-500">No scans yet. Sign an RoE and start your first scan.</p>
      </section>
    </div>
  );
}
