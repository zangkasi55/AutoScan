import { useTranslation } from 'react-i18next';
export function Scopes()       { const { t } = useTranslation(); return <h1 className="text-2xl font-bold">{t('scope.title')}</h1>; }
