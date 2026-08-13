import os
import base64
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def auditar_foto_con_gemini(guia_bytes, tienda_bytes, instrucciones):
    if not GEMINI_API_KEY:
        return "CORREGIR: La API Key de Gemini no está configurada."
        
    try:
        guia_b64 = base64.b64encode(guia_bytes).decode('utf-8')
        tienda_b64 = base64.b64encode(tienda_bytes).decode('utf-8')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        prompt = (
            "Actúa como un auditor visual de campañas de exhibición en Sunglass Hut. "
            "Se te proporcionan dos imágenes:\n"
            "1. La FOTO GUÍA (primera imagen): Es la referencia oficial de cómo debe quedar el montaje.\n"
            "2. La FOTO DE LA TIENDA (segunda imagen): Es el montaje real realizado por la tienda.\n\n"
            f"INSTRUCCIONES DE MONTAJE A VALIDAR:\n{instrucciones}\n\n"
            "Compara la foto de la tienda con la foto guía y con las instrucciones. "
            "Debes identificar si hay elementos faltantes, publicidad errónea, banners mal alineados, "
            "gafas en repisas incorrectas o diferencias significativas.\n"
            "Responde de forma clara, directa y en español.\n"
            "REGLA DE RESPUESTA CRÍTICA:\n"
            "- Si el montaje es correcto y cumple las instrucciones, empieza tu respuesta EXACTAMENTE con 'APROBADO'. Puedes añadir comentarios positivos después.\n"
            "- Si hay errores o diferencias que corregir, empieza tu respuesta EXACTAMENTE con 'CORREGIR' y proporciona una lista numerada con los puntos específicos que se deben solucionar en la tienda."
        )
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inlineData": {"mimeType": "image/jpeg", "data": guia_b64}},
                        {"inlineData": {"mimeType": "image/jpeg", "data": tienda_b64}}
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.2}
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "Error: No se recibió texto de la IA.")
            return f"Error: Respuesta de Gemini inesperada."
        else:
            return f"Error en la API de Gemini: Código {response.status_code}"
    except Exception as e:
        return f"Error de conexión con Gemini: {str(e)}"

def procesar_ticket_con_gemini(imagen_bytes):
    import io
    from PIL import Image
    import numpy as np

    ocr_text = ""
    # Simplified EasyOCR for backend (Assuming we install it or skip and fallback to Gemini)
    try:
        import easyocr
        reader = easyocr.Reader(['es','en'])
        img = Image.open(io.BytesIO(imagen_bytes))
        if img.mode != 'RGB': img = img.convert('RGB')
        max_dim = 1280
        if img.width > max_dim or img.height > max_dim: img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        img_np = np.array(img)
        results = reader.readtext(img_np, detail=0)
        ocr_text = "\n".join(results)
    except Exception as ex_ocr:
        pass

    if not ocr_text.strip():
        if GEMINI_API_KEY:
            try:
                img_b64 = base64.b64encode(imagen_bytes).decode('utf-8')
                prompt = (
                    "Actúa como un sistema OCR inteligente de escaneo de tickets de compra de tiendas de lentes / retail.\n"
                    "Analiza detalladamente la imagen del ticket proporcionado y extrae los datos principales.\n"
                    "Responde ÚNICAMENTE en formato JSON válido con claves exactas: transaccion, fecha_compra, nombre_cliente, vendedor, upc, precio, notas, items."
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": "image/jpeg", "data": img_b64}}]}],
                    "generationConfig": {"temperature": 0.1}
                }
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
                res = requests.post(url, json=payload, timeout=20)
                if res.status_code == 200:
                    cand = res.json().get("candidates", [])
                    if cand:
                        parts = cand[0].get("content", {}).get("parts", [])
                        if parts:
                            clean_text = parts[0].get("text", "").replace("```json", "").replace("```", "").strip()
                            return json.loads(clean_text), None
            except Exception: pass
        return None, "No se pudo extraer texto legible de la imagen del ticket."

    try:
        prompt = (
            "Actúa como un estructurador JSON de tickets de compra de tiendas de lentes / retail.\n"
            f"--- TEXTO OCR DEL TICKET ---\n{ocr_text}\n-----------------------------\n\n"
            "Analiza el texto y extrae todos los datos que logres identificar en formato JSON válido."
        )
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=25)
        if res.status_code == 200:
            out_str = res.json()["choices"][0]["message"]["content"]
            clean_str = out_str.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_str)
            return parsed, None
        else:
            return None, f"Respuesta Groq OCR ({res.status_code}): No se completó la lectura."
    except Exception as ex_groq:
        return None, f"Error al estructurar ticket con OCR: {str(ex_groq)}"
