# ============================================================
# MÓDULO DE AUTOSINCRONIZACIÓN AUTOMÁTICA DE USUARIOS DE TIENDA
# ============================================================
import json

SGH_USERS_MASTER = [
  {
    "Usuario": "sgh3488",
    "Contrasena": "$2b$12$koNf/Fk6iHQ./toj3PsZ/Op1vlWCqizGuqrqXV7tYTaPlnxag2gBS",
    "Nombre_Completo": "Tienda Atizapán (3488)",
    "Rol": "Gerente",
    "Tienda": "Atizapán",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9277",
    "Contrasena": "$2b$12$4yoURomJjCBe6LK9/KOkLOwp/0ihA/6fgoyVdqPZknIlFwDidkfIW",
    "Nombre_Completo": "Tienda Ampliación Interlomas (9277)",
    "Rol": "Gerente",
    "Tienda": "Ampliación Interlomas",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3502",
    "Contrasena": "$2b$12$DZyHBiciy0xRDNFk0vGILuLHKQ0pE7nBoryT1xDLMR3BtwNxdHeWq",
    "Nombre_Completo": "Tienda Interlomas (3502)",
    "Rol": "Gerente",
    "Tienda": "Interlomas",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3586",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Punta Norte 1 (3586)",
    "Rol": "Gerente",
    "Tienda": "Punta Norte 1",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5256",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Punta Norte 2 (5256)",
    "Rol": "Gerente",
    "Tienda": "Punta Norte 2",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3583",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Satélite (3583)",
    "Rol": "Gerente",
    "Tienda": "Satélite",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3507",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Lindavista (3507)",
    "Rol": "Gerente",
    "Tienda": "Lindavista",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8839",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Fortuna (8839)",
    "Rol": "Gerente",
    "Tienda": "Fortuna",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3645",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Vallejo (3645)",
    "Rol": "Gerente",
    "Tienda": "Vallejo",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3019",
    "Contrasena": "$2b$12$SWcBya369EQkvJD.Ta91tuX3wDbgLO053N62oiU1iZ/wY1sTd15X6",
    "Nombre_Completo": "Tienda Toreo (3019)",
    "Rol": "Gerente",
    "Tienda": "Toreo",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sghc964",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Explanada Pachuca (c964)",
    "Rol": "Gerente",
    "Tienda": "Explanada Pachuca",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sghq382",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Parque Tepeyac (q382)",
    "Rol": "Gerente",
    "Tienda": "Parque Tepeyac",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3542",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Galerías Pachuca (3542)",
    "Rol": "Gerente",
    "Tienda": "Galerías Pachuca",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3519",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Santa Fe (3519)",
    "Rol": "Gerente",
    "Tienda": "Santa Fe",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9539",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda Town Square Metepec (9539)",
    "Rol": "Gerente",
    "Tienda": "Town Square Metepec",
    "Segmento": "SGH",
    "Zona": "Zona Centro",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5208",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AICM T1A (5208)",
    "Rol": "Gerente",
    "Tienda": "AICM T1A",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5215",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AICM T1D (5215)",
    "Rol": "Gerente",
    "Tienda": "AICM T1D",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5378",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AICM T1F (5378)",
    "Rol": "Gerente",
    "Tienda": "AICM T1F",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5379",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AICM T2A (5379)",
    "Rol": "Gerente",
    "Tienda": "AICM T2A",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5385",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AICM T2B (5385)",
    "Rol": "Gerente",
    "Tienda": "AICM T2B",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5399",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AICM T2D (5399)",
    "Rol": "Gerente",
    "Tienda": "AICM T2D",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh25977",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AIFA (25977)",
    "Rol": "Gerente",
    "Tienda": "AIFA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8829",
    "Contrasena": "$2b$12$vlFESCjh0BUDexcoL94KB.8fwABKe92umiQ.KUUnsXyKB2k6zrPDe",
    "Nombre_Completo": "Tienda ANTEA (8829)",
    "Rol": "Gerente",
    "Tienda": "ANTEA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh10615",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ENCUENTRO OCEANIA (10615)",
    "Rol": "Gerente",
    "Tienda": "ENCUENTRO OCEANIA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8885",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LA VICTORIA (8885)",
    "Rol": "Gerente",
    "Tienda": "LA VICTORIA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3508",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda P DELTA 1 (3508)",
    "Rol": "Gerente",
    "Tienda": "P DELTA 1",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9507",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PASEO QRO (9507)",
    "Rol": "Gerente",
    "Tienda": "PASEO QRO",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9563",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda QRO PREM OUTLET (9563)",
    "Rol": "Gerente",
    "Tienda": "QRO PREM OUTLET",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3487",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda QRO1 (3487)",
    "Rol": "Gerente",
    "Tienda": "QRO1",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3584",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SAN MIGUEL 1 (3584)",
    "Rol": "Gerente",
    "Tienda": "SAN MIGUEL 1",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2383",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TEZONTLE 2 (2383)",
    "Rol": "Gerente",
    "Tienda": "TEZONTLE 2",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3506",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda 222 A (3506)",
    "Rol": "Gerente",
    "Tienda": "222 A",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh7049",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ANTARA (7049)",
    "Rol": "Gerente",
    "Tienda": "ANTARA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9344",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ANTENAS (9344)",
    "Rol": "Gerente",
    "Tienda": "ANTENAS",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9603",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ANTENAS 2 (9603)",
    "Rol": "Gerente",
    "Tienda": "ANTENAS 2",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3574",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GAL TOL (3574)",
    "Rol": "Gerente",
    "Tienda": "GAL TOL",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh26246",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GAL METEPEC AMP (26246)",
    "Rol": "Gerente",
    "Tienda": "GAL METEPEC AMP",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2561",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LERMA OUTLET (2561)",
    "Rol": "Gerente",
    "Tienda": "LERMA OUTLET",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3516",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LERMA OUTLET 2 (3516)",
    "Rol": "Gerente",
    "Tienda": "LERMA OUTLET 2",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8474",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MASARYK (8474)",
    "Rol": "Gerente",
    "Tienda": "MASARYK",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3557",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda METEPEC 1 (3557)",
    "Rol": "Gerente",
    "Tienda": "METEPEC 1",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3500",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SAMARA (3500)",
    "Rol": "Gerente",
    "Tienda": "SAMARA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3585",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda STA FE 2 (3585)",
    "Rol": "Gerente",
    "Tienda": "STA FE 2",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3150",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ACA3 (3150)",
    "Rol": "Gerente",
    "Tienda": "ACA3",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh4018",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ANGELOPOLIS (4018)",
    "Rol": "Gerente",
    "Tienda": "ANGELOPOLIS",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9006",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AVERANDA (9006)",
    "Rol": "Gerente",
    "Tienda": "AVERANDA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9428",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda EXPLANADA PUEBLA (9428)",
    "Rol": "Gerente",
    "Tienda": "EXPLANADA PUEBLA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8691",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda FORUM CUERNAVACA (8691)",
    "Rol": "Gerente",
    "Tienda": "FORUM CUERNAVACA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9054",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MANACAR (9054)",
    "Rol": "Gerente",
    "Tienda": "MANACAR",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3028",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda OASIS COY (3028)",
    "Rol": "Gerente",
    "Tienda": "OASIS COY",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9063",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PASEO ACOXPA (9063)",
    "Rol": "Gerente",
    "Tienda": "PASEO ACOXPA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9116",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PASEO ZIHUATANEJO (9116)",
    "Rol": "Gerente",
    "Tienda": "PASEO ZIHUATANEJO",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh4040",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PERISUR (4040)",
    "Rol": "Gerente",
    "Tienda": "PERISUR",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh4066",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PUEBLA OUTLET (4066)",
    "Rol": "Gerente",
    "Tienda": "PUEBLA OUTLET",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9342",
    "Contrasena": "$2b$12$wGpHz4cteRvQptHOkVzSY.gx2Sq3GlJvyLMY5f/jPYHIfUnNI3jkm",
    "Nombre_Completo": "Tienda SOLARA PUEBLA (9342)",
    "Rol": "Gerente",
    "Tienda": "SOLARA PUEBLA",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5238",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ZIHUATANEJO T1 (5238)",
    "Rol": "Gerente",
    "Tienda": "ZIHUATANEJO T1",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh7060",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY ESFERA (7060)",
    "Rol": "Gerente",
    "Tienda": "MTY ESFERA",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8686",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY FASHION DRIVE (8686)",
    "Rol": "Gerente",
    "Tienda": "MTY FASHION DRIVE",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3169",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY1 (3169)",
    "Rol": "Gerente",
    "Tienda": "MTY1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3511",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY11 (3511)",
    "Rol": "Gerente",
    "Tienda": "MTY11",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3170",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY2 (3170)",
    "Rol": "Gerente",
    "Tienda": "MTY2",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3178",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY4 (3178)",
    "Rol": "Gerente",
    "Tienda": "MTY4",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3181",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY7 (3181)",
    "Rol": "Gerente",
    "Tienda": "MTY7",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh27405",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAZA SAN LUIS SOLARIS (27405)",
    "Rol": "Gerente",
    "Tienda": "PLAZA SAN LUIS SOLARIS",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9537",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PUNTO VALLE (9537)",
    "Rol": "Gerente",
    "Tienda": "PUNTO VALLE",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9536",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PUNTO VALLE KIOSCO (9536)",
    "Rol": "Gerente",
    "Tienda": "PUNTO VALLE KIOSCO",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8902",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SALTILLO 1 (8902)",
    "Rol": "Gerente",
    "Tienda": "SALTILLO 1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9506",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SLP AERO (9506)",
    "Rol": "Gerente",
    "Tienda": "SLP AERO",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh25164",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SLP PARK (25164)",
    "Rol": "Gerente",
    "Tienda": "SLP PARK",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3617",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SLP1 (3617)",
    "Rol": "Gerente",
    "Tienda": "SLP1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3582",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SLP2 (3582)",
    "Rol": "Gerente",
    "Tienda": "SLP2",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3504",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TOR1 (3504)",
    "Rol": "Gerente",
    "Tienda": "TOR1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3051",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CDJ (3051)",
    "Rol": "Gerente",
    "Tienda": "CDJ",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2902",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CDJ T1 (2902)",
    "Rol": "Gerente",
    "Tienda": "CDJ T1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2903",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CHI T1 (2903)",
    "Rol": "Gerente",
    "Tienda": "CHI T1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3154",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CHI1 (3154)",
    "Rol": "Gerente",
    "Tienda": "CHI1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3155",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CHI2 (3155)",
    "Rol": "Gerente",
    "Tienda": "CHI2",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh7061",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY LA FE (7061)",
    "Rol": "Gerente",
    "Tienda": "MTY LA FE",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8897",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY OUTLET (8897)",
    "Rol": "Gerente",
    "Tienda": "MTY OUTLET",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3287",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY TA (3287)",
    "Rol": "Gerente",
    "Tienda": "MTY TA",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3567",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY TA2 (3567)",
    "Rol": "Gerente",
    "Tienda": "MTY TA2",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh25163",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY TA3 (25163)",
    "Rol": "Gerente",
    "Tienda": "MTY TA3",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3289",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY TB (3289)",
    "Rol": "Gerente",
    "Tienda": "MTY TB",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3296",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY TC (3296)",
    "Rol": "Gerente",
    "Tienda": "MTY TC",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3179",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY5 (3179)",
    "Rol": "Gerente",
    "Tienda": "MTY5",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3180",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY6 (3180)",
    "Rol": "Gerente",
    "Tienda": "MTY6",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5006",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY8 (5006)",
    "Rol": "Gerente",
    "Tienda": "MTY8",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3523",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MTY9 (3523)",
    "Rol": "Gerente",
    "Tienda": "MTY9",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9343",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PASEO CHIHUAHUA (9343)",
    "Rol": "Gerente",
    "Tienda": "PASEO CHIHUAHUA",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9056",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PASEO DURANGO (9056)",
    "Rol": "Gerente",
    "Tienda": "PASEO DURANGO",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9345",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ALAMEDA TIJ (9345)",
    "Rol": "Gerente",
    "Tienda": "ALAMEDA TIJ",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh26369",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ANDENES HMO (26369)",
    "Rol": "Gerente",
    "Tienda": "ANDENES HMO",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8491",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ENSENADA (8491)",
    "Rol": "Gerente",
    "Tienda": "ENSENADA",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3347",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda HMO T1 (3347)",
    "Rol": "Gerente",
    "Tienda": "HMO T1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3491",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda HMO1 (3491)",
    "Rol": "Gerente",
    "Tienda": "HMO1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh25858",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LANDMARK TIJUANA (25858)",
    "Rol": "Gerente",
    "Tienda": "LANDMARK TIJUANA",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh4862",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MEXICALI T1 (4862)",
    "Rol": "Gerente",
    "Tienda": "MEXICALI T1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8820",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda NOGALES (8820)",
    "Rol": "Gerente",
    "Tienda": "NOGALES",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh15610",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PENINSULA TIJ (15610)",
    "Rol": "Gerente",
    "Tienda": "PENINSULA TIJ",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh26153",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SN PEDRO MEXICALI (26153)",
    "Rol": "Gerente",
    "Tienda": "SN PEDRO MEXICALI",
    "Segmento": "SGH",
    "Zona": "ZONA CENTRO",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5080",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TIJ (5080)",
    "Rol": "Gerente",
    "Tienda": "TIJ",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh7062",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TIJ 2 (7062)",
    "Rol": "Gerente",
    "Tienda": "TIJ 2",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2905",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TIJ T1A (2905)",
    "Rol": "Gerente",
    "Tienda": "TIJ T1A",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8845",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TIJ T1C (8845)",
    "Rol": "Gerente",
    "Tienda": "TIJ T1C",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3196",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ACLN (3196)",
    "Rol": "Gerente",
    "Tienda": "ACLN",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh26503",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ANIMA CABOS (26503)",
    "Rol": "Gerente",
    "Tienda": "ANIMA CABOS",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5352",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CABO T1 (5352)",
    "Rol": "Gerente",
    "Tienda": "CABO T1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3203",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CABO1 (3203)",
    "Rol": "Gerente",
    "Tienda": "CABO1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3204",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CABO2 (3204)",
    "Rol": "Gerente",
    "Tienda": "CABO2",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3206",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CABO3 (3206)",
    "Rol": "Gerente",
    "Tienda": "CABO3",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh7048",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CABO4 (7048)",
    "Rol": "Gerente",
    "Tienda": "CABO4",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3009",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CLN FORUM (3009)",
    "Rol": "Gerente",
    "Tienda": "CLN FORUM",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3138",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CLN FORUM 2 (3138)",
    "Rol": "Gerente",
    "Tienda": "CLN FORUM 2",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2726",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GAL MAZ (2726)",
    "Rol": "Gerente",
    "Tienda": "GAL MAZ",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh25237",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LA CEIBA (25237)",
    "Rol": "Gerente",
    "Tienda": "LA CEIBA",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8881",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LA PAZ CENTRO (8881)",
    "Rol": "Gerente",
    "Tienda": "LA PAZ CENTRO",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh7051",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LA PAZ T1 (7051)",
    "Rol": "Gerente",
    "Tienda": "LA PAZ T1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9279",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LOS MOCHIS (9279)",
    "Rol": "Gerente",
    "Tienda": "LOS MOCHIS",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3201",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MAZ T1 (3201)",
    "Rol": "Gerente",
    "Tienda": "MAZ T1",
    "Segmento": "SGH",
    "Zona": "ZONA NORTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5638",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AGS (5638)",
    "Rol": "Gerente",
    "Tienda": "AGS",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh10955",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ALTACIA LEON (10955)",
    "Rol": "Gerente",
    "Tienda": "ALTACIA LEON",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5107",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CIBELES (5107)",
    "Rol": "Gerente",
    "Tienda": "CIBELES",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5112",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LEON MEDIANA (5112)",
    "Rol": "Gerente",
    "Tienda": "LEON MEDIANA",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5632",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LEON GDE (5632)",
    "Rol": "Gerente",
    "Tienda": "LEON GDE",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3200",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LEON OUTLET (3200)",
    "Rol": "Gerente",
    "Tienda": "LEON OUTLET",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3456",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LEON T1 (3456)",
    "Rol": "Gerente",
    "Tienda": "LEON T1",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5610",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MOR ALTOZANO (5610)",
    "Rol": "Gerente",
    "Tienda": "MOR ALTOZANO",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh10876",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MOR AME KIOSKO (10876)",
    "Rol": "Gerente",
    "Tienda": "MOR AME KIOSKO",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh15364",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MOR AMERICAS (15364)",
    "Rol": "Gerente",
    "Tienda": "MOR AMERICAS",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8784",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MOR T1 (8784)",
    "Rol": "Gerente",
    "Tienda": "MOR T1",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9393",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAZA CIBELES (9393)",
    "Rol": "Gerente",
    "Tienda": "PLAZA CIBELES",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3911",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SALAMANCA (3911)",
    "Rol": "Gerente",
    "Tienda": "SALAMANCA",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3238",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda URUAPAN (3238)",
    "Rol": "Gerente",
    "Tienda": "URUAPAN",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3518",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ZAC1 (3518)",
    "Rol": "Gerente",
    "Tienda": "ZAC1",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3151",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AND2 (3151)",
    "Rol": "Gerente",
    "Tienda": "AND2",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3260",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AND3 (3260)",
    "Rol": "Gerente",
    "Tienda": "AND3",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3010",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda APVR (3010)",
    "Rol": "Gerente",
    "Tienda": "APVR",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3259",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GG STZA (3259)",
    "Rol": "Gerente",
    "Tienda": "GG STZA",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3160",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GG4 (3160)",
    "Rol": "Gerente",
    "Tienda": "GG4",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3770",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GG5 (3770)",
    "Rol": "Gerente",
    "Tienda": "GG5",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3162",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GP3 (3162)",
    "Rol": "Gerente",
    "Tienda": "GP3",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8692",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LA ISLA PVR (8692)",
    "Rol": "Gerente",
    "Tienda": "LA ISLA PVR",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9562",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LANDMARK GDL (9562)",
    "Rol": "Gerente",
    "Tienda": "LANDMARK GDL",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9176",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MALECON VALLARTA (9176)",
    "Rol": "Gerente",
    "Tienda": "MALECON VALLARTA",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3035",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PVR GAL (3035)",
    "Rol": "Gerente",
    "Tienda": "PVR GAL",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3348",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PVR T1 (3348)",
    "Rol": "Gerente",
    "Tienda": "PVR T1",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8604",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda SENTURA ZAMORA (8604)",
    "Rol": "Gerente",
    "Tienda": "SENTURA ZAMORA",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3049",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AGDL T1A (3049)",
    "Rol": "Gerente",
    "Tienda": "AGDL T1A",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3067",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AGDL T1B (3067)",
    "Rol": "Gerente",
    "Tienda": "AGDL T1B",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2719",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AGDL T1D (2719)",
    "Rol": "Gerente",
    "Tienda": "AGDL T1D",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9037",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AGDL T2A (9037)",
    "Rol": "Gerente",
    "Tienda": "AGDL T2A",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9253",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AGDL T2B (9253)",
    "Rol": "Gerente",
    "Tienda": "AGDL T2B",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9341",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AGDL T2C (9341)",
    "Rol": "Gerente",
    "Tienda": "AGDL T2C",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3464",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda COL1 (3464)",
    "Rol": "Gerente",
    "Tienda": "COL1",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8838",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda FORUM TEPIC (8838)",
    "Rol": "Gerente",
    "Tienda": "FORUM TEPIC",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh14499",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GAL SANTA ANITA (14499)",
    "Rol": "Gerente",
    "Tienda": "GAL SANTA ANITA",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3280",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GDL FORUM (3280)",
    "Rol": "Gerente",
    "Tienda": "GDL FORUM",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3497",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GDL FORUM 2 (3497)",
    "Rol": "Gerente",
    "Tienda": "GDL FORUM 2",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2529",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GDL OUTLET (2529)",
    "Rol": "Gerente",
    "Tienda": "GDL OUTLET",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9593",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MIDTOWN JALISCO (9593)",
    "Rol": "Gerente",
    "Tienda": "MIDTOWN JALISCO",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8882",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAZA PATRIA (8882)",
    "Rol": "Gerente",
    "Tienda": "PLAZA PATRIA",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3080",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PP KIOSCO (3080)",
    "Rol": "Gerente",
    "Tienda": "PP KIOSCO",
    "Segmento": "SGH",
    "Zona": "ZONA OCCIDENTE",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5078",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN FBO (5078)",
    "Rol": "Gerente",
    "Tienda": "CUN FBO",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2875",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T2A (2875)",
    "Rol": "Gerente",
    "Tienda": "CUN T2A",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2876",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T2B (2876)",
    "Rol": "Gerente",
    "Tienda": "CUN T2B",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2877",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T2C (2877)",
    "Rol": "Gerente",
    "Tienda": "CUN T2C",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2878",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T2D (2878)",
    "Rol": "Gerente",
    "Tienda": "CUN T2D",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh7058",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T2E (7058)",
    "Rol": "Gerente",
    "Tienda": "CUN T2E",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2879",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T3A (2879)",
    "Rol": "Gerente",
    "Tienda": "CUN T3A",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2880",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T3B (2880)",
    "Rol": "Gerente",
    "Tienda": "CUN T3B",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8992",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T3C (8992)",
    "Rol": "Gerente",
    "Tienda": "CUN T3C",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9184",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T4A (9184)",
    "Rol": "Gerente",
    "Tienda": "CUN T4A",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9183",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T4B (9183)",
    "Rol": "Gerente",
    "Tienda": "CUN T4B",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh12943",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN T4C (12943)",
    "Rol": "Gerente",
    "Tienda": "CUN T4C",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8471",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN OUTLET (8471)",
    "Rol": "Gerente",
    "Tienda": "CUN OUTLET",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5207",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN1 (5207)",
    "Rol": "Gerente",
    "Tienda": "CUN1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3290",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN2 (3290)",
    "Rol": "Gerente",
    "Tienda": "CUN2",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3295",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN3 (3295)",
    "Rol": "Gerente",
    "Tienda": "CUN3",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3556",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN5 (3556)",
    "Rol": "Gerente",
    "Tienda": "CUN5",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3600",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CUN6 (3600)",
    "Rol": "Gerente",
    "Tienda": "CUN6",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh10540",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LA ISLA CUN 2 (10540)",
    "Rol": "Gerente",
    "Tienda": "LA ISLA CUN 2",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh25859",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda OUTLET RIVERA MAYA (25859)",
    "Rol": "Gerente",
    "Tienda": "OUTLET RIVERA MAYA",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8851",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PUERTO CANCUN (8851)",
    "Rol": "Gerente",
    "Tienda": "PUERTO CANCUN",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh25245",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TULUM KAPEN HA (25245)",
    "Rol": "Gerente",
    "Tienda": "TULUM KAPEN HA",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh15536",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ALTAMA TAMPICO (15536)",
    "Rol": "Gerente",
    "Tienda": "ALTAMA TAMPICO",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2281",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AMERICAS VER (2281)",
    "Rol": "Gerente",
    "Tienda": "AMERICAS VER",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9602",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AMERICAS XALAPA (9602)",
    "Rol": "Gerente",
    "Tienda": "AMERICAS XALAPA",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh4222",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda ANDAMAR VER (4222)",
    "Rol": "Gerente",
    "Tienda": "ANDAMAR VER",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3526",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda COATZA 1 (3526)",
    "Rol": "Gerente",
    "Tienda": "COATZA 1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2882",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda HUA T1 (2882)",
    "Rol": "Gerente",
    "Tienda": "HUA T1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8823",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda HUATULCO BAHIAS (8823)",
    "Rol": "Gerente",
    "Tienda": "HUATULCO BAHIAS",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2885",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda OAX T1 (2885)",
    "Rol": "Gerente",
    "Tienda": "OAX T1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8822",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda OAXACA VALLE (8822)",
    "Rol": "Gerente",
    "Tienda": "OAXACA VALLE",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2887",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda VER T1 (2887)",
    "Rol": "Gerente",
    "Tienda": "VER T1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh4849",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda VER T1B (4849)",
    "Rol": "Gerente",
    "Tienda": "VER T1B",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9095",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda AMBAR TUXTLA (9095)",
    "Rol": "Gerente",
    "Tienda": "AMBAR TUXTLA",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3754",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CAMPECHE (3754)",
    "Rol": "Gerente",
    "Tienda": "CAMPECHE",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3482",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CD CAR 1 (3482)",
    "Rol": "Gerente",
    "Tienda": "CD CAR 1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh10637",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda GAL MERIDA (10637)",
    "Rol": "Gerente",
    "Tienda": "GAL MERIDA",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9551",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda HARBOR MERIDA (9551)",
    "Rol": "Gerente",
    "Tienda": "HARBOR MERIDA",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh26558",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LA ISLA MER 2 (26558)",
    "Rol": "Gerente",
    "Tienda": "LA ISLA MER 2",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh9191",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda LA ISLA MERIDA (9191)",
    "Rol": "Gerente",
    "Tienda": "LA ISLA MERIDA",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2883",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MER T1 (2883)",
    "Rol": "Gerente",
    "Tienda": "MER T1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3164",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MER1 (3164)",
    "Rol": "Gerente",
    "Tienda": "MER1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3167",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda MER4 (3167)",
    "Rol": "Gerente",
    "Tienda": "MER4",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5079",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TAB (5079)",
    "Rol": "Gerente",
    "Tienda": "TAB",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2886",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TAB T1 (2886)",
    "Rol": "Gerente",
    "Tienda": "TAB T1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3282",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda TAB2 (3282)",
    "Rol": "Gerente",
    "Tienda": "TAB2",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2881",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda CZM T1 (2881)",
    "Rol": "Gerente",
    "Tienda": "CZM T1",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2945",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAYA 10 (2945)",
    "Rol": "Gerente",
    "Tienda": "PLAYA 10",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5205",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAYA 16 (5205)",
    "Rol": "Gerente",
    "Tienda": "PLAYA 16",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh3625",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAYA AME (3625)",
    "Rol": "Gerente",
    "Tienda": "PLAYA AME",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5081",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAYA CH (5081)",
    "Rol": "Gerente",
    "Tienda": "PLAYA CH",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5342",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAYA CORAZON (5342)",
    "Rol": "Gerente",
    "Tienda": "PLAYA CORAZON",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh2900",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAYA PASEO (2900)",
    "Rol": "Gerente",
    "Tienda": "PLAYA PASEO",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh5203",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PLAYA ZOLAR (5203)",
    "Rol": "Gerente",
    "Tienda": "PLAYA ZOLAR",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  },
  {
    "Usuario": "sgh8983",
    "Contrasena": "sgh12345",
    "Nombre_Completo": "Tienda PUNTA LANGOSTA (8983)",
    "Rol": "Gerente",
    "Tienda": "PUNTA LANGOSTA",
    "Segmento": "SGH",
    "Zona": "ZONA SUR",
    "Puesto": "Gerente de Tienda"
  }
]

def sincronizar_usuarios_db(db):
    try:
        if not db: return
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT LOWER(TRIM(Usuario)) as u FROM usuarios")
        existing = set(r["u"] for r in cursor.fetchall() if r.get("u"))
        
        n_inserted = 0
        for u_data in SGH_USERS_MASTER:
            u_key = u_data["Usuario"].lower().strip()
            if u_key not in existing:
                cursor.execute("""
                    INSERT INTO usuarios 
                    (Usuario, Contrasena, Nombre_Completo, Rol, Tienda, Segmento, Zona, Puesto)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    u_data["Usuario"],
                    u_data["Contrasena"],
                    u_data["Nombre_Completo"],
                    u_data["Rol"],
                    u_data["Tienda"],
                    u_data.get("Segmento", "SGH"),
                    u_data.get("Zona", "ZONA CENTRO"),
                    u_data.get("Puesto", "Gerente de Tienda")
                ))
                n_inserted += 1
                existing.add(u_key)
        
        if n_inserted > 0:
            db.commit()
            print(f"✅ Auto-Sincronización DB: Se insertaron {n_inserted} usuarios de tiendas faltantes en la BD de Producción.")
        else:
            print(f"✅ Auto-Sincronización DB: Los {len(SGH_USERS_MASTER)} usuarios de tiendas ya están presentes en la BD.")
    except Exception as ex:
        print("Notice auto_sync_usuarios:", ex)
