import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from '../../../packages/i18n/en.json';
import th from '../../../packages/i18n/th.json';

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, th: { translation: th } },
  fallbackLng: 'th',
  lng: localStorage.getItem('avs.lang') || 'th',
  interpolation: { escapeValue: false },
});

export default i18n;
