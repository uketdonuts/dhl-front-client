/**
 * Categorías de productos DHL según documentación oficial de la API
 * Estas categorías se pueden obtener también via referenceData API / commodityCategory dataset
 */

export const DHL_CATEGORIES = [
  // Ropa y Vestimenta (100s)
  { code: '101', name: 'Coats & Jacket' },
  { code: '102', name: 'Blazers' },
  { code: '103', name: 'Suits' },
  { code: '104', name: 'Ensembles' },
  { code: '105', name: 'Trousers' },
  { code: '106', name: 'Shirts & Blouses' },
  { code: '107', name: 'Dresses' },
  { code: '108', name: 'Skirts' },
  { code: '109', name: 'Jerseys, Sweatshirts & Pullovers' },
  { code: '110', name: 'Sports & Swimwear' },
  { code: '111', name: 'Night & Underwear' },
  { code: '112', name: 'T-Shirts' },
  { code: '113', name: 'Tights & Leggings' },
  { code: '114', name: 'Socks' },
  { code: '115', name: 'Baby Clothes' },
  { code: '116', name: 'Clothing Accessories' },

  // Calzado (200s)
  { code: '201', name: 'Sneakers' },
  { code: '202', name: 'Athletic Footwear' },
  { code: '203', name: 'Leather Footwear' },
  { code: '204', name: 'Textile & Other Footwear' },

  // Anteojos y Lentes (300s)
  { code: '301', name: 'Spectacle Lenses' },
  { code: '302', name: 'Sunglasses' },
  { code: '303', name: 'Eyewear Frames' },
  { code: '304', name: 'Contact Lenses' },

  // Accesorios (400s)
  { code: '401', name: 'Watches' },
  { code: '402', name: 'Jewelry' },
  { code: '403', name: 'Suitcases & Briefcases' },
  { code: '404', name: 'Handbags' },
  { code: '405', name: 'Wallets & Little Cases' },
  { code: '406', name: 'Bags & Containers' },

  // Bebidas Alcohólicas (500s)
  { code: '501', name: 'Beer' },
  { code: '502', name: 'Spirits' },
  { code: '503', name: 'Wine' },
  { code: '504', name: 'Cider, Perry & Rice Wine' },

  // Bebidas No Alcohólicas (600s)
  { code: '601', name: 'Bottled Water' },
  { code: '602', name: 'Soft Drinks' },
  { code: '603', name: 'Juices' },
  { code: '604', name: 'Coffee' },
  { code: '605', name: 'Tea' },
  { code: '606', name: 'Cocoa' },

  // Alimentos (700s)
  { code: '701', name: 'Dairy Products & Eggs' },
  { code: '702', name: 'Meat' },
  { code: '703', name: 'Fish & Seafood' },
  { code: '704', name: 'Fruits & Nuts' },
  { code: '705', name: 'Vegetables' },
  { code: '706', name: 'Bread & Cereal Products' },
  { code: '707', name: 'Oils & Fats' },
  { code: '708', name: 'Sauces & Spices' },
  { code: '709', name: 'Convenience Food' },
  { code: '710', name: 'Spreads & Sweeteners' },
  { code: '711', name: 'Baby Food' },
  { code: '712', name: 'Pet Food' },

  // Tabaco (800s)
  { code: '801', name: 'Cigarettes' },
  { code: '802', name: 'Smoking Tobacco' },
  { code: '803', name: 'Cigars' },
  { code: '804', name: 'E-Cigarettes' },

  // Productos de Limpieza (900s)
  { code: '901', name: 'Household Cleaners' },
  { code: '902', name: 'Dishwashing Detergents' },
  { code: '903', name: 'Polishes' },
  { code: '904', name: 'Room Scents' },
  { code: '905', name: 'Insecticides' },

  // Cosméticos y Cuidado Personal (1000s)
  { code: '1001', name: 'Cosmetics' },
  { code: '1002', name: 'Skin Care' },
  { code: '1003', name: 'Personal Care' },
  { code: '1004', name: 'Fragrances' },

  // Productos de Papel (1100s)
  { code: '1101', name: 'Toilet Paper' },
  { code: '1102', name: 'Paper Tissues' },
  { code: '1103', name: 'Household Paper' },
  { code: '1104', name: 'Feminine Hygiene' },
  { code: '1105', name: 'Baby Diapers' },
  { code: '1106', name: 'Incontinence' },

  // Electrónicos (1200s)
  { code: '1202', name: 'TV, Radio & Multimedia' },
  { code: '1203', name: 'TV Peripheral Devices' },
  { code: '1204', name: 'Telephony' },
  { code: '1205', name: 'Computing' },
  { code: '1206', name: 'Drones' },

  // Electrodomésticos (1300s)
  { code: '1301', name: 'Refrigerators' },
  { code: '1302', name: 'Freezers' },
  { code: '1303', name: 'Dishwashing Machines' },
  { code: '1304', name: 'Washing Machines' },
  { code: '1305', name: 'Cookers & Oven' },
  { code: '1306', name: 'Vacuum Cleaners' },
  { code: '1307', name: 'Small Kitchen Appliances' },
  { code: '1308', name: 'Hair Clippers' },
  { code: '1309', name: 'Irons' },
  { code: '1310', name: 'Toasters' },
  { code: '1311', name: 'Grills & Roasters' },
  { code: '1312', name: 'Hair Dryers' },
  { code: '1313', name: 'Coffee Machines' },
  { code: '1314', name: 'Microwave Ovens' },
  { code: '1315', name: 'Electric Kettles' },

  // Muebles (1400s)
  { code: '1401', name: 'Seats & Sofas' },
  { code: '1402', name: 'Beds' },
  { code: '1403', name: 'Mattresses' },
  { code: '1404', name: 'Closets, Nightstands & Dressers' },
  { code: '1405', name: 'Lamps & Lighting' },
  { code: '1406', name: 'Floor Covering' },
  { code: '1407', name: 'Kitchen Furniture' },
  { code: '1408', name: 'Plastic & Other Furniture' },

  // Medicamentos (1500s)
  { code: '1501', name: 'Analgesics' },
  { code: '1502', name: 'Cold & Cough Remedies' },
  { code: '1503', name: 'Digestives & Intestinal Remedies' },
  { code: '1504', name: 'Skin Treatment' },
  { code: '1505', name: 'Vitamins & Minerals' },
  { code: '1506', name: 'Hand Sanitizer' },

  // Juguetes y Deportes (1600s)
  { code: '1601', name: 'Toys & Games' },
  { code: '1602', name: 'Musical Instruments' },
  { code: '1603', name: 'Sports Equipment' }
];

/**
 * Obtiene una categoría por código
 * @param {string} code - Código de la categoría
 * @returns {object|null} - Categoría encontrada o null
 */
export const getCategoryByCode = (code) => {
  return DHL_CATEGORIES.find(cat => cat.code === code) || null;
};

/**
 * Busca categorías por nombre (búsqueda parcial)
 * @param {string} searchTerm - Término de búsqueda
 * @returns {array} - Array de categorías que coinciden
 */
export const searchCategories = (searchTerm) => {
  if (!searchTerm) return DHL_CATEGORIES;
  
  const term = searchTerm.toLowerCase();
  return DHL_CATEGORIES.filter(cat => 
    cat.name.toLowerCase().includes(term) || 
    cat.code.includes(term)
  );
};

export default DHL_CATEGORIES;
