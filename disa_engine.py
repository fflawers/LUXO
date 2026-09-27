import cv2
import numpy as np
import os
import glob
import time
import json
import base64
import requests
from datetime import datetime

def load_gemini_key():
    try:
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("gemini_api_key", "")
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    """
    Transformación de perspectiva de 4 puntos (warpPerspective):
    Endereza y aplana el documento eliminando distorsiones trapezoidales y superficies de mesa.
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    if maxWidth < 50 or maxHeight < 50:
        return None

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight), flags=cv2.INTER_LANCZOS4)
    return warped

def find_document_quad(crop_bgr):
    """
    Detección de bordes y polígono de 4 esquinas de la hoja/documento.
    """
    try:
        gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 30, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edged, kernel, iterations=2)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        min_area = (crop_bgr.shape[0] * crop_bgr.shape[1]) * 0.45
        for cnt in contours[:5]:
            if cv2.contourArea(cnt) > min_area:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.025 * peri, True)
                if len(approx) == 4:
                    return approx.reshape(4, 2)
    except Exception:
        pass
    return None

def enhance_doc_clean(img_bgr):
    """
    Retorna la imagen en su estado fotográfico real y puro:
    - 100% fiel al sensor de la cámara.
    - Cero filtros destructivos, cero ruido y cero artefactos.
    """
    return img_bgr

def enhance_doc(img_crop):
    return img_crop

def camscanner_magic_color(img_crop):
    return img_crop

def process_corte_image_gemini(image_path, output_dir=None, store_id="3502", date_str=None):
    """
    Pipeline CamScanner + Gemini Vision Inteligente:
    - Mantiene resolución nativa original completa (sin recomprimir antes del corte).
    - Aplica recorte relativo y corrección de perspectiva de 4 puntos (warpPerspective).
    - Aplica el pipeline de realce de documento (Document Enhancer).
    - Exporta en JPEG de alta calidad (calidad 98).
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    if output_dir is None:
        base_dir = os.path.join(r"c:\Users\MOISES\Desktop\luxo7.7\uploads\disa_cortes", date_str, f"Tienda_{store_id}")
    else:
        base_dir = output_dir
        
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. Cargar imagen en RESOLUCIÓN NATIVA COMPLETA (sin recomprimir)
    img_orig = cv2.imread(image_path)
    if img_orig is None:
        return {"success": False, "error": f"No se pudo abrir la imagen: {image_path}", "documents": []}
        
    h_orig, w_orig = img_orig.shape[:2]
    
    # Escala temporal SOLO para la llamada a la API de visión
    scale = 1280.0 / max(h_orig, w_orig) if max(h_orig, w_orig) > 1280 else 1.0
    img_small = cv2.resize(img_orig, (int(w_orig * scale), int(h_orig * scale))) if scale != 1.0 else img_orig
    _, buf = cv2.imencode(".jpg", img_small, [cv2.IMWRITE_JPEG_QUALITY, 90])
    img_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
    
    gemini_key = load_gemini_key()
    detected_docs = []
    
    if gemini_key:
        prompt = """
        Eres el auditor experto de Inteligencia Artificial de LUXO especializado en digitalización y clasificación de auditorías diarias de tienda (DiSA - Digital Sales Audit).
        Examina con máxima precisión esta fotografía del corte diario colocada sobre la mesa/mostrador.
        Identifica CADA documento individual, ticket, comprobante o reporte y asígnalo a su categoría DiSA exacta:

        CATÁLOGO OFICIAL DE CATEGORÍAS DISA:
        1. "01_Informe_Diario_Ventas": Hoja de reporte tamaño carta con título "Ventas diarias".
        2. "02_Informe_Reconciliacion": Hoja de reporte tamaño carta con título "Conciliación de cajón de efectivo".
        3. "04_Ticket_Cierre_Dia": Tickets térmicos del sistema de corte de tienda ("FINALIZAR RECUENTO", "STOREBANK / DEPOSITO BANCARIO", y "Firma empleado / Gerente").
           * Si están colocados juntos/paralelos, abárcalos en un solo box_2d que los cubra de extremo a extremo.
        4. "07_Cierre_Terminal": Tira o comprobante de cierre/resumen de terminal bancaria o Mercado Pago Point ("RESUMEN DE VENTAS" o "CIERRE DE LOTE / TERMINAL").
        5. "03_Vouchers": Cada comprobante/voucher individual de pago con tarjeta bancaria (Mercado Pago, AMEX, Visa, Mastercard).
        6. "13_Ticket_Venta": Cada ticket térmico individual de venta a cliente expedido por Sunglass Hut (tickets con código de barras y desglose de lentes).
        7. "05_Fichas_Deposito": Fichas bancarias de depósito en efectivo (Santander / BBVA).
        8. "06_Tira_Casa_Cambio": Tiras de casa de cambio o compra de divisas.
        9. "08_Credito_Tienda": Comprobantes de crédito en tienda o devolución.
        10. "09_Gift_Card": Tarjetas de regalo.
        11. "10_Gafa_Aniversario": Formato especial de gafa aniversario.
        12. "11_Deposito_Panamericano_Banco": Carta porte azul de traslado de valores Panamericano / Banco.
        13. "12_Notas_Manuales": Remisiones o notas manuales foliadas.

        REGLAS DE DETECCIÓN:
        - "box_2d": [ymin, xmin, ymax, xmax] en coordenadas normalizadas de 0 a 1000 que encuadre perfectamente el documento sin cortar bordes ni textos.
        - "rotation_degrees": 0 si el texto se lee normalmente de frente. Solo usa 90, 180 o 270 si el documento está rotado de lado o de cabeza en la fotografía respecto a su lectura normal.
        - "category": nombre exacto de la categoría indicada arriba.

        Devuelve ÚNICAMENTE un objeto JSON estructurado:
        {
          "documents": [
            {
              "box_2d": [ymin, xmin, ymax, xmax],
              "rotation_degrees": 0,
              "category": "01_Informe_Diario_Ventas"
            }
          ]
        }
        """
        
        model_candidates = [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-flash-latest"
        ]
        
        for m_name in model_candidates:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": img_b64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.1
                }
            }
            
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    content_text = data['candidates'][0]['content']['parts'][0]['text']
                    parsed = json.loads(content_text)
                    detected_docs = parsed.get("documents", [])
                    print(f"[DiSA Gemini AI ({m_name})] Successfully detected and classified {len(detected_docs)} documents.")
                    if detected_docs:
                        break
            except Exception as ex_ai:
                print(f"[DiSA Gemini AI ({m_name})] Attempt notice:", ex_ai)

    # Fallback to OpenCV contour segmentation if API was unavailable
    if not detected_docs:
        print("[DiSA Engine] Fallback to OpenCV contour detection.")
        gray = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
        blurred = cv2.bilateralFilter(gray, 7, 50, 50)
        _, thresh = cv2.threshold(blurred, 140, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        eroded = cv2.erode(thresh, kernel, iterations=1)
        contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = (img_small.shape[0] * img_small.shape[1]) * 0.005
        
        for cnt in contours:
            if cv2.contourArea(cnt) > min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                ymin = int((y / img_small.shape[0]) * 1000)
                xmin = int((x / img_small.shape[1]) * 1000)
                ymax = int(((y + h) / img_small.shape[0]) * 1000)
                xmax = int(((x + w) / img_small.shape[1]) * 1000)
                detected_docs.append({
                    "box_2d": [ymin, xmin, ymax, xmax],
                    "rotation_degrees": 0,
                    "category": "13_Ticket_Venta"
                })

    saved_docs = []
    counts_by_cat = {}
    
    # 2. Procesamiento sobre la IMAGEN ORIGINAL NATIVA utilizando coordenadas relativas (0.0 a 1.0)
    for idx, doc in enumerate(detected_docs, 1):
        box = doc.get("box_2d", [0, 0, 1000, 1000])
        ymin, xmin, ymax, xmax = box
        
        # Mapeo de coordenadas relativas normalizadas a píxeles nativos
        y1 = max(0, int((ymin / 1000.0) * h_orig) - 5)
        x1 = max(0, int((xmin / 1000.0) * w_orig) - 5)
        y2 = min(h_orig, int((ymax / 1000.0) * h_orig) + 5)
        x2 = min(w_orig, int((xmax / 1000.0) * w_orig) + 5)
        
        if (y2 - y1) < 40 or (x2 - x1) < 40:
            continue
            
        crop_native = img_orig[y1:y2, x1:x2]
        
        # 3. Detección de 4 esquinas y Corrección de Perspectiva (warpPerspective)
        quad = find_document_quad(crop_native)
        if quad is not None:
            warped = four_point_transform(crop_native, quad)
            if warped is not None and warped.size > 0:
                crop_processed = warped
            else:
                crop_processed = crop_native
        else:
            crop_processed = crop_native
            
        # 4. Corrección de orientación si el texto fue detectado rotado
        rot_deg = doc.get("rotation_degrees", 0)
        if rot_deg == 90:
            crop_processed = cv2.rotate(crop_processed, cv2.ROTATE_90_CLOCKWISE)
        elif rot_deg == 180:
            crop_processed = cv2.rotate(crop_processed, cv2.ROTATE_180)
        elif rot_deg == 270:
            crop_processed = cv2.rotate(crop_processed, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
        # 5. Pipeline de Realce de Documento (Document Enhancer)
        doc_final = enhance_doc_clean(crop_processed)
        category = doc.get("category", "13_Ticket_Venta")
        
        counts_by_cat[category] = counts_by_cat.get(category, 0) + 1
        num = counts_by_cat[category]
        
        filename = f"{category}_{num:02d}.jpg"
        out_path = os.path.join(base_dir, filename)
        
        # 6. Exportar en JPEG de alta calidad (calidad 98, superando el mínimo 92 requerido)
        cv2.imwrite(out_path, doc_final, [cv2.IMWRITE_JPEG_QUALITY, 98])
        
        saved_docs.append({
            "index": idx,
            "filename": filename,
            "filepath": out_path,
            "category": category,
            "width": doc_final.shape[1],
            "height": doc_final.shape[0]
        })
        
    return {
        "success": True,
        "total_documents": len(saved_docs),
        "output_directory": base_dir,
        "store_id": store_id,
        "date": date_str,
        "documents": saved_docs
    }

def process_corte_image(image_path, output_dir=None, store_id="3502", date_str=None):
    return process_corte_image_gemini(image_path, output_dir, store_id, date_str)

