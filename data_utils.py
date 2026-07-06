from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import re
import streamlit as st

FOCUS_ISO = "ECU"
V1_METRICS_FILE = "opportunity_metrics_hs4_ecu.csv"


HS_SECTION_RULES = [
    (1, range(1, 6), "1. Animales vivos y productos del reino animal"),
    (2, range(6, 15), "2. Productos del reino vegetal"),
    (3, range(15, 16), "3. Grasas y aceites animales o vegetales"),
    (4, range(16, 25), "4. Alimentos preparados; bebidas, licores y tabaco"),
    (5, range(25, 28), "5. Productos minerales"),
    (6, range(28, 39), "6. Productos de las industrias químicas o conexas"),
    (7, range(39, 41), "7. Plásticos y sus manufacturas; caucho y sus manufacturas"),
    (8, range(41, 44), "8. Pieles, cueros y sus manufacturas"),
    (9, range(44, 47), "9. Madera y sus manufacturas"),
    (10, range(47, 50), "10. Pasta de madera, papel y cartón"),
    (11, range(50, 64), "11. Textiles y sus manufacturas"),
    (12, range(64, 68), "12. Calzado, sombreros, paraguas y artículos afines"),
    (13, range(68, 71), "13. Manufacturas de piedra, yeso, cemento, cerámica y vidrio"),
    (14, range(71, 72), "14. Perlas, piedras preciosas y metales preciosos"),
    (15, range(72, 84), "15. Metales comunes y sus manufacturas"),
    (16, range(84, 86), "16. Máquinas, aparatos mecánicos y material eléctrico"),
    (17, range(86, 90), "17. Vehículos, aeronaves, buques y equipo de transporte"),
    (18, range(90, 93), "18. Instrumentos ópticos, fotográficos, médicos y musicales"),
    (19, range(93, 94), "19. Armas y municiones"),
    (20, range(94, 97), "20. Manufacturas diversas"),
    (21, range(97, 98), "21. Obras de arte, piezas de colección y antigüedades"),
]

SECTOR_LABELS_ES = {
    "Services": "Servicios",
    "Textiles": "Textiles",
    "Agriculture": "Agricultura",
    "Stone": "Piedra",
    "Minerals": "Minerales",
    "Metals": "Metales",
    "Chemicals": "Químicos",
    "Vehicles": "Vehículos",
    "Machinery": "Maquinaria",
    "Electronics": "Electrónica",
    "Other": "Otros",
}

HS4_LABEL_EXACT_ES = {
    "Horses": "Caballos",
    "Bovine": "Bovinos",
    "Swine": "Porcinos",
    "Sheep": "Ovinos",
    "Fowl": "Aves de corral",
    "Other live animals": "Otros animales vivos",
    "Beef": "Carne bovina",
    "Beef (frozen)": "Carne bovina (congelada)",
    "Pork": "Carne porcina",
    "Lamb": "Carne ovina",
    "Horse meat": "Carne de caballo",
    "Edible offal": "Despojos comestibles",
    "Poultry": "Aves de corral",
    "Other meat": "Otras carnes",
    "Pig and poultry fat": "Grasa de cerdo y de aves",
    "Preserved meat": "Carne conservada",
    "Live Fish": "Peces vivos",
    "Fish, excluding fillets": "Pescado, excluidos los filetes",
    "Frozen fish, excluding fillets": "Pescado congelado, excluidos los filetes",
    "Fish fillets": "Filetes de pescado",
    "Preserved fish": "Pescado conservado",
    "Crustaceans": "Crustáceos",
    "Molluscs": "Moluscos",
    "Milk": "Leche",
    "Milk, concentrated": "Leche concentrada",
    "Fermented milk products": "Productos lácteos fermentados",
    "Whey": "Suero de leche",
    "Butter": "Mantequilla",
    "Cheese": "Queso",
    "Eggs, in shell": "Huevos con cáscara",
    "Egg yolks": "Yemas de huevo",
    "Honey": "Miel",
    "Coffee": "Café",
    "Coffee extracts": "Extractos de café",
    "Salt": "Sal",
    "Copper ore": "Mineral de cobre",
    "Petroleum oils, crude": "Aceites de petróleo, crudos",
    "Petroleum oils, refined": "Aceites de petróleo, refinados",
    "Petroleum gases": "Gases de petróleo",
    "Electrical energy": "Energía eléctrica",
    "Gold": "Oro",
    "Medicaments, packaged": "Medicamentos, envasados",
    "Polymers of ethylene": "Polímeros de etileno",
    "Wooden tools": "Herramientas de madera",
    "T-shirts, knit": "Camisetas de punto",
    "Pig iron": "Arrabio",
    "Copper mattes": "Matas de cobre",
    "Unwrought aluminum": "Aluminio en bruto",
    "Electric motors and generators": "Motores y generadores eléctricos",
    "Cars": "Automóviles",
    "Medical instruments": "Instrumentos médicos",
}

HS4_CODE_OVERRIDE_ES = {
    "0503": "Crin",
    "0814": "Cáscaras de cítricos o melones",
    "1001": "Trigo y morcajo",
    "1101": "Harina de trigo o morcajo",
    "1102": "Harinas de cereales",
    "1103": "Sémolas y harinas gruesas de cereales",
    "1104": "Granos de cereales trabajados",
    "1109": "Gluten de trigo",
    "1212": "Algas y demás productos vegetales comestibles",
    "1213": "Paja y cascarilla de cereales",
    "1214": "Productos forrajeros",
    "1404": "Productos vegetales n.e.p.",
    "1515": "Otras grasas y aceites vegetales",
    "1703": "Melazas",
    "1905": "Productos de panadería",
    "2106": "Preparaciones alimenticias n.e.p.",
    "2201": "Aguas",
    "2202": "Aguas saborizadas o azucaradas",
    "2302": "Residuos de cereales",
    "2501": "Sal",
    "2619": "Escorias de hierro o acero",
    "2817": "Óxido o peróxido de zinc",
    "3006": "Productos farmacéuticos",
    "3101": "Fertilizantes animales o vegetales",
    "3204": "Materias colorantes orgánicas sintéticas",
    "3202": "Materias curtientes sintéticas",
    "3208": "Pinturas y barnices, no acuosos",
    "3209": "Pinturas y barnices, acuosos",
    "3210": "Las demás pinturas y barnices",
    "3305": "Productos capilares",
    "3306": "Productos de higiene dental",
    "3402": "Productos de limpieza",
    "3812": "Estabilizantes para caucho o plástico",
    "3820": "Preparaciones anticongelantes",
    "3901": "Polímeros de etileno",
    "3902": "Polímeros de propileno",
    "3903": "Polímeros de estireno",
    "3904": "Polímeros de cloruro de vinilo",
    "3905": "Polímeros de acetato de vinilo",
    "3906": "Polímeros acrílicos",
    "3914": "Intercambiadores de iones a base de polímeros",
    "3924": "Artículos domésticos de plástico",
    "3925": "Artículos de plástico para construcción",
    "4002": "Caucho sintético",
    "4007": "Hilo y cuerda de caucho vulcanizado",
    "4009": "Tubos de caucho vulcanizado",
    "4014": "Artículos higiénicos o farmacéuticos de caucho",
    "4601": "Productos de materias trenzables",
    "4101": "Cueros en bruto de bovinos o equinos",
    "4405": "Lana y harina de madera",
    "4703": "Pasta química de madera, a la sosa o al sulfato",
    "5204": "Hilo de coser de algodón",
    "5401": "Hilo de coser sintético",
    "5503": "Fibras discontinuas sintéticas",
    "5506": "Fibras discontinuas sintéticas, procesadas",
    "5508": "Hilo de coser de fibras discontinuas sintéticas",
    "5512": "Tejidos de más de 85% de fibras discontinuas sintéticas",
    "5513": "Tejidos de menos de 85% de fibras discontinuas sintéticas con peso < 170 g/m2",
    "5514": "Tejidos de menos de 85% de fibras discontinuas sintéticas con peso > 170 g/m2",
    "5515": "Otros tejidos de fibras discontinuas sintéticas",
    "5811": "Productos textiles acolchados",
    "6203": "Trajes y pantalones para hombre",
    "6204": "Trajes y pantalones para mujer",
    "6205": "Camisas para hombre",
    "6206": "Camisas para mujer",
    "6207": "Ropa interior para hombre",
    "6911": "Artículos domésticos de porcelana o loza",
    "6912": "Artículos domésticos de cerámica",
    "7013": "Artículos de vidrio para decoración de interiores",
    "7014": "Artículos de vidrio para señalización",
    "7017": "Artículos de vidrio para laboratorio, higiene o farmacia",
    "7019": "Fibras de vidrio",
    "7104": "Piedras preciosas sintéticas",
    "7203": "Productos ferrosos obtenidos por reducción de mineral de hierro",
    "7207": "Productos semiterminados de hierro o acero sin alear",
    "7210": "Productos laminados planos de hierro, ancho > 600 mm, revestidos",
    "7219": "Productos laminados planos de acero inoxidable de ancho > 600 mm",
    "7220": "Productos laminados planos de acero inoxidable de ancho < 600 mm",
    "7225": "Productos laminados planos de los demás aceros aleados, ancho > 600 mm",
    "7226": "Productos laminados planos de los demás aceros aleados, ancho < 600 mm",
    "7307": "Accesorios para tuberías de hierro o acero",
    "7308": "Estructuras y sus partes, de hierro o acero",
    "7309": "Depósitos, etc., > 300 litros, de hierro o acero",
    "7321": "Estufas y aparatos similares no eléctricos de hierro o acero",
    "7323": "Artículos domésticos de hierro o acero",
    "7314": "Telas metálicas de alambre de hierro o acero",
    "7317": "Clavos y artículos similares de hierro o acero",
    "7322": "Radiadores para calefacción central de hierro o acero",
    "7325": "Otros artículos moldeados de hierro o acero",
    "7417": "Utensilios de cocina de cobre",
    "7418": "Artículos domésticos de cobre",
    "7602": "Desechos y chatarra de aluminio",
    "7610": "Estructuras de aluminio (puentes, torres, etc.)",
    "7615": "Artículos domésticos de aluminio",
    "7616": "Otros artículos de aluminio",
    "8210": "Aparatos accionados a mano para preparar alimentos, <10 kg",
    "8301": "Candados y cerraduras",
    "8405": "Generadores de gas de agua",
    "8412": "Otros motores",
    "8418": "Refrigeradores y congeladores",
    "8421": "Centrífugas",
    "8422": "Máquinas para lavar vajilla",
    "8432": "Maquinaria para preparación o cultivo del suelo",
    "8433": "Maquinaria de cosecha o agrícola",
    "8450": "Máquinas lavadoras domésticas o de lavandería",
    "8452": "Máquinas de coser",
    "8501": "Motores y generadores eléctricos",
    "8502": "Grupos electrógenos y convertidores rotativos",
    "8509": "Aparatos electrodomésticos electromecánicos",
    "8510": "Afeitadoras eléctricas y cortadoras de cabello",
    "8512": "Equipos eléctricos de alumbrado para vehículos automotores",
    "8513": "Lámparas eléctricas portátiles",
    "8514": "Hornos eléctricos industriales",
    "8515": "Máquinas eléctricas de soldadura",
    "8516": "Calentadores eléctricos",
    "8530": "Controles eléctricos de señalización y tráfico",
    "8536": "Aparatos eléctricos para < 1 kV",
    "8538": "Partes para aparatos eléctricos",
    "8546": "Aisladores eléctricos de cualquier material",
    "8601": "Trenes eléctricos",
    "8607": "Partes de locomotoras o material rodante ferroviario",
    "8702": "Autobuses",
    "8716": "Remolques y semirremolques",
    "8901": "Buques de carga y embarcaciones similares",
    "8902": "Barcos de pesca",
    "8903": "Embarcaciones de recreo o deporte",
    "8905": "Buques para funciones especiales, n.e.p.",
    "8906": "Los demás buques",
    "8907": "Las demás estructuras flotantes",
    "8908": "Estructuras flotantes para desguace",
    "9020": "Los demás aparatos respiratorios y máscaras de gas",
    "9021": "Aparatos ortopédicos",
    "9402": "Muebles médicos, dentales o veterinarios",
    "9401": "Asientos",
    "9403": "Otros muebles y sus partes",
}

HS4_LABEL_REGEX_REPLACEMENTS = [
    (r"\bprepared or preserved\b", "preparado o conservado"),
    (r"\bpreserved\b", "conservado"),
    (r"\bfrozen\b", "congelado"),
    (r"\bother\b", "otros"),
    (r"\blive\b", "vivos"),
    (r"\bexcluding\b", "excluidos"),
    (r"\bfillets\b", "filetes"),
    (r"\bfish\b", "pescado"),
    (r"\bcrustaceans\b", "crustáceos"),
    (r"\bmolluscs\b", "moluscos"),
    (r"\bmilk\b", "leche"),
    (r"\bconcentrated\b", "concentrada"),
    (r"\bfermented\b", "fermentados"),
    (r"\bproducts\b", "productos"),
    (r"\bwhey\b", "suero"),
    (r"\bbutter\b", "mantequilla"),
    (r"\bcheese\b", "queso"),
    (r"\beggs\b", "huevos"),
    (r"\bhoney\b", "miel"),
    (r"\bcoffee\b", "café"),
    (r"\bextracts\b", "extractos"),
    (r"\btea\b", "té"),
    (r"\bmate\b", "mate"),
    (r"\bpepper\b", "pimienta"),
    (r"\bspices\b", "especias"),
    (r"\bvegetables\b", "hortalizas"),
    (r"\blegumes\b", "legumbres"),
    (r"\bfruit\b", "fruta"),
    (r"\bfruits\b", "frutas"),
    (r"\bnuts\b", "frutos secos"),
    (r"\bbananas\b", "bananos"),
    (r"\bcitrus\b", "cítricos"),
    (r"\bgrapes\b", "uvas"),
    (r"\bapples\b", "manzanas"),
    (r"\bpears\b", "peras"),
    (r"\bpotatoes\b", "papas"),
    (r"\btomatoes\b", "tomates"),
    (r"\bonions\b", "cebollas"),
    (r"\bgarlic\b", "ajo"),
    (r"\blettuce\b", "lechuga"),
    (r"\bcarrots\b", "zanahorias"),
    (r"\bcucumbers\b", "pepinos"),
    (r"\btubers\b", "tubérculos"),
    (r"\bflowers\b", "flores"),
    (r"\bplants\b", "plantas"),
    (r"\bwooden\b", "de madera"),
    (r"\bwood\b", "madera"),
    (r"\btools\b", "herramientas"),
    (r"\bmedicaments\b", "medicamentos"),
    (r"\bpackaged\b", "envasados"),
    (r"\bpolymers\b", "polímeros"),
    (r"\bethylene\b", "etileno"),
    (r"\bwoven fabrics\b", "tejidos"),
    (r"\bcotton\b", "algodón"),
    (r"\bweighing\b", "con peso"),
    (r"\bknit\b", "de punto"),
    (r"\bmotors\b", "motores"),
    (r"\bgenerators\b", "generadores"),
    (r"\belectric\b", "eléctrico"),
    (r"\belectrical\b", "eléctrico"),
    (r"\bmedical\b", "médico"),
    (r"\binstruments\b", "instrumentos"),
    (r"\bcars\b", "automóviles"),
    (r"\bpetroleum oils\b", "aceites de petróleo"),
    (r"\bpetroleum gases\b", "gases de petróleo"),
    (r"\bcrude\b", "crudos"),
    (r"\brefined\b", "refinados"),
    (r"\bore\b", "mineral"),
    (r"\bores\b", "minerales"),
    (r"\bcopper\b", "cobre"),
    (r"\bgold\b", "oro"),
    (r"\bsilver\b", "plata"),
    (r"\bdiamonds\b", "diamantes"),
    (r"\bprecious stones\b", "piedras preciosas"),
    (r"\baluminum\b", "aluminio"),
    (r"\bunwrought\b", "en bruto"),
    (r"\bmm\b", "mm"),
    (r"\band\b", "y"),
    (r"\bof\b", "de"),
    (r"\bor\b", "o"),
    (r"\bfor\b", "para"),
    (r"\bwith\b", "con"),
    (r"\bin\b", "en"),
]

HS4_LABEL_WORD_FIXES = {
    "and": "y",
    "or": "o",
    "of": "de",
    "for": "para",
    "with": "con",
    "than": "que",
    "used": "usados",
    "new": "nuevos",
    "raw": "en bruto",
    "plants": "plantas",
    "plant": "planta",
    "seeds": "semillas",
    "seed": "semilla",
    "sowing": "siembra",
    "stuffing": "relleno",
    "brooms": "escobas",
    "cocoa": "cacao",
    "paste": "pasta",
    "butter": "manteca",
    "powder": "polvo",
    "graphite": "grafito",
    "sands": "arenas",
    "sand": "arena",
    "calcium": "calcio",
    "phosphates": "fosfatos",
    "phosphate": "fosfato",
    "sulfate": "sulfato",
    "abrasives": "abrasivos",
    "magnesia": "magnesia",
    "steatite": "esteatita",
    "cryolite": "criolita",
    "borates": "boratos",
    "precious": "preciosos",
    "ores": "minerales",
    "ore": "mineral",
    "photographic": "fotográfico",
    "plates": "placas",
    "plate": "placa",
    "film": "película",
    "paper": "papel",
    "developed": "revelada",
    "preparations": "preparaciones",
    "preparation": "preparación",
    "pickling": "decapado",
    "surfaces": "superficies",
    "stabilizers": "estabilizantes",
    "elements": "elementos",
    "culture": "cultivo",
    "media": "medios",
    "noncellular": "no celulares",
    "reinforced": "reforzadas",
    "pneumatic": "neumáticos",
    "tires": "neumáticos",
    "skins": "pieles",
    "skin": "piel",
    "sheep": "ovinos",
    "lambs": "corderos",
    "leather": "cuero",
    "furskins": "pieles finas",
    "sheets": "hojas",
    "veneering": "chapado",
    "wooden": "de madera",
    "cork": "corcho",
    "debacked": "descortezado",
    "cardboard": "cartón",
    "packing": "embalaje",
    "silk": "seda",
    "woven": "tejidos",
    "cotton": "algodón",
    "flax": "lino",
    "glass": "vidrio",
    "mirrors": "espejos",
    "beads": "cuentas",
    "fibers": "fibras",
    "fiber": "fibra",
    "jewelry": "joyería",
    "imitation": "imitación",
    "flat-rolled": "laminados planos",
    "width": "ancho",
    "hot-rolled": "laminados en caliente",
    "cold-rolled": "laminados en frío",
    "clad": "revestidos",
    "forged": "forjados",
    "wire": "alambre",
    "nonalloy": "sin alear",
    "stainless": "inoxidable",
    "alloy": "aleado",
    "containers": "recipientes",
    "container": "recipiente",
    "compressed": "comprimido",
    "liquified": "licuado",
    "barbed": "de púas",
    "cloth": "telas",
    "radiators": "radiadores",
    "central": "central",
    "heating": "calefacción",
    "copper": "cobre",
    "aluminum": "aluminio",
    "lead": "plomo",
    "handtools": "herramientas de mano",
    "gardening": "jardinería",
    "pliers": "alicates",
    "pincers": "tenazas",
    "interchangeable": "intercambiables",
    "knives": "cuchillas",
    "blades": "hojas",
    "office": "oficina",
    "trays": "bandejas",
    "clips": "clips",
    "stoppers": "tapones",
    "caps": "cápsulas",
    "lids": "tapas",
    "boilers": "calderas",
    "pumps": "bombas",
    "liquids": "líquidos",
    "sprays": "pulverizadores",
    "dispersers": "dispersores",
    "processing": "procesamiento",
    "grain": "granos",
    "fabrics": "tejidos",
    "fabric": "tejido",
    "soldering": "soldadura",
    "lamps": "lámparas",
    "broadcasting": "radiodifusión",
    "insulated": "aislado",
    "coaches": "coches",
    "railway": "ferroviario",
    "cameras": "cámaras",
    "frames": "monturas",
    "spectacles": "gafas",
    "goggles": "antiparras",
    "watches": "relojes",
    "watch": "reloj",
    "sports": "deportivos",
    "fishing": "pesca",
    "hunting": "caza",
    "floating": "flotantes",
    "scrapping": "desguace",
    "transporting": "transporte",
    "goods": "mercancías",
    "household": "domésticos",
    "pharmaceutical": "farmacéuticos",
    "appliances": "aparatos",
    "motors": "motores",
    "generators": "generadores",
    "heaters": "calentadores",
    "parts": "partes",
    "structures": "estructuras",
    "furniture": "muebles",
    "seats": "asientos",
    "refrigerators": "refrigeradores",
    "freezers": "congeladores",
    "orthopedic": "ortopédicos",
    "centrifuges": "centrífugas",
    "harvesting": "cosecha",
    "sewing": "coser",
    "washing": "lavadoras",
    "machines": "máquinas",
    "machine": "máquina",
    "motors": "motores",
    "generators": "generadores",
    "padlocks": "candados",
    "locks": "cerraduras",
    "trailers": "remolques",
    "semi-trailers": "semirremolques",
    "buses": "autobuses",
    "perfumes": "perfumes",
    "pharmeceutical": "farmacéuticos",
    "hygienic": "higiénicos",
    "hygienic": "higiénicos",
    "items": "artículos",
    "flour": "harina",
    "meals": "harinas",
    "wheat": "trigo",
    "meslin": "morcajo",
    "waters": "aguas",
    "sweetened": "azucaradas",
    "flavored": "saborizadas",
    "residues": "residuos",
    "tanning": "curtientes",
    "substances": "sustancias",
    "cleaning": "limpieza",
    "antifreezing": "anticongelantes",
    "bovines": "bovinos",
    "equinos": "equinos",
    "slag": "escorias",
}


def translate_hs4_label_es(text: str) -> str:
    s = "" if text is None else str(text).strip()
    if not s:
        return s
    if s in HS4_LABEL_EXACT_ES:
        return HS4_LABEL_EXACT_ES[s]

    out = s
    for pattern, repl in HS4_LABEL_REGEX_REPLACEMENTS:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    for old, new in HS4_LABEL_WORD_FIXES.items():
        out = re.sub(rf"\b{re.escape(old)}\b", new, out, flags=re.IGNORECASE)

    out = re.sub(r"\s+", " ", out).strip(" ,;")
    if out:
        out = out[0].upper() + out[1:]
    return out


def translate_sector_label_es(text: str) -> str:
    s = "" if text is None else str(text).strip()
    if not s:
        return "Otros"
    return SECTOR_LABELS_ES.get(s, s)


def project_root() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        parent for parent in here.parents
        if (parent / "data" / "input").exists() and (parent / "data" / "intermediate").exists()
    ]
    if candidates:
        for parent in reversed(candidates):
            if (parent / "data" / "intermediate" / "complexity_calculations.csv").exists():
                return parent
        return candidates[0]
    return Path(__file__).resolve().parents[2]


def input_dir() -> Path:
    return project_root() / "data" / "input"


def intermediate_dir() -> Path:
    return project_root() / "data" / "intermediate"


def output_dir() -> Path:
    here = Path(__file__).resolve()
    candidates = [parent / "data" / "output" for parent in here.parents if (parent / "data" / "output").exists()]
    if candidates:
        for candidate in reversed(candidates):
            if (candidate / "anchors_proximity_percentile.csv").exists():
                return candidate
        return candidates[0]
    return project_root() / "data" / "output"


def _nearest_existing_data_file(filename: str, data_subdir: str) -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "data" / data_subdir / filename
        if candidate.exists():
            return candidate
    return None


def _nearest_existing_data_file_any(filenames: list[str], data_subdir: str) -> Path | None:
    for filename in filenames:
        candidate = _nearest_existing_data_file(filename, data_subdir)
        if candidate is not None:
            return candidate
    return None


def _file_mtime_ns(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except FileNotFoundError:
        return -1


def _resolve_intermediate_csv(primary_name: str, fallback_name: str | None = None) -> Path:
    primary = intermediate_dir() / primary_name
    if primary.exists():
        return primary
    if fallback_name:
        fallback = intermediate_dir() / fallback_name
        if fallback.exists():
            return fallback
    raise FileNotFoundError(
        f"Missing intermediate file. Tried: {primary_name}"
        + (f", {fallback_name}" if fallback_name else "")
    )


def normalize_0_1(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    lo = s.min()
    hi = s.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - lo) / (hi - lo)


def normalize_zscore(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    mu = s.mean()
    sigma = s.std(ddof=0)
    if not np.isfinite(mu) or not np.isfinite(sigma) or sigma == 0:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - mu) / sigma


def hs4_to_section_name(code: str) -> str:
    digits = "".join(ch for ch in str(code) if ch.isdigit())
    if len(digits) < 2:
        return "Otros"
    chapter = int(digits[:2])
    for _, chapters, label in HS_SECTION_RULES:
        if chapter in chapters:
            return label
    return "Otros"


@st.cache_data(show_spinner=False)
def load_rankings_countries(year: int = 2024) -> set[str]:
    path = input_dir() / "rankings.csv"
    df = pd.read_csv(path)
    if "year" not in df.columns:
        return set()
    df = df[pd.to_numeric(df["year"], errors="coerce") == int(year)].copy()
    if df.empty:
        return set()

    iso_col = "country_iso3_code" if "country_iso3_code" in df.columns else None
    if iso_col is None:
        candidates = [c for c in df.columns if "iso" in c.lower() and "3" in c.lower()]
        if candidates:
            iso_col = candidates[0]
    if iso_col is None:
        return set()

    s = df[iso_col].astype(str).str.upper().str.strip().str[:3]
    s = s[s.str.len() == 3]
    return set(s.unique().tolist())


@st.cache_data(show_spinner=False)
def load_hs92_reference() -> pd.DataFrame:
    path = input_dir() / "hs92_4digits.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["hs4"] = df["product_hs92_code"].astype(str).str.zfill(4)

    es_path = input_dir() / "hs92_4digits_master_es.csv"
    if not es_path.exists():
        raise FileNotFoundError(
            f"Falta el archivo maestro de traducciones HS4: {es_path}"
        )

    es = pd.read_csv(es_path, encoding="utf-8-sig")
    required_cols = {"hs4", "product_name_short_es"}
    missing_cols = required_cols.difference(es.columns)
    if missing_cols:
        raise ValueError(
            f"El archivo maestro HS4 no contiene las columnas requeridas: {sorted(missing_cols)}"
        )

    es["hs4"] = es["hs4"].astype(str).str.zfill(4)
    es["product_name_short_es"] = es["product_name_short_es"].fillna("").astype(str).str.strip()
    if es["hs4"].nunique() != 1241:
        raise ValueError(
            f"El archivo maestro HS4 debería tener 1241 códigos únicos y tiene {es['hs4'].nunique()}."
        )
    if (es["product_name_short_es"] == "").any():
        missing_codes = es.loc[es["product_name_short_es"] == "", "hs4"].tolist()[:20]
        raise ValueError(
            f"El archivo maestro HS4 contiene traducciones vacías. Ejemplos: {missing_codes}"
        )

    df = df.merge(es[["hs4", "product_name_short_es"]], on="hs4", how="left", validate="one_to_one")
    if df["product_name_short_es"].isna().any():
        missing_codes = df.loc[df["product_name_short_es"].isna(), "hs4"].tolist()[:20]
        raise ValueError(
            f"El archivo maestro HS4 no cubre todos los códigos. Ejemplos faltantes: {missing_codes}"
        )

    df["product_name_short"] = df["product_name_short_es"].astype(str).str.strip()
    sector_series = df["sector"] if "sector" in df.columns else pd.Series(["Other"] * len(df), index=df.index)
    df["sector"] = sector_series.map(translate_sector_label_es)
    return df[["hs4", "product_name_short", "product_name", "sector", "green_product"]].drop_duplicates("hs4")


@st.cache_data(show_spinner=False)
def load_natural_resource_exclusion_labels() -> list[str]:
    df = load_hs92_reference().copy()
    df["hs4"] = df["hs4"].astype(str).str.zfill(4)
    df["name"] = (
        df["product_name_short"]
        .fillna(df["product_name"])
        .fillna("")
        .astype(str)
        .str.strip()
    )
    df["sector"] = df["sector"].fillna("").astype(str)
    df["chapter"] = pd.to_numeric(df["hs4"].str[:2], errors="coerce").fillna(0).astype(int)

    raw_minerals = df["chapter"].eq(25) & ~df["hs4"].isin({"2522", "2523"})
    raw_ores = df["hs4"].between("2601", "2617")
    all_fuel_and_oil_related = df["chapter"].eq(27)
    raw_precious_stones = df["hs4"].isin({"7101", "7102", "7103", "7108"})

    is_natural_resource = raw_minerals | raw_ores | all_fuel_and_oil_related | raw_precious_stones

    out = df.loc[is_natural_resource, ["hs4", "name"]].drop_duplicates("hs4").sort_values("hs4")
    return (out["hs4"] + " - " + out["name"]).tolist()


@st.cache_data(show_spinner=False)
def _load_anchor_proximity_dataset_cached(_mtime_ns: int) -> pd.DataFrame:
    path = output_dir() / "anchors_proximity_percentile.csv"
    df = pd.read_csv(path)
    for col in ["anchor_hs4", "candidate_hs4"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.zfill(4)

    if "dai_percentile" not in df.columns and "alignment_weighted_percentile" in df.columns:
        df["dai_percentile"] = df["alignment_weighted_percentile"]
    if "dai_lead" not in df.columns and "alignment_lead_weighted" in df.columns:
        df["dai_lead"] = df["alignment_lead_weighted"]
    if "dai_index" not in df.columns:
        df["dai_index"] = 0.0
    if "alignment_weighted_percentile" not in df.columns and "dai_percentile" in df.columns:
        df["alignment_weighted_percentile"] = df["dai_percentile"]
    if "alignment_lead_weighted" not in df.columns and "dai_lead" in df.columns:
        df["alignment_lead_weighted"] = df["dai_lead"]

    numeric_cols = [
        "proximity",
        "proximity_above_country_median",
        "proximity_rank",
        "eligible_candidate_count",
        "pci",
        "cog",
        "distance_travelled",
        "accessible_market_size",
        "accessible_market_size_share",
        "accessible_market_growth_5y",
        "dai_index",
        "dai_percentile",
        "dai_lead",
        "alignment_weighted_percentile",
        "attractiveness_score",
        "feasibility_score",
        "combined_score",
        "anchor_density",
        "anchor_density_percentile",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["anchor_sector"] = df.get("anchor_sector", "").fillna("Other").astype(str).map(translate_sector_label_es)
    anchor_section_fallback = df.get("anchor_hs_section_name", "").fillna("Otros").astype(str)
    df["anchor_hs_section_name"] = df["anchor_hs4"].astype(str).map(hs4_to_section_name).where(
        df["anchor_hs4"].astype(str).str.len() >= 4,
        anchor_section_fallback,
    )
    df["candidate_sector"] = df.get("candidate_sector", "").fillna("Other").astype(str).map(translate_sector_label_es)
    df["candidate_hs_section_name"] = df.get(
        "candidate_hs_section_name",
        df.get("candidate_hs4", "").astype(str).map(hs4_to_section_name),
    )
    df["candidate_hs_section_name"] = df["candidate_hs4"].astype(str).map(hs4_to_section_name).where(
        df["candidate_hs4"].astype(str).str.len() >= 4,
        df["candidate_hs_section_name"],
    )
    df["candidate_hs_section_name"] = df["candidate_hs_section_name"].fillna("Otros").astype(str)
    df["accessible_market_size_b"] = pd.to_numeric(df.get("accessible_market_size", 0), errors="coerce").fillna(0.0) / 1_000_000_000
    try:
        metrics = pd.read_csv(intermediate_dir() / V1_METRICS_FILE, usecols=["hs4", "raw_rca_trade"])
        metrics["hs4"] = metrics["hs4"].astype(str).str.zfill(4)
        metrics["raw_rca_trade"] = pd.to_numeric(metrics["raw_rca_trade"], errors="coerce").fillna(0.0)
        df = df.merge(
            metrics.rename(columns={"hs4": "candidate_hs4", "raw_rca_trade": "candidate_raw_rca"}),
            on="candidate_hs4",
            how="left",
        )
    except Exception:
        df["candidate_raw_rca"] = 0.0
    df["candidate_raw_rca"] = pd.to_numeric(df.get("candidate_raw_rca", 0), errors="coerce").fillna(0.0)
    return df


def load_anchor_proximity_dataset() -> pd.DataFrame:
    path = output_dir() / "anchors_proximity_percentile.csv"
    df = _load_anchor_proximity_dataset_cached(_file_mtime_ns(path))
    ref = load_hs92_reference()[["hs4", "product_name_short"]].copy()
    hs4_to_name = dict(zip(ref["hs4"].astype(str).str.zfill(4), ref["product_name_short"].astype(str).str.strip()))
    df["anchor_hs4"] = df["anchor_hs4"].astype(str).str.zfill(4)
    df["candidate_hs4"] = df["candidate_hs4"].astype(str).str.zfill(4)
    df["anchor_product_name_short"] = df["anchor_hs4"].map(hs4_to_name).fillna(df.get("anchor_product_name_short", "")).astype(str).str.strip()
    df["candidate_product_name_short"] = df["candidate_hs4"].map(hs4_to_name).fillna(df.get("candidate_product_name_short", "")).astype(str).str.strip()
    return df


@st.cache_data(show_spinner=False)
def load_hs92_level6_reference() -> pd.DataFrame:
    path = input_dir() / "product_hs92.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["product_level"] = pd.to_numeric(df["product_level"], errors="coerce")
    df = df[df["product_level"] == 6].copy()
    if df.empty:
        return pd.DataFrame(columns=["hs6", "product_name"])

    code = (
        df["product_hs92_code"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(6)
        .str[:6]
    )
    df["hs6"] = code
    return df[["hs6", "product_name"]].drop_duplicates("hs6")


@st.cache_data(show_spinner=False)
def _load_gdp_ppp_weights(year: int = 2024) -> pd.Series:
    path = input_dir() / "weights_gdp_ppp.csv"
    ycol = str(int(year))
    df = pd.read_csv(path)
    if ycol not in df.columns:
        return pd.Series(dtype="float64")
    df["importer"] = df["COUNTRY.ID"].astype(str).str.upper().str.strip().str[:3]
    df = df[df["importer"].str.len() == 3].copy()
    df["gdp_raw"] = pd.to_numeric(df[ycol], errors="coerce").fillna(0.0)
    out = df.groupby("importer")["gdp_raw"].sum()
    total = float(out.sum())
    if total <= 0:
        return pd.Series(dtype="float64")
    return (out / total).rename("gdp_weight")


@st.cache_data(show_spinner=True)
def compute_network_alignment_indices_hs4(valid_hs4: Iterable[str], year: int = 2024) -> pd.DataFrame:
    valid_hs4 = set(valid_hs4)
    allowed_countries = load_rankings_countries(2024)
    trade_path = input_dir() / "hs92_country_country_product_year_6_2020_2024.csv"
    usecols = [
        "country_iso3_code",
        "partner_iso3_code",
        "product_hs92_code",
        "year",
        "export_value",
    ]

    # X_{z->y} (bilateral exports), X_{z,i} (exports by product), and M_{i,y} (partner imports by product)
    xzy_acc = pd.Series(dtype="float64")  # index: (exporter, importer)
    xzi_acc = pd.Series(dtype="float64")  # index: (exporter, product_code)
    miy_acc = pd.Series(dtype="float64")  # index: (importer, product_code)

    for chunk in pd.read_csv(trade_path, usecols=usecols, chunksize=1_000_000, low_memory=False):
        chunk["year"] = pd.to_numeric(chunk["year"], errors="coerce")
        chunk = chunk[chunk["year"] == int(year)]
        if chunk.empty:
            continue

        chunk["product_code"] = chunk["product_hs92_code"].astype(str).str[:4].str.zfill(4)
        chunk = chunk[chunk["product_code"].isin(valid_hs4)]
        if chunk.empty:
            continue

        chunk["value"] = pd.to_numeric(chunk["export_value"], errors="coerce").fillna(0.0)
        chunk["exporter_iso"] = chunk["country_iso3_code"].astype(str).str.upper().str.strip()
        chunk["importer"] = chunk["partner_iso3_code"].astype(str).str.upper().str.strip()
        if allowed_countries:
            chunk = chunk[
                chunk["exporter_iso"].isin(allowed_countries) & chunk["importer"].isin(allowed_countries)
            ]
            if chunk.empty:
                continue

        xzy_grp = chunk.groupby(["exporter_iso", "importer"])["value"].sum()
        xzy_acc = xzy_grp.copy() if xzy_acc.empty else xzy_acc.add(xzy_grp, fill_value=0)

        xzi_grp = chunk.groupby(["exporter_iso", "product_code"])["value"].sum()
        xzi_acc = xzi_grp.copy() if xzi_acc.empty else xzi_acc.add(xzi_grp, fill_value=0)

        miy_grp = chunk.groupby(["importer", "product_code"])["value"].sum()
        miy_acc = miy_grp.copy() if miy_acc.empty else miy_acc.add(miy_grp, fill_value=0)

    exporters = sorted(allowed_countries) if allowed_countries else []
    if "ECU" not in exporters:
        exporters = sorted(set(exporters).union({"ECU"}))
    products = sorted(valid_hs4)
    if xzy_acc.empty or miy_acc.empty or not exporters or not products:
        base = pd.MultiIndex.from_product(
            [[int(year)], products, exporters],
            names=["year", "product_code", "exporter_iso"],
        ).to_frame(index=False)
        base["dai_index"] = 0.0
        base["dai_percentile"] = 0.0
        base["unweighted_index"] = 0.0
        base["weighted_index"] = 0.0
        base["unweighted_percentile"] = 0.0
        base["weighted_percentile"] = 0.0
        return base[
            [
                "year",
                "product_code",
                "exporter_iso",
                "dai_index",
                "dai_percentile",
                "unweighted_index",
                "unweighted_percentile",
                "weighted_index",
                "weighted_percentile",
            ]
        ]

    xzy = xzy_acc.rename("X_zy").reset_index()
    xzy.columns = ["exporter_iso", "importer", "X_zy"]
    M_y = xzy.groupby("importer")["X_zy"].sum().rename("M_y")
    X_z = xzy.groupby("exporter_iso")["X_zy"].sum().rename("X_z")
    world_total = float(M_y.sum())

    pipe = xzy.merge(M_y.reset_index(), on="importer", how="left").merge(
        X_z.reset_index(), on="exporter_iso", how="left"
    )
    # Demand Alignment Index kernel:
    # C(z,y) = (X_zy / X_z) / (M_y / WT)
    # omega(i,y) = M_iy / world_import_i
    pipe["export_share_to_y"] = np.where(pipe["X_z"] > 0, pipe["X_zy"] / pipe["X_z"], 0.0)
    pipe["market_share_world_trade"] = np.where(world_total > 0, pipe["M_y"] / world_total, 0.0)
    pipe["dai_affinity"] = np.where(
        pipe["market_share_world_trade"] > 0,
        pipe["export_share_to_y"] / pipe["market_share_world_trade"],
        0.0,
    )
    pipe["dai_affinity"] = pipe["dai_affinity"].replace([np.inf, -np.inf], 0.0).fillna(0.0)

    miy = miy_acc.rename("M_iy").reset_index()
    miy.columns = ["importer", "product_code", "M_iy"]
    world_import_i = miy.groupby("product_code")["M_iy"].sum().rename("world_import_i")
    demand = miy.merge(world_import_i.reset_index(), on="product_code", how="left")
    demand["omega"] = np.where(demand["world_import_i"] > 0, demand["M_iy"] / demand["world_import_i"], 0.0)
    demand["omega"] = demand["omega"].replace([np.inf, -np.inf], 0.0).fillna(0.0)

    partners = sorted(set(pipe["importer"]).union(set(demand["importer"])))
    affinity_mat = (
        pipe.pivot(index="exporter_iso", columns="importer", values="dai_affinity")
        .reindex(index=exporters, columns=partners, fill_value=0.0)
        .fillna(0.0)
    )
    omega_mat = (
        demand.pivot(index="importer", columns="product_code", values="omega")
        .reindex(index=partners, columns=products, fill_value=0.0)
        .fillna(0.0)
    )

    dai_arr = affinity_mat.to_numpy(dtype=float) @ omega_mat.to_numpy(dtype=float)

    dai_df = (
        pd.DataFrame(dai_arr, index=exporters, columns=products)
        .stack(future_stack=True)
        .rename("dai_index")
        .reset_index()
        .rename(columns={"level_0": "exporter_iso", "level_1": "product_code"})
    )
    out = dai_df.copy()
    out["year"] = int(year)

    if not xzi_acc.empty:
        xzi = xzi_acc.rename("X_zi").reset_index()
        xzi.columns = ["exporter_iso", "product_code", "X_zi"]
        top30 = (
            xzi.sort_values(["product_code", "X_zi", "exporter_iso"], ascending=[True, False, True])
            .groupby("product_code", sort=False)
            .head(30)[["product_code", "exporter_iso"]]
        )
    else:
        top30 = pd.DataFrame(columns=["product_code", "exporter_iso"])

    ecu_rows = pd.DataFrame({"product_code": products, "exporter_iso": "ECU"})
    comparison_set = pd.concat([top30, ecu_rows], ignore_index=True).drop_duplicates()
    out = out.merge(comparison_set, on=["product_code", "exporter_iso"], how="inner")

    out["dai_percentile"] = out.groupby("product_code")["dai_index"].rank(method="average", pct=True) * 100
    # Compatibility aliases for existing downstream files/scripts.
    out["unweighted_index"] = out["dai_index"]
    out["weighted_index"] = out["dai_index"]
    out["unweighted_percentile"] = out["dai_percentile"]
    out["weighted_percentile"] = out["dai_percentile"]
    return out[
        [
            "year",
            "product_code",
            "exporter_iso",
            "dai_index",
            "dai_percentile",
            "unweighted_index",
            "unweighted_percentile",
            "weighted_index",
            "weighted_percentile",
        ]
    ]


@st.cache_data(show_spinner=False)
def compute_alignment_leads_hs4(valid_hs4: Iterable[str], year: int = 2024) -> pd.DataFrame:
    valid_hs4 = set(valid_hs4)
    allowed_countries = load_rankings_countries(2024)
    trade_path = input_dir() / "hs92_country_country_product_year_6_2020_2024.csv"
    usecols = [
        "country_iso3_code",
        "partner_iso3_code",
        "product_hs92_code",
        "year",
        "export_value",
    ]

    xzi_acc = pd.Series(dtype="float64")  # index: (exporter_iso, hs4)
    for chunk in pd.read_csv(trade_path, usecols=usecols, chunksize=1_000_000, low_memory=False):
        chunk["year"] = pd.to_numeric(chunk["year"], errors="coerce")
        chunk = chunk[chunk["year"] == int(year)]
        if chunk.empty:
            continue
        chunk["hs4"] = chunk["product_hs92_code"].astype(str).str[:4].str.zfill(4)
        chunk = chunk[chunk["hs4"].isin(valid_hs4)]
        if chunk.empty:
            continue
        chunk["exporter_iso"] = chunk["country_iso3_code"].astype(str).str.upper().str.strip()
        chunk["importer_iso"] = chunk["partner_iso3_code"].astype(str).str.upper().str.strip()
        if allowed_countries:
            chunk = chunk[
                chunk["exporter_iso"].isin(allowed_countries) & chunk["importer_iso"].isin(allowed_countries)
            ]
            if chunk.empty:
                continue
        chunk["value"] = pd.to_numeric(chunk["export_value"], errors="coerce").fillna(0.0)
        grp = chunk.groupby(["exporter_iso", "hs4"])["value"].sum()
        xzi_acc = grp.copy() if xzi_acc.empty else xzi_acc.add(grp, fill_value=0.0)

    base = pd.DataFrame({"hs4": sorted(valid_hs4)})
    if xzi_acc.empty:
        base["dai_lead"] = 0.0
        base["alignment_lead_unweighted"] = 0.0
        base["alignment_lead_weighted"] = 0.0
        return base[["hs4", "dai_lead", "alignment_lead_unweighted", "alignment_lead_weighted"]]

    exports = xzi_acc.rename("exports_2024").reset_index()
    exports.columns = ["exporter_iso", "hs4", "exports_2024"]

    top5 = (
        exports[exports["exporter_iso"] != "ECU"]
        .sort_values(["hs4", "exports_2024", "exporter_iso"], ascending=[True, False, True])
        .groupby("hs4", sort=False)
        .head(5)[["hs4", "exporter_iso"]]
    )

    align = compute_network_alignment_indices_hs4(valid_hs4, year=year).rename(columns={"product_code": "hs4"})[
        ["hs4", "exporter_iso", "dai_percentile"]
    ]

    comp = top5.merge(align, on=["hs4", "exporter_iso"], how="left")
    comp_med = comp.groupby("hs4", as_index=False).agg(
        competitor_median_dai=("dai_percentile", "median"),
    )

    ecu = align[align["exporter_iso"] == "ECU"][
        ["hs4", "dai_percentile"]
    ].rename(
        columns={
            "dai_percentile": "ecu_dai_percentile",
        }
    )

    out = base.merge(ecu, on="hs4", how="left").merge(comp_med, on="hs4", how="left")
    out["dai_lead"] = (
        pd.to_numeric(out["ecu_dai_percentile"], errors="coerce").fillna(0.0)
        - pd.to_numeric(out["competitor_median_dai"], errors="coerce").fillna(0.0)
    )
    out["alignment_lead_unweighted"] = out["dai_lead"]
    out["alignment_lead_weighted"] = out["dai_lead"]
    return out[["hs4", "dai_lead", "alignment_lead_unweighted", "alignment_lead_weighted"]]


@st.cache_data(show_spinner=True)
def compute_trade_metrics(valid_hs4: Iterable[str]) -> pd.DataFrame:
    valid_hs4 = set(valid_hs4)
    allowed_countries = load_rankings_countries(2024)
    trade_path = input_dir() / "hs92_country_country_product_year_6_2020_2024.csv"
    distance_path = intermediate_dir() / "ecuador_distance.csv"
    accessible_path = intermediate_dir() / "accessible_market_by_product.csv"
    accessible_growth_path = intermediate_dir() / "accessible_market_growth_by_product.csv"
    accessible_growth_yearly_path = intermediate_dir() / "accessible_market_by_product_year.csv"
    potential_path = intermediate_dir() / "potential_market_by_product.csv"
    potential_growth_path = intermediate_dir() / "potential_market_growth_by_product.csv"
    potential_growth_yearly_path = intermediate_dir() / "potential_market_by_product_year.csv"

    world_acc = pd.Series(dtype="float64")  # index: (year, hs4)
    ecu_year_acc = pd.Series(dtype="float64")  # index: (year, hs4)
    imports_2024_acc = pd.Series(dtype="float64")  # index: (importer, hs4)
    exp_hs4_2024_acc = pd.Series(dtype="float64")  # index: (exporter, hs4)

    # Accessible market size and its 2020-2024 CAGR by product for Ecuador (HS4).
    # Accept both renamed outputs and legacy potential-market file names for robustness.
    if accessible_growth_path.exists():
        pm = pd.read_csv(accessible_growth_path)
        pm["iso3_o"] = pm["iso3_o"].astype(str).str.upper().str.strip()
        pm = pm[pm["iso3_o"] == FOCUS_ISO].copy()
        pm["hs4"] = (
            pm["hs92"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.replace(r"\D", "", regex=True)
            .str.zfill(4)
            .str[-4:]
        )
        pm["accessible_market_size_2020"] = pd.to_numeric(pm.get("accessible_market_size_2020", 0), errors="coerce").fillna(0.0)
        pm["accessible_market_size_2024"] = pd.to_numeric(pm.get("accessible_market_size_2024", 0), errors="coerce").fillna(0.0)
        pm = pm.groupby("hs4", as_index=False)[["accessible_market_size_2020", "accessible_market_size_2024"]].sum()
        pm["accessible_market_size"] = pm["accessible_market_size_2024"]
        pm["accessible_market_growth_5y"] = np.where(
            (pm["accessible_market_size_2020"] > 0) & (pm["accessible_market_size_2024"] > 0),
            (pm["accessible_market_size_2024"] / pm["accessible_market_size_2020"]) ** (1 / 5) - 1,
            0.0,
        )
        pm = pm[["hs4", "accessible_market_size", "accessible_market_growth_5y"]]
    elif accessible_growth_yearly_path.exists():
        pm = pd.read_csv(accessible_growth_yearly_path)
        pm["iso3_o"] = pm["iso3_o"].astype(str).str.upper().str.strip()
        pm = pm[pm["iso3_o"] == FOCUS_ISO].copy()
        pm["hs4"] = (
            pm["hs92"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.replace(r"\D", "", regex=True)
            .str.zfill(4)
            .str[-4:]
        )
        pm["year"] = pd.to_numeric(pm["year"], errors="coerce")
        pm["accessible_market_size"] = pd.to_numeric(pm["accessible_market_size"], errors="coerce").fillna(0.0)
        pm = pm[pm["year"].isin([2020, 2024])].copy()
        pm = pm.groupby(["hs4", "year"], as_index=False)["accessible_market_size"].sum()
        pm = pm.pivot(index="hs4", columns="year", values="accessible_market_size").reset_index()
        for y in [2020, 2024]:
            if y not in pm.columns:
                pm[y] = 0.0
        pm["accessible_market_size_2020"] = pd.to_numeric(pm[2020], errors="coerce").fillna(0.0)
        pm["accessible_market_size_2024"] = pd.to_numeric(pm[2024], errors="coerce").fillna(0.0)
        pm["accessible_market_size"] = pm["accessible_market_size_2024"]
        pm["accessible_market_growth_5y"] = np.where(
            (pm["accessible_market_size_2020"] > 0) & (pm["accessible_market_size_2024"] > 0),
            (pm["accessible_market_size_2024"] / pm["accessible_market_size_2020"]) ** (1 / 5) - 1,
            0.0,
        )
        pm = pm[["hs4", "accessible_market_size", "accessible_market_growth_5y"]]
    elif potential_growth_path.exists():
        pm = pd.read_csv(potential_growth_path)
        pm["iso3_d"] = pm["iso3_d"].astype(str).str.upper().str.strip()
        pm = pm[pm["iso3_d"] == FOCUS_ISO].copy()
        pm["hs4"] = (
            pm["hs92"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.replace(r"\D", "", regex=True)
            .str.zfill(4)
            .str[-4:]
        )
        pm["accessible_market_size_2020"] = pd.to_numeric(pm.get("potential_market_size_2020", 0), errors="coerce").fillna(0.0)
        pm["accessible_market_size_2024"] = pd.to_numeric(pm.get("potential_market_size_2024", 0), errors="coerce").fillna(0.0)
        pm = pm.groupby("hs4", as_index=False)[["accessible_market_size_2020", "accessible_market_size_2024"]].sum()
        pm["accessible_market_size"] = pm["accessible_market_size_2024"]
        pm["accessible_market_growth_5y"] = np.where(
            (pm["accessible_market_size_2020"] > 0) & (pm["accessible_market_size_2024"] > 0),
            (pm["accessible_market_size_2024"] / pm["accessible_market_size_2020"]) ** (1 / 5) - 1,
            0.0,
        )
        pm = pm[["hs4", "accessible_market_size", "accessible_market_growth_5y"]]
    elif potential_growth_yearly_path.exists():
        pm = pd.read_csv(potential_growth_yearly_path)
        pm["iso3_d"] = pm["iso3_d"].astype(str).str.upper().str.strip()
        pm = pm[pm["iso3_d"] == FOCUS_ISO].copy()
        pm["hs4"] = (
            pm["hs92"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.replace(r"\D", "", regex=True)
            .str.zfill(4)
            .str[-4:]
        )
        pm["year"] = pd.to_numeric(pm["year"], errors="coerce")
        pm["accessible_market_size"] = pd.to_numeric(pm["potential_market_size"], errors="coerce").fillna(0.0)
        pm = pm[pm["year"].isin([2020, 2024])].copy()
        pm = pm.groupby(["hs4", "year"], as_index=False)["accessible_market_size"].sum()
        pm = pm.pivot(index="hs4", columns="year", values="accessible_market_size").reset_index()
        for y in [2020, 2024]:
            if y not in pm.columns:
                pm[y] = 0.0
        pm["accessible_market_size_2020"] = pd.to_numeric(pm[2020], errors="coerce").fillna(0.0)
        pm["accessible_market_size_2024"] = pd.to_numeric(pm[2024], errors="coerce").fillna(0.0)
        pm["accessible_market_size"] = pm["accessible_market_size_2024"]
        pm["accessible_market_growth_5y"] = np.where(
            (pm["accessible_market_size_2020"] > 0) & (pm["accessible_market_size_2024"] > 0),
            (pm["accessible_market_size_2024"] / pm["accessible_market_size_2020"]) ** (1 / 5) - 1,
            0.0,
        )
        pm = pm[["hs4", "accessible_market_size", "accessible_market_growth_5y"]]
    elif potential_path.exists():
        pm = pd.read_csv(potential_path)
        pm["iso3_d"] = pm["iso3_d"].astype(str).str.upper().str.strip()
        pm = pm[pm["iso3_d"] == FOCUS_ISO].copy()
        pm["hs4"] = (
            pm["hs92"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.replace(r"\D", "", regex=True)
            .str.zfill(4)
            .str[-4:]
        )
        pm["accessible_market_size"] = pd.to_numeric(pm["potential_market_imports_sum"], errors="coerce").fillna(0.0)
        pm = pm.groupby("hs4", as_index=False)["accessible_market_size"].sum()
        pm["accessible_market_growth_5y"] = 0.0
    else:
        pm = pd.DataFrame({"hs4": sorted(valid_hs4), "accessible_market_size": 0.0, "accessible_market_growth_5y": 0.0})

    usecols = [
        "country_iso3_code",
        "partner_iso3_code",
        "product_hs92_code",
        "year",
        "export_value",
    ]

    for chunk in pd.read_csv(trade_path, usecols=usecols, chunksize=1_000_000, low_memory=False):
        chunk["year"] = pd.to_numeric(chunk["year"], errors="coerce")
        chunk = chunk[chunk["year"].isin([2020, 2024])]
        if chunk.empty:
            continue

        chunk["year"] = chunk["year"].astype(int)
        chunk["hs4"] = chunk["product_hs92_code"].astype(str).str[:4].str.zfill(4)
        chunk = chunk[chunk["hs4"].isin(valid_hs4)]
        if chunk.empty:
            continue

        chunk["value"] = pd.to_numeric(chunk["export_value"], errors="coerce").fillna(0)
        chunk["exporter"] = chunk["country_iso3_code"].astype(str).str.upper().str.strip()
        chunk["importer"] = chunk["partner_iso3_code"].astype(str).str.upper().str.strip()
        if allowed_countries:
            chunk = chunk[
                chunk["exporter"].isin(allowed_countries) & chunk["importer"].isin(allowed_countries)
            ]
            if chunk.empty:
                continue

        world_grp = chunk.groupby(["year", "hs4"])["value"].sum()
        if world_acc.empty:
            world_acc = world_grp.copy()
        else:
            world_acc = world_acc.add(world_grp, fill_value=0)

        ecu_year_grp = chunk[chunk["exporter"] == "ECU"].groupby(["year", "hs4"])["value"].sum()
        if ecu_year_acc.empty:
            ecu_year_acc = ecu_year_grp.copy()
        else:
            ecu_year_acc = ecu_year_acc.add(ecu_year_grp, fill_value=0)

        c2024 = chunk[chunk["year"] == 2024]
        if c2024.empty:
            continue

        imp_grp = c2024.groupby(["importer", "hs4"])["value"].sum()
        if imports_2024_acc.empty:
            imports_2024_acc = imp_grp.copy()
        else:
            imports_2024_acc = imports_2024_acc.add(imp_grp, fill_value=0)

        exp_grp = c2024.groupby(["exporter", "hs4"])["value"].sum()
        if exp_hs4_2024_acc.empty:
            exp_hs4_2024_acc = exp_grp.copy()
        else:
            exp_hs4_2024_acc = exp_hs4_2024_acc.add(exp_grp, fill_value=0)

    world = world_acc.rename("value").reset_index()
    world.columns = ["year", "hs4", "world_value"]

    world_pivot = world.pivot(index="hs4", columns="year", values="world_value").reset_index()
    if 2020 not in world_pivot.columns:
        world_pivot[2020] = 0
    if 2024 not in world_pivot.columns:
        world_pivot[2024] = 0
    world_pivot["market_growth_5y"] = np.where(
        (world_pivot[2020] > 0) & (world_pivot[2024] > 0),
        (world_pivot[2024] / world_pivot[2020]) ** (1 / 5) - 1,
        0,
    )

    world_2024 = world[world["year"] == 2024][["hs4", "world_value"]].rename(columns={"world_value": "total_trade"})
    world_total_2024 = world_2024["total_trade"].sum()
    world_2024["market_size_share"] = np.where(
        world_total_2024 > 0,
        world_2024["total_trade"] / world_total_2024,
        0,
    )

    if ecu_year_acc.empty:
        ecu_pivot = pd.DataFrame({"hs4": sorted(valid_hs4), 2020: 0.0, 2024: 0.0})
    else:
        ecu_year = ecu_year_acc.rename("ecu_value").reset_index()
        ecu_year.columns = ["year", "hs4", "ecu_value"]
        ecu_pivot = ecu_year.pivot(index="hs4", columns="year", values="ecu_value").reset_index()
        if 2020 not in ecu_pivot.columns:
            ecu_pivot[2020] = 0.0
        if 2024 not in ecu_pivot.columns:
            ecu_pivot[2024] = 0.0

    ecu_pivot["ecu_export_growth_5y"] = np.where(
        (ecu_pivot[2020] > 0) & (ecu_pivot[2024] > 0),
        (ecu_pivot[2024] / ecu_pivot[2020]) ** (1 / 5) - 1,
        0,
    )
    ecu_2024 = ecu_pivot[["hs4", 2024, "ecu_export_growth_5y"]].rename(columns={2024: "ecu_total_trade"})

    # Ecuador market share by product and absolute change (2024 - 2020).
    share_df = world_pivot[["hs4", 2020, 2024]].rename(columns={2020: "world_2020", 2024: "world_2024"})
    share_df = share_df.merge(
        ecu_pivot[["hs4", 2020, 2024]].rename(columns={2020: "ecu_2020", 2024: "ecu_2024"}),
        on="hs4",
        how="left",
    ).fillna(0)
    share_df["ecu_market_share_2020"] = np.where(share_df["world_2020"] > 0, share_df["ecu_2020"] / share_df["world_2020"], 0)
    share_df["ecu_market_share_2024"] = np.where(share_df["world_2024"] > 0, share_df["ecu_2024"] / share_df["world_2024"], 0)
    share_df["market_share_change_abs"] = share_df["ecu_market_share_2024"] - share_df["ecu_market_share_2020"]
    share_df = share_df[["hs4", "ecu_market_share_2020", "ecu_market_share_2024", "market_share_change_abs"]]

    # Use the canonical product-level travelled distance from hs92_attributes.csv.
    # This is the export-weighted bilateral distance generated in data_processing.ipynb
    # and is the same threshold used to construct accessible market.
    distance_travelled = load_hs4_distance_attributes()

    # Effective number of exporters (Hill number of order 2 / inverse HHI) under the same 145-country filter.
    if exp_hs4_2024_acc.empty:
        eff_df = pd.DataFrame({"hs4": sorted(valid_hs4), "eff_num_exp": 0.0})
        rank_df = pd.DataFrame({"hs4": sorted(valid_hs4), "ecu_exporter_rank": np.nan})
    else:
        exp_hs4 = exp_hs4_2024_acc.rename("value").reset_index()
        exp_hs4.columns = ["exporter", "hs4", "value"]
        totals = exp_hs4.groupby("hs4")["value"].sum().rename("total")
        exp_hs4 = exp_hs4.merge(totals, on="hs4", how="left")
        exp_hs4["share"] = np.where(exp_hs4["total"] > 0, exp_hs4["value"] / exp_hs4["total"], 0)
        eff_df = (
            exp_hs4.groupby("hs4", as_index=False)["share"]
            .apply(lambda s: float(1 / np.sum(np.square(s))) if np.sum(np.square(s)) > 0 else 0.0)
            .rename(columns={"share": "eff_num_exp"})
        )
        # Ecuador's rank among exporters by product in 2024 (1 = largest exporter).
        exp_hs4["exporter_rank"] = exp_hs4.groupby("hs4")["value"].rank(method="min", ascending=False)
        ecu_rank = exp_hs4[exp_hs4["exporter"] == "ECU"][["hs4", "exporter_rank"]].rename(
            columns={"exporter_rank": "ecu_exporter_rank"}
        )
        rank_df = pd.DataFrame({"hs4": sorted(valid_hs4)}).merge(ecu_rank, on="hs4", how="left")

    out = world_pivot[["hs4", "market_growth_5y"]].merge(world_2024, on="hs4", how="outer")
    out = out.merge(ecu_2024, on="hs4", how="left")
    out = out.merge(share_df, on="hs4", how="left")
    out = out.merge(distance_travelled, on="hs4", how="left")
    out = out.merge(eff_df, on="hs4", how="left")
    out = out.merge(rank_df, on="hs4", how="left")
    out = out.merge(pm, on="hs4", how="left")
    out = out.fillna(0)
    # Raw RCA for ECU in 2024 from trade shares:
    # RCA_i = (X_ECU_i / X_ECU_total) / (X_world_i / X_world_total)
    ecu_total_2024 = float(pd.to_numeric(out["ecu_total_trade"], errors="coerce").fillna(0.0).sum())
    world_total_2024 = float(pd.to_numeric(out["total_trade"], errors="coerce").fillna(0.0).sum())
    out["raw_rca_trade"] = np.where(
        (ecu_total_2024 > 0) & (world_total_2024 > 0) & (out["total_trade"] > 0),
        (pd.to_numeric(out["ecu_total_trade"], errors="coerce").fillna(0.0) / ecu_total_2024)
        / (pd.to_numeric(out["total_trade"], errors="coerce").fillna(0.0) / world_total_2024),
        0.0,
    )
    out["raw_rca_trade"] = (
        pd.to_numeric(out["raw_rca_trade"], errors="coerce")
        .replace([np.inf, -np.inf], 0.0)
        .fillna(0.0)
    )
    out["market_size"] = pd.to_numeric(out["total_trade"], errors="coerce").fillna(0.0)
    total_accessible_size = float(pd.to_numeric(out["accessible_market_size"], errors="coerce").fillna(0.0).sum())
    out["accessible_market_size_share"] = np.where(
        total_accessible_size > 0,
        pd.to_numeric(out["accessible_market_size"], errors="coerce").fillna(0.0) / total_accessible_size,
        0.0,
    )
    out["accessible_market_to_market_ratio"] = np.where(
        out["market_size"] > 0,
        pd.to_numeric(out["accessible_market_size"], errors="coerce").fillna(0.0) / out["market_size"],
        0.0,
    )
    out["ecu_exporter_rank"] = pd.to_numeric(out["ecu_exporter_rank"], errors="coerce")
    out.loc[out["ecu_exporter_rank"] <= 0, "ecu_exporter_rank"] = np.nan
    median_cagr = out["market_growth_5y"].median()
    median_accessible_market_growth = out["accessible_market_growth_5y"].median()
    median_ecu_export_cagr = out["ecu_export_growth_5y"].median()
    out["above_median_cagr"] = out["market_growth_5y"] > median_cagr
    out["above_median_accessible_market_growth"] = out["accessible_market_growth_5y"] > median_accessible_market_growth
    out["above_median_export_cagr"] = out["ecu_export_growth_5y"] > median_ecu_export_cagr
    return out


@st.cache_data(show_spinner=False)
def load_product_market_deep_dive(hs4: str, focus_year: int = 2024) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    allowed_countries = load_rankings_countries(2024)
    trade_path = input_dir() / "hs92_country_country_product_year_6_2020_2024.csv"
    usecols = [
        "country_iso3_code",
        "partner_iso3_code",
        "product_hs92_code",
        "year",
        "export_value",
    ]

    hs4 = str(hs4).zfill(4)
    world_by_year = pd.Series(dtype="float64")  # index: year
    ecu_by_year = pd.Series(dtype="float64")  # index: year
    dest_focus = pd.Series(dtype="float64")  # index: importer
    hs6_year_acc = pd.Series(dtype="float64")  # index: (hs6, year), ECU exports

    for chunk in pd.read_csv(trade_path, usecols=usecols, chunksize=1_000_000, low_memory=False):
        chunk["hs4"] = chunk["product_hs92_code"].astype(str).str[:4].str.zfill(4)
        chunk = chunk[chunk["hs4"] == hs4]
        if chunk.empty:
            continue

        chunk["year"] = pd.to_numeric(chunk["year"], errors="coerce")
        chunk = chunk[chunk["year"].notna()]
        if chunk.empty:
            continue
        chunk["year"] = chunk["year"].astype(int)
        chunk = chunk[chunk["year"].between(2020, 2024)]
        if chunk.empty:
            continue
        chunk["value"] = pd.to_numeric(chunk["export_value"], errors="coerce").fillna(0)
        chunk["exporter"] = chunk["country_iso3_code"].astype(str).str.upper().str.strip()
        chunk["importer"] = chunk["partner_iso3_code"].astype(str).str.upper().str.strip()
        chunk["hs6"] = chunk["product_hs92_code"].astype(str).str.zfill(6).str[:6]
        if allowed_countries:
            chunk = chunk[
                chunk["exporter"].isin(allowed_countries) & chunk["importer"].isin(allowed_countries)
            ]
            if chunk.empty:
                continue

        w = chunk.groupby("year")["value"].sum()
        world_by_year = w.copy() if world_by_year.empty else world_by_year.add(w, fill_value=0)

        ecu = chunk[chunk["exporter"] == "ECU"].groupby("year")["value"].sum()
        ecu_by_year = ecu.copy() if ecu_by_year.empty else ecu_by_year.add(ecu, fill_value=0)

        ecu_hs6 = chunk[chunk["exporter"] == "ECU"].groupby(["hs6", "year"])["value"].sum()
        hs6_year_acc = ecu_hs6.copy() if hs6_year_acc.empty else hs6_year_acc.add(ecu_hs6, fill_value=0)

        focus = chunk[(chunk["year"] == focus_year) & (chunk["exporter"] == "ECU")].groupby("importer")["value"].sum()
        dest_focus = focus.copy() if dest_focus.empty else dest_focus.add(focus, fill_value=0)

    if world_by_year.empty:
        share_df = pd.DataFrame(columns=["year", "world_value", "ecu_value", "ecu_market_share"])
    else:
        share_df = world_by_year.rename("world_value").reset_index()
        share_df.columns = ["year", "world_value"]
        ecu_df = ecu_by_year.rename("ecu_value").reset_index()
        ecu_df.columns = ["year", "ecu_value"]
        share_df = share_df.merge(ecu_df, on="year", how="left").fillna(0)
        share_df["ecu_market_share"] = np.where(
            share_df["world_value"] > 0,
            share_df["ecu_value"] / share_df["world_value"],
            0,
        )
        share_df = share_df.sort_values("year").reset_index(drop=True)

    if dest_focus.empty:
        dest_df = pd.DataFrame(columns=["importer", "value", "share"])
    else:
        dest_df = dest_focus.rename("value").reset_index()
        dest_df.columns = ["importer", "value"]
        total = dest_df["value"].sum()
        dest_df["share"] = np.where(total > 0, dest_df["value"] / total, 0)
        dest_df = dest_df.sort_values("value", ascending=False).reset_index(drop=True)

    if hs6_year_acc.empty:
        hs6_table = pd.DataFrame(
            columns=["hs6", "product_name", "2020", "2021", "2022", "2023", "2024", "total_2020_2024", "cagr_5y"]
        )
    else:
        hs6_long = hs6_year_acc.rename("value").reset_index()
        hs6_long.columns = ["hs6", "year", "value"]
        hs6_table = hs6_long.pivot(index="hs6", columns="year", values="value").reset_index()
        for y in [2020, 2021, 2022, 2023, 2024]:
            if y not in hs6_table.columns:
                hs6_table[y] = 0.0
        hs6_table = hs6_table[["hs6", 2020, 2021, 2022, 2023, 2024]].fillna(0.0)
        hs6_table["total_2020_2024"] = hs6_table[[2020, 2021, 2022, 2023, 2024]].sum(axis=1)
        hs6_table["cagr_5y"] = np.where(
            (hs6_table[2020] > 0) & (hs6_table[2024] > 0),
            (hs6_table[2024] / hs6_table[2020]) ** (1 / 5) - 1,
            0.0,
        )
        hs6_table = hs6_table.sort_values("total_2020_2024", ascending=False).reset_index(drop=True)
        hs6_table = hs6_table.rename(columns={2020: "2020", 2021: "2021", 2022: "2022", 2023: "2023", 2024: "2024"})
        hs6_ref = load_hs92_level6_reference()
        hs6_table = hs6_table.merge(hs6_ref, on="hs6", how="left")
        hs6_table["product_name"] = hs6_table["product_name"].fillna("")
        hs6_table = hs6_table[
            ["hs6", "product_name", "2020", "2021", "2022", "2023", "2024", "total_2020_2024", "cagr_5y"]
        ]

    return dest_df, share_df, hs6_table


@st.cache_data(show_spinner=False)
def load_accessible_market_destinations_by_product(hs4: str, focus_year: int = 2024) -> pd.DataFrame:
    hs4 = str(hs4).zfill(4)
    compact_path = _nearest_existing_data_file("accessible_market_country_hs4_ecu_2024.csv", "intermediate")
    if compact_path is not None and int(focus_year) == 2024:
        df = pd.read_csv(compact_path, low_memory=False)
        if df.empty:
            return pd.DataFrame(columns=["importer_iso", "accessible_market_imports"])
        df["hs4"] = df["hs4"].astype(str).str.zfill(4)
        df["importer_iso"] = df["importer_iso"].astype(str).str.upper().str.strip()
        df["accessible_market_imports"] = pd.to_numeric(df["accessible_market_imports"], errors="coerce").fillna(0.0)
        return (
            df[df["hs4"] == hs4]
            .groupby("importer_iso", as_index=False)["accessible_market_imports"]
            .sum()
            .sort_values("accessible_market_imports", ascending=False)
            .reset_index(drop=True)
        )

    detailed_path = _nearest_existing_data_file("accessible_market_by_country_product_year.csv", "intermediate")
    if detailed_path is None:
        return pd.DataFrame(columns=["importer_iso", "accessible_market_imports"])

    acc = pd.Series(dtype="float64")
    usecols = ["year", "iso3_o", "iso3_d", "hs92", "accessible_market", "accessible_market_imports"]
    for chunk in pd.read_csv(detailed_path, usecols=usecols, chunksize=500_000, low_memory=False):
        chunk["year"] = pd.to_numeric(chunk["year"], errors="coerce")
        chunk["hs4"] = chunk["hs92"].astype(str).str.zfill(4)
        chunk["origin_iso"] = chunk["iso3_o"].astype(str).str.upper().str.strip()
        chunk["importer_iso"] = chunk["iso3_d"].astype(str).str.upper().str.strip()
        chunk["accessible_market_imports"] = pd.to_numeric(chunk["accessible_market_imports"], errors="coerce").fillna(0.0)
        chunk["accessible_market"] = pd.to_numeric(chunk["accessible_market"], errors="coerce").fillna(0).astype(int)
        chunk = chunk[
            (chunk["year"] == int(focus_year))
            & (chunk["origin_iso"] == FOCUS_ISO)
            & (chunk["hs4"] == hs4)
            & ((chunk["accessible_market"] == 1) | (chunk["accessible_market_imports"] > 0))
        ]
        if chunk.empty:
            continue
        grp = chunk.groupby("importer_iso")["accessible_market_imports"].sum()
        acc = grp.copy() if acc.empty else acc.add(grp, fill_value=0)

    if acc.empty:
        return pd.DataFrame(columns=["importer_iso", "accessible_market_imports"])

    return (
        acc.rename("accessible_market_imports")
        .reset_index()
        .sort_values("accessible_market_imports", ascending=False)
        .reset_index(drop=True)
    )


@st.cache_data(show_spinner=False)
def load_top_exporters_for_product_markets(
    hs4: str,
    importers: tuple[str, ...],
    focus_year: int = 2024,
    top_n: int = 20,
) -> pd.DataFrame:
    hs4 = str(hs4).zfill(4)
    importer_set = {str(x).upper().strip() for x in importers if str(x).strip()}
    if not importer_set:
        return pd.DataFrame(columns=["exporter_iso", "export_value", "export_value_m", "market_share"])

    compact_path = _nearest_existing_data_file_any(
        ["exporters_by_importer_hs4_2024.csv.gz", "exporters_by_importer_hs4_2024.csv"],
        "intermediate",
    )
    if compact_path is not None and int(focus_year) == 2024:
        df = pd.read_csv(compact_path, low_memory=False)
        if df.empty:
            return pd.DataFrame(columns=["rank", "exporter_iso", "export_value", "export_value_m", "market_share"])
        df["hs4"] = df["hs4"].astype(str).str.zfill(4)
        df["importer_iso"] = df["importer_iso"].astype(str).str.upper().str.strip()
        df["exporter_iso"] = df["exporter_iso"].astype(str).str.upper().str.strip()
        df["export_value"] = pd.to_numeric(df["export_value"], errors="coerce").fillna(0.0)
        out = (
            df[(df["hs4"] == hs4) & (df["importer_iso"].isin(importer_set))]
            .groupby("exporter_iso", as_index=False)["export_value"]
            .sum()
            .sort_values("export_value", ascending=False)
            .reset_index(drop=True)
        )
        if out.empty:
            return pd.DataFrame(columns=["rank", "exporter_iso", "export_value", "export_value_m", "market_share"])
        total_value = float(out["export_value"].sum())
        out["export_value_m"] = out["export_value"] / 1_000_000
        out["market_share"] = out["export_value"] / total_value if total_value > 0 else 0.0
        out["rank"] = np.arange(1, len(out) + 1)
        return out.head(int(top_n))[["rank", "exporter_iso", "export_value", "export_value_m", "market_share"]]

    trade_path = _nearest_existing_data_file("hs92_country_country_product_year_6_2020_2024.csv", "input")
    if trade_path is None:
        return pd.DataFrame(columns=["exporter_iso", "export_value", "export_value_m", "market_share"])

    acc = pd.Series(dtype="float64")
    usecols = ["country_iso3_code", "partner_iso3_code", "product_hs92_code", "year", "export_value"]
    for chunk in pd.read_csv(trade_path, usecols=usecols, chunksize=500_000, low_memory=False):
        chunk["year"] = pd.to_numeric(chunk["year"], errors="coerce")
        chunk = chunk[chunk["year"] == int(focus_year)]
        if chunk.empty:
            continue
        chunk["hs4"] = chunk["product_hs92_code"].astype(str).str.zfill(4).str[:4]
        chunk = chunk[chunk["hs4"] == hs4]
        if chunk.empty:
            continue
        chunk["importer_iso"] = chunk["partner_iso3_code"].astype(str).str.upper().str.strip()
        chunk = chunk[chunk["importer_iso"].isin(importer_set)]
        if chunk.empty:
            continue
        chunk["exporter_iso"] = chunk["country_iso3_code"].astype(str).str.upper().str.strip()
        chunk = chunk[chunk["exporter_iso"].str.len() == 3]
        if chunk.empty:
            continue
        chunk["export_value"] = pd.to_numeric(chunk["export_value"], errors="coerce").fillna(0.0)
        grp = chunk.groupby("exporter_iso")["export_value"].sum()
        acc = grp.copy() if acc.empty else acc.add(grp, fill_value=0)

    if acc.empty:
        return pd.DataFrame(columns=["exporter_iso", "export_value", "export_value_m", "market_share"])

    out = (
        acc.rename("export_value")
        .reset_index()
        .sort_values("export_value", ascending=False)
        .reset_index(drop=True)
    )
    total_value = float(out["export_value"].sum())
    out["export_value_m"] = out["export_value"] / 1_000_000
    out["market_share"] = out["export_value"] / total_value if total_value > 0 else 0.0
    out["rank"] = np.arange(1, len(out) + 1)
    return out.head(int(top_n))[["rank", "exporter_iso", "export_value", "export_value_m", "market_share"]]


@st.cache_data(show_spinner=False)
def load_eff_num_exp() -> pd.DataFrame:
    path = _resolve_intermediate_csv("hs92_attributes.csv")
    df = pd.read_csv(path, usecols=["hs92", "eff_num_exp"])
    df["hs4"] = df["hs92"].astype(str).str.zfill(4)
    return df[["hs4", "eff_num_exp"]].drop_duplicates("hs4")


@st.cache_data(show_spinner=False)
def load_hs4_distance_attributes() -> pd.DataFrame:
    path = _resolve_intermediate_csv("hs92_attributes.csv")
    df = pd.read_csv(path, usecols=["hs92", "travelled_distance"])
    df["hs4"] = df["hs92"].astype(str).str.zfill(4)
    df["distance_travelled"] = pd.to_numeric(df["travelled_distance"], errors="coerce").fillna(0.0)
    return df[["hs4", "distance_travelled"]].drop_duplicates("hs4")


@st.cache_data(show_spinner=False)
def load_or_build_v1_hs4_metrics(valid_hs4: Iterable[str], year: int = 2024) -> pd.DataFrame:
    valid_hs4_set = set(str(x).zfill(4) for x in valid_hs4)
    primary_path = intermediate_dir() / V1_METRICS_FILE
    required_cols = {"accessible_market_growth_5y"}
    required_alignment_sets = [
        {"dai_percentile", "dai_lead"},
        {"alignment_weighted_percentile", "alignment_lead_weighted"},
    ]

    if primary_path.exists():
        m = pd.read_csv(primary_path)
        if "hs4" in m.columns:
            m["hs4"] = m["hs4"].astype(str).str.zfill(4)
            m = m[m["hs4"].isin(valid_hs4_set)].copy()
            cols = set(m.columns)
            has_alignment = any(req.issubset(cols) for req in required_alignment_sets)
            if not m.empty and required_cols.issubset(cols) and has_alignment:
                return m

    raise FileNotFoundError(
        "Missing precomputed V1 metrics for Ecuador dashboard. "
        f"Expected {primary_path.name}"
        + " in the app bundle data/intermediate folder."
    )


@st.cache_data(show_spinner=True)
def load_opportunity_dataset() -> pd.DataFrame:
    hs_ref = load_hs92_reference()
    valid_hs4 = hs_ref["hs4"].tolist()
    allowed_countries = load_rankings_countries(2024)

    complexity_path = _resolve_intermediate_csv("complexity_ecu_2024.csv")
    c = pd.read_csv(complexity_path)
    c["hs4"] = c["product"].astype(str).str.zfill(4)
    if "location" in c.columns:
        c = c[c["location"] == FOCUS_ISO]
    c = c[c["time"] == 2024]
    c["raw_rca"] = pd.to_numeric(c.get("rca", 0), errors="coerce").fillna(0.0)
    c["density_percentile"] = pd.to_numeric(c.get("density_percentile", 0), errors="coerce").fillna(0.0)
    if "rca_transformation" in c.columns:
        c["rca_transformed"] = pd.to_numeric(c["rca_transformation"], errors="coerce").fillna(0.0)
    elif "rca_transformed" in c.columns:
        c["rca_transformed"] = pd.to_numeric(c["rca_transformed"], errors="coerce").fillna(0.0)
    else:
        c["rca_transformed"] = c["raw_rca"]

    if "density_percentile" not in c.columns:
        c["density_percentile"] = 0.0

    c = c[["hs4", "raw_rca", "rca_transformed", "pci", "cog", "density", "density_percentile"]].drop_duplicates("hs4")
    metrics = load_or_build_v1_hs4_metrics(valid_hs4, year=2024)

    df = c.merge(hs_ref, on="hs4", how="left")
    df = df.merge(metrics, on="hs4", how="left")
    if "dai_percentile" not in df.columns and "alignment_weighted_percentile" in df.columns:
        df["dai_percentile"] = df["alignment_weighted_percentile"]
    if "dai_lead" not in df.columns and "alignment_lead_weighted" in df.columns:
        df["dai_lead"] = df["alignment_lead_weighted"]
    if "dai_index" not in df.columns:
        df["dai_index"] = 0.0
    df["alignment_weighted_percentile"] = pd.to_numeric(
        df.get("dai_percentile", df.get("alignment_weighted_percentile", 0.0)),
        errors="coerce",
    ).fillna(0.0)
    df["alignment_lead_weighted"] = pd.to_numeric(
        df.get("dai_lead", df.get("alignment_lead_weighted", 0.0)),
        errors="coerce",
    ).fillna(0.0)
    # Prefer RCA recomputed from trade shares for filtering/display as "raw RCA".
    if "raw_rca_trade" in df.columns:
        df["raw_rca"] = pd.to_numeric(df["raw_rca_trade"], errors="coerce").fillna(0.0)
    df = df.fillna(0)
    if "ecu_exporter_rank" in df.columns:
        df["ecu_exporter_rank"] = pd.to_numeric(df["ecu_exporter_rank"], errors="coerce")
        df.loc[df["ecu_exporter_rank"] <= 0, "ecu_exporter_rank"] = np.nan

    numeric_cols = [
        "rca_transformed",
        "raw_rca",
        "pci",
        "cog",
        "density",
        "density_percentile",
        "eff_num_exp",
        "distance_travelled",
        "dai_index",
        "dai_percentile",
        "dai_lead",
        "alignment_weighted_percentile",
        "market_growth_5y",
        "market_size_share",
        "accessible_market_size_share",
        "market_size",
        "accessible_market_size",
        "accessible_market_growth_5y",
        "accessible_market_to_market_ratio",
        "total_trade",
        "ecu_total_trade",
        "alignment_lead_unweighted",
        "alignment_lead_weighted",
    ]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["density_percentile"] = (
        pd.to_numeric(df["density_percentile"], errors="coerce")
        .replace([np.inf, -np.inf], 0.0)
        .fillna(0.0)
        .clip(lower=0.0)
    )

    # Keep min-max normalized values for views that need bounded scales (e.g., sizes/ranking views).
    for col in ["raw_rca", "rca_transformed", "density", "eff_num_exp", "distance_travelled", "dai_percentile", "pci", "cog", "market_growth_5y", "accessible_market_growth_5y", "market_size_share", "accessible_market_size_share"]:
        if col not in df.columns:
            df[col] = 0.0
        df[f"{col}_norm"] = normalize_0_1(df[col])

    # Use z-score normalization for feasibility/attractiveness index construction.
    for col in ["raw_rca", "rca_transformed", "density", "eff_num_exp", "distance_travelled", "dai_percentile", "pci", "cog", "market_growth_5y", "accessible_market_growth_5y", "market_size_share", "accessible_market_size_share"]:
        if col not in df.columns:
            df[col] = 0.0
        df[f"{col}_z"] = normalize_zscore(df[col])

    df["feasibility_index"] = df[
        ["rca_transformed_z", "density_z", "eff_num_exp_z", "dai_percentile_z"]
    ].mean(axis=1)
    df["attractiveness_index"] = df[
        ["pci_z", "cog_z", "accessible_market_growth_5y_z", "accessible_market_size_share_z"]
    ].mean(axis=1)
    df["combined_score"] = (df["feasibility_index"] + df["attractiveness_index"]) / 2
    df["accessible_market_size_b"] = pd.to_numeric(df["accessible_market_size"], errors="coerce").fillna(0.0) / 1_000_000_000
    df["market_size_b"] = pd.to_numeric(df["market_size"], errors="coerce").fillna(0.0) / 1_000_000_000
    df["total_trade_b"] = df["total_trade"] / 1_000_000_000
    df["ecu_total_trade_b"] = df["ecu_total_trade"] / 1_000_000_000
    return df
