export const site = {
  consumerBrand: process.env.NEXT_PUBLIC_CONSUMER_BRAND || "BalkonCheck",
  platformBrand: process.env.NEXT_PUBLIC_PLATFORM_BRAND || "SolarLead",
  operatorName: process.env.NEXT_PUBLIC_OPERATOR_NAME || "",
  operatorLegalForm: process.env.NEXT_PUBLIC_OPERATOR_LEGAL_FORM || "",
  addressLine1: process.env.NEXT_PUBLIC_OPERATOR_ADDRESS_LINE1 || "",
  addressLine2: process.env.NEXT_PUBLIC_OPERATOR_ADDRESS_LINE2 || "",
  postalCity: process.env.NEXT_PUBLIC_OPERATOR_POSTAL_CITY || "",
  country: process.env.NEXT_PUBLIC_OPERATOR_COUNTRY || "Deutschland",
  email: process.env.NEXT_PUBLIC_OPERATOR_EMAIL || "",
  phone: process.env.NEXT_PUBLIC_OPERATOR_PHONE || "",
  registerCourt: process.env.NEXT_PUBLIC_OPERATOR_REGISTER_COURT || "",
  registerNumber: process.env.NEXT_PUBLIC_OPERATOR_REGISTER_NUMBER || "",
  vatId: process.env.NEXT_PUBLIC_OPERATOR_VAT_ID || "",
  privacyEmail: process.env.NEXT_PUBLIC_PRIVACY_EMAIL || process.env.NEXT_PUBLIC_OPERATOR_EMAIL || "",
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
  hostingProvider: process.env.NEXT_PUBLIC_HOSTING_PROVIDER || "",
  hostingCountry: process.env.NEXT_PUBLIC_HOSTING_COUNTRY || "",
  cloudflareEnabled: (process.env.NEXT_PUBLIC_CLOUDFLARE_ENABLED || "false") === "true",
};

export const operatorDisplay = () => {
  const n = [site.operatorName, site.operatorLegalForm].filter(Boolean).join(" ");
  return n || "Betreiber dieser Website";
};

export const publicConfigComplete = () => Boolean(
  site.operatorName && site.addressLine1 && site.postalCity && site.email
);
