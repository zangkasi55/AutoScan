import { useTranslation } from 'react-i18next';
export function Findings()     { const { t } = useTranslation(); return <h1 className="text-2xl font-bold">{t('nav.findings')}</h1>; }
