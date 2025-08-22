/**
 * Servicio para mapeo de países - maneja conversiones entre nombres y códigos ISO
 */

// Mapeo completo de países con múltiples variaciones de nombres
const COUNTRY_MAPPING = {
  // Códigos ISO de 2 letras como clave principal
  'AD': { code: 'AD', name: 'Andorra', names: ['Andorra'] },
  'AE': { code: 'AE', name: 'United Arab Emirates', names: ['United Arab Emirates', 'UAE', 'Emiratos Árabes Unidos'] },
  'AF': { code: 'AF', name: 'Afghanistan', names: ['Afghanistan', 'Afganistán'] },
  'AG': { code: 'AG', name: 'Antigua and Barbuda', names: ['Antigua and Barbuda', 'Antigua y Barbuda'] },
  'AI': { code: 'AI', name: 'Anguilla', names: ['Anguilla'] },
  'AL': { code: 'AL', name: 'Albania', names: ['Albania'] },
  'AM': { code: 'AM', name: 'Armenia', names: ['Armenia'] },
  'AO': { code: 'AO', name: 'Angola', names: ['Angola'] },
  'AQ': { code: 'AQ', name: 'Antarctica', names: ['Antarctica', 'Antártida'] },
  'AR': { code: 'AR', name: 'Argentina', names: ['Argentina'] },
  'AS': { code: 'AS', name: 'American Samoa', names: ['American Samoa', 'Samoa Americana'] },
  'AT': { code: 'AT', name: 'Austria', names: ['Austria'] },
  'AU': { code: 'AU', name: 'Australia', names: ['Australia'] },
  'AW': { code: 'AW', name: 'Aruba', names: ['Aruba'] },
  'AX': { code: 'AX', name: 'Åland Islands', names: ['Åland Islands', 'Islas Åland'] },
  'AZ': { code: 'AZ', name: 'Azerbaijan', names: ['Azerbaijan', 'Azerbaiyán'] },
  'BA': { code: 'BA', name: 'Bosnia and Herzegovina', names: ['Bosnia and Herzegovina', 'Bosnia y Herzegovina'] },
  'BB': { code: 'BB', name: 'Barbados', names: ['Barbados'] },
  'BD': { code: 'BD', name: 'Bangladesh', names: ['Bangladesh'] },
  'BE': { code: 'BE', name: 'Belgium', names: ['Belgium', 'Bélgica'] },
  'BF': { code: 'BF', name: 'Burkina Faso', names: ['Burkina Faso'] },
  'BG': { code: 'BG', name: 'Bulgaria', names: ['Bulgaria'] },
  'BH': { code: 'BH', name: 'Bahrain', names: ['Bahrain', 'Baréin'] },
  'BI': { code: 'BI', name: 'Burundi', names: ['Burundi'] },
  'BJ': { code: 'BJ', name: 'Benin', names: ['Benin'] },
  'BL': { code: 'BL', name: 'Saint Barthélemy', names: ['Saint Barthélemy', 'San Bartolomé'] },
  'BM': { code: 'BM', name: 'Bermuda', names: ['Bermuda'] },
  'BN': { code: 'BN', name: 'Brunei', names: ['Brunei'] },
  'BO': { code: 'BO', name: 'Bolivia', names: ['Bolivia'] },
  'BQ': { code: 'BQ', name: 'Caribbean Netherlands', names: ['Caribbean Netherlands', 'Países Bajos del Caribe'] },
  'BR': { code: 'BR', name: 'Brazil', names: ['Brazil', 'Brasil'] },
  'BS': { code: 'BS', name: 'Bahamas', names: ['Bahamas'] },
  'BT': { code: 'BT', name: 'Bhutan', names: ['Bhutan', 'Bután'] },
  'BV': { code: 'BV', name: 'Bouvet Island', names: ['Bouvet Island', 'Isla Bouvet'] },
  'BW': { code: 'BW', name: 'Botswana', names: ['Botswana'] },
  'BY': { code: 'BY', name: 'Belarus', names: ['Belarus', 'Bielorrusia'] },
  'BZ': { code: 'BZ', name: 'Belize', names: ['Belize'] },
  'CA': { code: 'CA', name: 'Canada', names: ['Canada', 'Canadá'] },
  'CC': { code: 'CC', name: 'Cocos Islands', names: ['Cocos Islands', 'Islas Cocos'] },
  'CD': { code: 'CD', name: 'Congo (DRC)', names: ['Congo (DRC)', 'República Democrática del Congo'] },
  'CF': { code: 'CF', name: 'Central African Republic', names: ['Central African Republic', 'República Centroafricana'] },
  'CG': { code: 'CG', name: 'Congo', names: ['Congo'] },
  'CH': { code: 'CH', name: 'Switzerland', names: ['Switzerland', 'Suiza'] },
  'CI': { code: 'CI', name: 'Côte d\'Ivoire', names: ['Côte d\'Ivoire', 'Costa de Marfil'] },
  'CK': { code: 'CK', name: 'Cook Islands', names: ['Cook Islands', 'Islas Cook'] },
  'CL': { code: 'CL', name: 'Chile', names: ['Chile'] },
  'CM': { code: 'CM', name: 'Cameroon', names: ['Cameroon', 'Camerún'] },
  'CN': { code: 'CN', name: 'China', names: ['China'] },
  'CO': { code: 'CO', name: 'Colombia', names: ['Colombia'] },
  'CR': { code: 'CR', name: 'Costa Rica', names: ['Costa Rica'] },
  'CU': { code: 'CU', name: 'Cuba', names: ['Cuba'] },
  'CV': { code: 'CV', name: 'Cape Verde', names: ['Cape Verde', 'Cabo Verde'] },
  'CW': { code: 'CW', name: 'Curaçao', names: ['Curaçao'] },
  'CX': { code: 'CX', name: 'Christmas Island', names: ['Christmas Island', 'Isla Christmas'] },
  'CY': { code: 'CY', name: 'Cyprus', names: ['Cyprus', 'Chipre'] },
  'CZ': { code: 'CZ', name: 'Czech Republic', names: ['Czech Republic', 'República Checa'] },
  'DE': { code: 'DE', name: 'Germany', names: ['Germany', 'Alemania'] },
  'DJ': { code: 'DJ', name: 'Djibouti', names: ['Djibouti', 'Yibuti'] },
  'DK': { code: 'DK', name: 'Denmark', names: ['Denmark', 'Dinamarca'] },
  'DM': { code: 'DM', name: 'Dominica', names: ['Dominica'] },
  'DO': { code: 'DO', name: 'Dominican Republic', names: ['Dominican Republic', 'República Dominicana'] },
  'DZ': { code: 'DZ', name: 'Algeria', names: ['Algeria', 'Argelia'] },
  'EC': { code: 'EC', name: 'Ecuador', names: ['Ecuador'] },
  'EE': { code: 'EE', name: 'Estonia', names: ['Estonia'] },
  'EG': { code: 'EG', name: 'Egypt', names: ['Egypt', 'Egipto'] },
  'EH': { code: 'EH', name: 'Western Sahara', names: ['Western Sahara', 'Sahara Occidental'] },
  'ER': { code: 'ER', name: 'Eritrea', names: ['Eritrea'] },
  'ES': { code: 'ES', name: 'Spain', names: ['Spain', 'España'] },
  'ET': { code: 'ET', name: 'Ethiopia', names: ['Ethiopia', 'Etiopía'] },
  'FI': { code: 'FI', name: 'Finland', names: ['Finland', 'Finlandia'] },
  'FJ': { code: 'FJ', name: 'Fiji', names: ['Fiji'] },
  'FK': { code: 'FK', name: 'Falkland Islands', names: ['Falkland Islands', 'Islas Malvinas'] },
  'FM': { code: 'FM', name: 'Micronesia', names: ['Micronesia'] },
  'FO': { code: 'FO', name: 'Faroe Islands', names: ['Faroe Islands', 'Islas Feroe'] },
  'FR': { code: 'FR', name: 'France', names: ['France', 'Francia'] },
  'GA': { code: 'GA', name: 'Gabon', names: ['Gabon', 'Gabón'] },
  'GB': { code: 'GB', name: 'United Kingdom', names: ['United Kingdom', 'Reino Unido', 'UK'] },
  'GD': { code: 'GD', name: 'Grenada', names: ['Grenada', 'Granada'] },
  'GE': { code: 'GE', name: 'Georgia', names: ['Georgia'] },
  'GF': { code: 'GF', name: 'French Guiana', names: ['French Guiana', 'Guayana Francesa'] },
  'GG': { code: 'GG', name: 'Guernsey', names: ['Guernsey'] },
  'GH': { code: 'GH', name: 'Ghana', names: ['Ghana'] },
  'GI': { code: 'GI', name: 'Gibraltar', names: ['Gibraltar'] },
  'GL': { code: 'GL', name: 'Greenland', names: ['Greenland', 'Groenlandia'] },
  'GM': { code: 'GM', name: 'Gambia', names: ['Gambia'] },
  'GN': { code: 'GN', name: 'Guinea', names: ['Guinea'] },
  'GP': { code: 'GP', name: 'Guadeloupe', names: ['Guadeloupe'] },
  'GQ': { code: 'GQ', name: 'Equatorial Guinea', names: ['Equatorial Guinea', 'Guinea Ecuatorial'] },
  'GR': { code: 'GR', name: 'Greece', names: ['Greece', 'Grecia'] },
  'GS': { code: 'GS', name: 'South Georgia', names: ['South Georgia', 'Georgia del Sur'] },
  'GT': { code: 'GT', name: 'Guatemala', names: ['Guatemala'] },
  'GU': { code: 'GU', name: 'Guam', names: ['Guam'] },
  'GW': { code: 'GW', name: 'Guinea-Bissau', names: ['Guinea-Bissau'] },
  'GY': { code: 'GY', name: 'Guyana', names: ['Guyana'] },
  'HK': { code: 'HK', name: 'Hong Kong', names: ['Hong Kong'] },
  'HM': { code: 'HM', name: 'Heard Island', names: ['Heard Island', 'Isla Heard'] },
  'HN': { code: 'HN', name: 'Honduras', names: ['Honduras'] },
  'HR': { code: 'HR', name: 'Croatia', names: ['Croatia', 'Croacia'] },
  'HT': { code: 'HT', name: 'Haiti', names: ['Haiti', 'Haití'] },
  'HU': { code: 'HU', name: 'Hungary', names: ['Hungary', 'Hungría'] },
  'ID': { code: 'ID', name: 'Indonesia', names: ['Indonesia'] },
  'IE': { code: 'IE', name: 'Ireland', names: ['Ireland', 'Irlanda'] },
  'IL': { code: 'IL', name: 'Israel', names: ['Israel'] },
  'IM': { code: 'IM', name: 'Isle of Man', names: ['Isle of Man', 'Isla de Man'] },
  'IN': { code: 'IN', name: 'India', names: ['India'] },
  'IO': { code: 'IO', name: 'British Indian Ocean Territory', names: ['British Indian Ocean Territory', 'Territorio Británico del Océano Índico'] },
  'IQ': { code: 'IQ', name: 'Iraq', names: ['Iraq', 'Irak'] },
  'IR': { code: 'IR', name: 'Iran', names: ['Iran', 'Irán'] },
  'IS': { code: 'IS', name: 'Iceland', names: ['Iceland', 'Islandia'] },
  'IT': { code: 'IT', name: 'Italy', names: ['Italy', 'Italia'] },
  'JE': { code: 'JE', name: 'Jersey', names: ['Jersey'] },
  'JM': { code: 'JM', name: 'Jamaica', names: ['Jamaica'] },
  'JO': { code: 'JO', name: 'Jordan', names: ['Jordan', 'Jordania'] },
  'JP': { code: 'JP', name: 'Japan', names: ['Japan', 'Japón'] },
  'KE': { code: 'KE', name: 'Kenya', names: ['Kenya'] },
  'KG': { code: 'KG', name: 'Kyrgyzstan', names: ['Kyrgyzstan', 'Kirguistán'] },
  'KH': { code: 'KH', name: 'Cambodia', names: ['Cambodia', 'Camboya'] },
  'KI': { code: 'KI', name: 'Kiribati', names: ['Kiribati'] },
  'KM': { code: 'KM', name: 'Comoros', names: ['Comoros', 'Comoras'] },
  'KN': { code: 'KN', name: 'Saint Kitts and Nevis', names: ['Saint Kitts and Nevis', 'San Cristóbal y Nieves'] },
  'KP': { code: 'KP', name: 'North Korea', names: ['North Korea', 'Corea del Norte'] },
  'KR': { code: 'KR', name: 'South Korea', names: ['South Korea', 'Corea del Sur'] },
  'KW': { code: 'KW', name: 'Kuwait', names: ['Kuwait'] },
  'KY': { code: 'KY', name: 'Cayman Islands', names: ['Cayman Islands', 'Islas Caimán'] },
  'KZ': { code: 'KZ', name: 'Kazakhstan', names: ['Kazakhstan', 'Kazajistán'] },
  'LA': { code: 'LA', name: 'Laos', names: ['Laos'] },
  'LB': { code: 'LB', name: 'Lebanon', names: ['Lebanon', 'Líbano'] },
  'LC': { code: 'LC', name: 'Saint Lucia', names: ['Saint Lucia', 'Santa Lucía'] },
  'LI': { code: 'LI', name: 'Liechtenstein', names: ['Liechtenstein'] },
  'LK': { code: 'LK', name: 'Sri Lanka', names: ['Sri Lanka'] },
  'LR': { code: 'LR', name: 'Liberia', names: ['Liberia'] },
  'LS': { code: 'LS', name: 'Lesotho', names: ['Lesotho'] },
  'LT': { code: 'LT', name: 'Lithuania', names: ['Lithuania', 'Lituania'] },
  'LU': { code: 'LU', name: 'Luxembourg', names: ['Luxembourg', 'Luxemburgo'] },
  'LV': { code: 'LV', name: 'Latvia', names: ['Latvia', 'Letonia'] },
  'LY': { code: 'LY', name: 'Libya', names: ['Libya', 'Libia'] },
  'MA': { code: 'MA', name: 'Morocco', names: ['Morocco', 'Marruecos'] },
  'MC': { code: 'MC', name: 'Monaco', names: ['Monaco', 'Mónaco'] },
  'MD': { code: 'MD', name: 'Moldova', names: ['Moldova'] },
  'ME': { code: 'ME', name: 'Montenegro', names: ['Montenegro'] },
  'MF': { code: 'MF', name: 'Saint Martin', names: ['Saint Martin', 'San Martín'] },
  'MG': { code: 'MG', name: 'Madagascar', names: ['Madagascar'] },
  'MH': { code: 'MH', name: 'Marshall Islands', names: ['Marshall Islands', 'Islas Marshall'] },
  'MK': { code: 'MK', name: 'North Macedonia', names: ['North Macedonia', 'Macedonia del Norte'] },
  'ML': { code: 'ML', name: 'Mali', names: ['Mali', 'Malí'] },
  'MM': { code: 'MM', name: 'Myanmar', names: ['Myanmar'] },
  'MN': { code: 'MN', name: 'Mongolia', names: ['Mongolia'] },
  'MO': { code: 'MO', name: 'Macau', names: ['Macau', 'Macao'] },
  'MP': { code: 'MP', name: 'Northern Mariana Islands', names: ['Northern Mariana Islands', 'Islas Marianas del Norte'] },
  'MQ': { code: 'MQ', name: 'Martinique', names: ['Martinique'] },
  'MR': { code: 'MR', name: 'Mauritania', names: ['Mauritania'] },
  'MS': { code: 'MS', name: 'Montserrat', names: ['Montserrat'] },
  'MT': { code: 'MT', name: 'Malta', names: ['Malta'] },
  'MU': { code: 'MU', name: 'Mauritius', names: ['Mauritius', 'Mauricio'] },
  'MV': { code: 'MV', name: 'Maldives', names: ['Maldives', 'Maldivas'] },
  'MW': { code: 'MW', name: 'Malawi', names: ['Malawi'] },
  'MX': { code: 'MX', name: 'Mexico', names: ['Mexico', 'México'] },
  'MY': { code: 'MY', name: 'Malaysia', names: ['Malaysia', 'Malasia'] },
  'MZ': { code: 'MZ', name: 'Mozambique', names: ['Mozambique'] },
  'NA': { code: 'NA', name: 'Namibia', names: ['Namibia'] },
  'NC': { code: 'NC', name: 'New Caledonia', names: ['New Caledonia', 'Nueva Caledonia'] },
  'NE': { code: 'NE', name: 'Niger', names: ['Niger', 'Níger'] },
  'NF': { code: 'NF', name: 'Norfolk Island', names: ['Norfolk Island', 'Isla Norfolk'] },
  'NG': { code: 'NG', name: 'Nigeria', names: ['Nigeria'] },
  'NI': { code: 'NI', name: 'Nicaragua', names: ['Nicaragua'] },
  'NL': { code: 'NL', name: 'Netherlands', names: ['Netherlands', 'Países Bajos', 'Holanda'] },
  'NO': { code: 'NO', name: 'Norway', names: ['Norway', 'Noruega'] },
  'NP': { code: 'NP', name: 'Nepal', names: ['Nepal'] },
  'NR': { code: 'NR', name: 'Nauru', names: ['Nauru'] },
  'NU': { code: 'NU', name: 'Niue', names: ['Niue'] },
  'NZ': { code: 'NZ', name: 'New Zealand', names: ['New Zealand', 'Nueva Zelanda'] },
  'OM': { code: 'OM', name: 'Oman', names: ['Oman', 'Omán'] },
  'PA': { code: 'PA', name: 'Panama', names: ['Panama', 'Panamá'] },
  'PE': { code: 'PE', name: 'Peru', names: ['Peru', 'Perú'] },
  'PF': { code: 'PF', name: 'French Polynesia', names: ['French Polynesia', 'Polinesia Francesa'] },
  'PG': { code: 'PG', name: 'Papua New Guinea', names: ['Papua New Guinea', 'Papúa Nueva Guinea'] },
  'PH': { code: 'PH', name: 'Philippines', names: ['Philippines', 'Filipinas'] },
  'PK': { code: 'PK', name: 'Pakistan', names: ['Pakistan', 'Pakistán'] },
  'PL': { code: 'PL', name: 'Poland', names: ['Poland', 'Polonia'] },
  'PM': { code: 'PM', name: 'Saint Pierre and Miquelon', names: ['Saint Pierre and Miquelon', 'San Pedro y Miquelón'] },
  'PN': { code: 'PN', name: 'Pitcairn', names: ['Pitcairn'] },
  'PR': { code: 'PR', name: 'Puerto Rico', names: ['Puerto Rico'] },
  'PS': { code: 'PS', name: 'Palestine', names: ['Palestine', 'Palestina'] },
  'PT': { code: 'PT', name: 'Portugal', names: ['Portugal'] },
  'PW': { code: 'PW', name: 'Palau', names: ['Palau'] },
  'PY': { code: 'PY', name: 'Paraguay', names: ['Paraguay'] },
  'QA': { code: 'QA', name: 'Qatar', names: ['Qatar'] },
  'RE': { code: 'RE', name: 'Réunion', names: ['Réunion'] },
  'RO': { code: 'RO', name: 'Romania', names: ['Romania', 'Rumania'] },
  'RS': { code: 'RS', name: 'Serbia', names: ['Serbia'] },
  'RU': { code: 'RU', name: 'Russia', names: ['Russia', 'Rusia'] },
  'RW': { code: 'RW', name: 'Rwanda', names: ['Rwanda'] },
  'SA': { code: 'SA', name: 'Saudi Arabia', names: ['Saudi Arabia', 'Arabia Saudí'] },
  'SB': { code: 'SB', name: 'Solomon Islands', names: ['Solomon Islands', 'Islas Salomón'] },
  'SC': { code: 'SC', name: 'Seychelles', names: ['Seychelles'] },
  'SD': { code: 'SD', name: 'Sudan', names: ['Sudan', 'Sudán'] },
  'SE': { code: 'SE', name: 'Sweden', names: ['Sweden', 'Suecia'] },
  'SG': { code: 'SG', name: 'Singapore', names: ['Singapore', 'Singapur'] },
  'SH': { code: 'SH', name: 'Saint Helena', names: ['Saint Helena', 'Santa Elena'] },
  'SI': { code: 'SI', name: 'Slovenia', names: ['Slovenia', 'Eslovenia'] },
  'SJ': { code: 'SJ', name: 'Svalbard and Jan Mayen', names: ['Svalbard and Jan Mayen'] },
  'SK': { code: 'SK', name: 'Slovakia', names: ['Slovakia', 'Eslovaquia'] },
  'SL': { code: 'SL', name: 'Sierra Leone', names: ['Sierra Leone'] },
  'SM': { code: 'SM', name: 'San Marino', names: ['San Marino'] },
  'SN': { code: 'SN', name: 'Senegal', names: ['Senegal'] },
  'SO': { code: 'SO', name: 'Somalia', names: ['Somalia'] },
  'SR': { code: 'SR', name: 'Suriname', names: ['Suriname'] },
  'SS': { code: 'SS', name: 'South Sudan', names: ['South Sudan', 'Sudán del Sur'] },
  'ST': { code: 'ST', name: 'São Tomé and Príncipe', names: ['São Tomé and Príncipe', 'Santo Tomé y Príncipe'] },
  'SV': { code: 'SV', name: 'El Salvador', names: ['El Salvador'] },
  'SX': { code: 'SX', name: 'Sint Maarten', names: ['Sint Maarten'] },
  'SY': { code: 'SY', name: 'Syria', names: ['Syria', 'Siria'] },
  'SZ': { code: 'SZ', name: 'Eswatini', names: ['Eswatini', 'Suazilandia'] },
  'TC': { code: 'TC', name: 'Turks and Caicos Islands', names: ['Turks and Caicos Islands', 'Islas Turcas y Caicos'] },
  'TD': { code: 'TD', name: 'Chad', names: ['Chad'] },
  'TF': { code: 'TF', name: 'French Southern Territories', names: ['French Southern Territories', 'Territorios Australes Franceses'] },
  'TG': { code: 'TG', name: 'Togo', names: ['Togo'] },
  'TH': { code: 'TH', name: 'Thailand', names: ['Thailand', 'Tailandia'] },
  'TJ': { code: 'TJ', name: 'Tajikistan', names: ['Tajikistan', 'Tayikistán'] },
  'TK': { code: 'TK', name: 'Tokelau', names: ['Tokelau'] },
  'TL': { code: 'TL', name: 'Timor-Leste', names: ['Timor-Leste'] },
  'TM': { code: 'TM', name: 'Turkmenistan', names: ['Turkmenistan', 'Turkmenistán'] },
  'TN': { code: 'TN', name: 'Tunisia', names: ['Tunisia', 'Túnez'] },
  'TO': { code: 'TO', name: 'Tonga', names: ['Tonga'] },
  'TR': { code: 'TR', name: 'Turkey', names: ['Turkey', 'Turquía'] },
  'TT': { code: 'TT', name: 'Trinidad and Tobago', names: ['Trinidad and Tobago', 'Trinidad y Tobago'] },
  'TV': { code: 'TV', name: 'Tuvalu', names: ['Tuvalu'] },
  'TW': { code: 'TW', name: 'Taiwan', names: ['Taiwan', 'Taiwán'] },
  'TZ': { code: 'TZ', name: 'Tanzania', names: ['Tanzania'] },
  'UA': { code: 'UA', name: 'Ukraine', names: ['Ukraine', 'Ucrania'] },
  'UG': { code: 'UG', name: 'Uganda', names: ['Uganda'] },
  'UM': { code: 'UM', name: 'United States Minor Outlying Islands', names: ['United States Minor Outlying Islands', 'Islas Ultramarinas de Estados Unidos'] },
  'US': { code: 'US', name: 'United States', names: ['United States', 'Estados Unidos', 'USA', 'US'] },
  'UY': { code: 'UY', name: 'Uruguay', names: ['Uruguay'] },
  'UZ': { code: 'UZ', name: 'Uzbekistan', names: ['Uzbekistan', 'Uzbekistán'] },
  'VA': { code: 'VA', name: 'Vatican City', names: ['Vatican City', 'Ciudad del Vaticano'] },
  'VC': { code: 'VC', name: 'Saint Vincent and the Grenadines', names: ['Saint Vincent and the Grenadines', 'San Vicente y las Granadinas'] },
  'VE': { code: 'VE', name: 'Venezuela', names: ['Venezuela'] },
  'VG': { code: 'VG', name: 'British Virgin Islands', names: ['British Virgin Islands', 'Islas Vírgenes Británicas'] },
  'VI': { code: 'VI', name: 'United States Virgin Islands', names: ['United States Virgin Islands', 'Islas Vírgenes de los Estados Unidos'] },
  'VN': { code: 'VN', name: 'Vietnam', names: ['Vietnam'] },
  'VU': { code: 'VU', name: 'Vanuatu', names: ['Vanuatu'] },
  'WF': { code: 'WF', name: 'Wallis and Futuna', names: ['Wallis and Futuna'] },
  'WS': { code: 'WS', name: 'Samoa', names: ['Samoa'] },
  'YE': { code: 'YE', name: 'Yemen', names: ['Yemen'] },
  'YT': { code: 'YT', name: 'Mayotte', names: ['Mayotte'] },
  'ZA': { code: 'ZA', name: 'South Africa', names: ['South Africa', 'Sudáfrica'] },
  'ZM': { code: 'ZM', name: 'Zambia', names: ['Zambia'] },
  'ZW': { code: 'ZW', name: 'Zimbabwe', names: ['Zimbabwe'] }
};

// Crear un índice inverso para búsqueda rápida por nombre
const NAME_TO_CODE_INDEX = {};
Object.values(COUNTRY_MAPPING).forEach(country => {
  country.names.forEach(name => {
    NAME_TO_CODE_INDEX[name.toLowerCase()] = country.code;
  });
});

/**
 * Convierte un nombre de país a código ISO de 2 letras
 * @param {string} countryName - Nombre del país en cualquier idioma soportado
 * @returns {string|null} - Código ISO de 2 letras o null si no se encuentra
 */
export function mapCountryNameToCode(countryName) {
  if (!countryName || typeof countryName !== 'string') {
    return null;
  }

  // Limpiar el nombre de entrada
  const cleanName = countryName.trim();
  
  // Si ya es un código de 2 letras, validar y devolver
  if (cleanName.length === 2) {
    const upperCode = cleanName.toUpperCase();
    return COUNTRY_MAPPING[upperCode] ? upperCode : null;
  }

  // Buscar por nombre (case-insensitive)
  const lowerName = cleanName.toLowerCase();
  return NAME_TO_CODE_INDEX[lowerName] || null;
}

/**
 * Convierte un código ISO a nombre de país
 * @param {string} countryCode - Código ISO de 2 letras
 * @param {string} language - 'en' para inglés, 'es' para español (por defecto inglés)
 * @returns {string|null} - Nombre del país o null si no se encuentra
 */
export function mapCodeToCountryName(countryCode, language = 'en') {
  if (!countryCode || typeof countryCode !== 'string') {
    return null;
  }

  const upperCode = countryCode.toUpperCase();
  const country = COUNTRY_MAPPING[upperCode];
  
  if (!country) {
    return null;
  }

  // Por simplicidad, devolvemos el primer nombre (que suele ser el más común)
  return country.name;
}

/**
 * Obtiene todos los nombres alternativos de un país
 * @param {string} countryCode - Código ISO de 2 letras
 * @returns {Array|null} - Array de nombres alternativos o null si no se encuentra
 */
export function getCountryAlternativeNames(countryCode) {
  if (!countryCode || typeof countryCode !== 'string') {
    return null;
  }

  const upperCode = countryCode.toUpperCase();
  const country = COUNTRY_MAPPING[upperCode];
  
  return country ? country.names : null;
}

/**
 * Valida si un código de país es válido
 * @param {string} countryCode - Código ISO de 2 letras
 * @returns {boolean} - true si es válido, false en caso contrario
 */
export function isValidCountryCode(countryCode) {
  if (!countryCode || typeof countryCode !== 'string') {
    return false;
  }

  const upperCode = countryCode.toUpperCase();
  return !!COUNTRY_MAPPING[upperCode];
}

/**
 * Busca países por nombre parcial (útil para autocompletado)
 * @param {string} partialName - Nombre parcial del país
 * @param {number} limit - Límite de resultados (por defecto 10)
 * @returns {Array} - Array de países que coinciden
 */
export function searchCountriesByPartialName(partialName, limit = 10) {
  if (!partialName || typeof partialName !== 'string') {
    return [];
  }

  const searchTerm = partialName.toLowerCase();
  const matches = [];

  Object.values(COUNTRY_MAPPING).forEach(country => {
    const hasMatch = country.names.some(name => 
      name.toLowerCase().includes(searchTerm)
    );
    
    if (hasMatch) {
      matches.push({
        code: country.code,
        name: country.name,
        alternativeNames: country.names
      });
    }
  });

  return matches.slice(0, limit);
}

export default {
  mapCountryNameToCode,
  mapCodeToCountryName,
  getCountryAlternativeNames,
  isValidCountryCode,
  searchCountriesByPartialName
};
