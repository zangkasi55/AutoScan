import { useTranslation } from 'react-i18next';
export function Reports()      { const { t } = useTranslation(); return <h1 className="text-2xl font-bold">{t('nav.reports')}</h1>; }
