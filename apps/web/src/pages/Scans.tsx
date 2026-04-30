import { useTranslation } from 'react-i18next';
export function Scans()        { const { t } = useTranslation(); return <h1 className="text-2xl font-bold">{t('scan.title')}</h1>; }
