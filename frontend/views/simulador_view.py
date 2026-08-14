import flet as ft
import os
import re
import json
import time
import threading
import datetime
import requests
import base64
import math
import asyncio
import csv
import subprocess
import tempfile
import shutil
import random
import calendar
import flet_video as fv
from frontend.components.ui import EmojiIconButton, EmojiDropdown

def _build_simulador_view(
    GROQ_API_KEY,
    GROQ_MODEL,
    URL_GROQ,
    autor,
    avatar_icon,
    call_gemini,
    cambiar_vista,
    color_borde,
    conectar_db,
    feedback,
    mostrar_snack,
    page,
    score,
    target_id,
    target_nombre,
    texto,
    tid,
    tnom,
    user_info,
    v_item,
    vendedores_list
):
    vendedor_dropdown = EmojiDropdown(
        label="Seleccionar Vendedor",
        border_color="#9D50BB",
        width=260,
        height=45
    )
    cliente_dropdown = EmojiDropdown(
        label="Perfil de Cliente",
        border_color="#9D50BB",
        width=260,
        height=45,
        options=[
            ft.dropdown.Option("Objeción de Precio - 'Son Muy Caros'", "Cliente insiste en que las gafas Sunglass Hut son muy caras y que vio unos lentes parecidos mucho más baratos en otro lugar"),
            ft.dropdown.Option("Duda Técnica - Polarizados y Chromance", "Cliente confundido preguntando qué ventaja real tienen las micas polarizadas y Chromance sobre las normales y por qué valen la pena"),
            ft.dropdown.Option("Consulta de Garantías - Ruptura o Robo", "Cliente interesado pero pregunta qué garantía tienen los lentes si sufren alguna ruptura, daño accidental o si se los roban"),
            ft.dropdown.Option("Cliente Indeciso - Ray-Ban Meta", "Cliente Indeciso buscando tecnología (Ray-Ban Meta)"),
            ft.dropdown.Option("Cliente Reclamando Cambio sin Ticket", "Cliente molesto que exige cambio de lentes Oakley sin ticket de compra"),
            ft.dropdown.Option("Cliente buscando Kit de Limpieza", "Cliente que solo entra preguntando por un paño de limpieza sencillo"),
            ft.dropdown.Option("Cliente de Regalo de Lujo", "Cliente indeciso buscando un regalo premium para su pareja (Gafas Versace)"),
            ft.dropdown.Option("Cliente Apurado - Gafas Polarizadas", "Cliente muy apurado que tiene un vuelo en pocas horas y busca unas gafas clásicas polarizadas (Ray-Ban Aviator) para la playa, exige rapidez y no quiere rodeos"),
            ft.dropdown.Option("Cliente Escéptico - Privacidad Meta", "Cliente desconfiado e interesado en la tecnología de las gafas inteligentes (Ray-Ban Meta), pero le preocupa mucho la privacidad y si la cámara o el micrófono graban de forma oculta"),
            ft.dropdown.Option("Coleccionista Exigente - Prada/Versace", "Cliente de alto nivel adquisitivo, muy conocedor de moda, que busca una pieza exclusiva de edición limitada de Prada o Versace y espera una atención ultra-premium y detalles de diseño"),
            ft.dropdown.Option("Cliente Comparador - Objeción de Precio", "Cliente indeciso que le encantan unas gafas Dolce & Gabbana, pero insiste en que las vio más baratas en una tienda en línea no autorizada y cuestiona el valor y autenticidad del producto en tienda física"),
            ft.dropdown.Option("Cliente de Descuento - Sin Temporada", "Cliente que insiste en obtener un descuento especial para comprar un solo par de gafas (Oakley o Ray-Ban) a pesar de que le explicas que no es temporada de rebajas ni hay promociones vigentes en tienda"),
            ft.dropdown.Option("Padre Indeciso - Regalo Adolescente", "Padre o madre de familia que busca un regalo de cumpleaños para su hijo adolescente, no sabe qué marca está de moda (Oakley o Ray-Ban Meta) y necesita asesoría paciente sobre tendencias juveniles"),
            ft.dropdown.Option("Deportista - Presupuesto Ajustado", "Deportista aficionado que busca gafas de sol de alto rendimiento para correr o ciclismo (Oakley Sutro), conoce los beneficios técnicos del lente pero tiene un presupuesto muy limitado y busca la opción de menor costo"),
            ft.dropdown.Option("Ejecutivo - Imagen Profesional", "Profesional corporativo que busca unas gafas elegantes y sobrias para usar con vestimenta formal de negocios (Persol o Prada), valora la discreción, calidad de materiales e imagen profesional"),
            ft.dropdown.Option("Cliente Reclamando Garantía - Lentes Rayados", "Cliente molesto que viene a exigir el cambio o garantía gratis de sus gafas porque los lentes están completamente rayados debido a mal uso (los limpió con su playera o los dejó caer), e insiste en que es defecto de fábrica")
        ]
    )
    
    chat_history = []
    sim_chat_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    user_input = ft.TextField(
        label="Escribe tu respuesta al cliente...",
        border_color="#9D50BB",
        color="white",
        expand=True,
        disabled=True,
        multiline=True,
        min_lines=1,
        max_lines=4,
        shift_enter=True
    )
    btn_enviar = ft.IconButton(
        icon=ft.Icons.SEND,
        icon_color="#00FFFF",
        disabled=True
    )
    
    vendedor_seleccionado_id = [None]
    perfil_cliente_txt = [""]
    
    def cargar_vendedores_dropdown():
        opciones = []
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT ID_Vendedor, Nombre_Completo FROM vendedores WHERE ID_Usuario_Tienda = %s AND Activo = 1 ORDER BY Nombre_Completo ASC", (user_info["id"],))
                rows = cursor.fetchall()
                db.close()
                if rows:
                    opciones = [ft.dropdown.Option(str(r["ID_Vendedor"]), r["Nombre_Completo"]) for r in rows]
        except Exception as ex:
            print("Error dropdown vendedores:", ex)
    
        # Si no hay vendedores en BD, cargar de vendedores_list o por defecto
        if not opciones:
            try:
                for idx, v_item in enumerate(vendedores_list, 1):
                    n_val = v_item["nombre"].value.strip() if hasattr(v_item["nombre"], "value") and v_item["nombre"].value else f"Vendedor {idx}"
                    opciones.append(ft.dropdown.Option(str(idx), n_val))
            except Exception:
                pass
        
        if not opciones:
            opciones = [
                ft.dropdown.Option("1", "JOHANA"),
                ft.dropdown.Option("2", "FERNANDO"),
                ft.dropdown.Option("3", "ARIADNA")
            ]
    
        vendedor_dropdown.options = opciones
    
    cargar_vendedores_dropdown()
    
    def agregar_mensaje_chat(autor, texto, avatar_icon, color_borde):
        sim_chat_column.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(avatar_icon, color=color_borde),
                    ft.Text(f"{autor}: {texto}", color="white", expand=True, selectable=True)
                ], spacing=10, vertical_alignment="start"),
                bgcolor="#141424" if autor == "Cliente" else "#111111",
                padding=10,
                border_radius=8,
                border=ft.Border.all(1, "#333333")
            )
        )
        page.update()
    
    def enviar_mensaje_simulacion(e):
        msg_txt = user_input.value.strip()
        if not msg_txt:
            return
        user_input.value = ""
        chat_history.append({"role": "user", "content": msg_txt})
        agregar_mensaje_chat("Vendedor", msg_txt, ft.Icons.PERSON, "#D8B4FE")
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_prompt = f"""Eres un cliente de Sunglass Hut. Tu perfil es: '{perfil_cliente_txt[0]}'.
        Estás interactuando con el asesor de ventas en la tienda física.
        Responde de forma natural, realista, breve y conversacional (máximo 2 a 3 oraciones por mensaje).
        No salgas del personaje. Si el vendedor te ofrece promociones, kits o garantías, reacciona según tu perfil de cliente.
        Mantén la interacción fluida. Si sientes que la atención es mala, sé difícil. Si es buena, muéstrate cooperativo.
        """
        
        mensajes_api = [{"role": "system", "content": system_prompt}]
        mensajes_api.extend(chat_history[-10:])
        
        payload = {
            "model": GROQ_MODEL,
            "messages": mensajes_api
        }
        
        try:
            res = requests.post(URL_GROQ, headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                ia_response = res.json()["choices"][0]["message"]["content"]
                chat_history.append({"role": "assistant", "content": ia_response})
                agregar_mensaje_chat("Cliente", ia_response, ft.Icons.SUPPORT_AGENT, "#00FFFF")
            else:
                agregar_mensaje_chat("Cliente", "[Error de comunicación con el simulador]", ft.Icons.ERROR, "red")
        except Exception as ex_sim:
            print("Error simulacion API:", ex_sim)
            agregar_mensaje_chat("Cliente", "[Error de conexión del simulador]", ft.Icons.ERROR, "red")
    
    btn_enviar.on_click = enviar_mensaje_simulacion
    
    def finalizar_simulacion_click(e):
        user_input.disabled = True
        btn_enviar.disabled = True
        btn_finalizar.disabled = True
        page.update()
        
        agregar_mensaje_chat("Sistema", "Analizando el desempeño de la simulación de venta. Por favor espera...", ft.Icons.INFO, "#00FFFF")
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        perfil_lower = perfil_cliente_txt[0].lower()
        es_caso_servicio = "cambio" in perfil_lower or "reclamando" in perfil_lower or "ticket" in perfil_lower
        
        if es_caso_servicio:
            eval_prompt = """Analiza la siguiente conversación de roleplay de servicio al cliente en Sunglass Hut entre un Asesor de Ventas (Vendedor) y un Cliente que viene a realizar un CAMBIO de producto sin ticket de compra o presenta una queja.
            Evalúa el desempeño del vendedor en base a estos puntos específicos de servicio al cliente:
            1. Trato al cliente (Amabilidad, escucha activa, templanza y empatía ante la molestia del cliente).
            2. Manejo de objeciones y políticas (¿Explicó claramente las políticas de devolución/cambios sin ticket y dio alternativas viables?).
            3. Búsqueda de soluciones y CRM (¿Ofreció buscar en el sistema de ventas con los datos del cliente, correo electrónico o ID de transacción?).
            4. Protocolo de atención ante conflictos (¿Evitó discutir y mantuvo una postura profesional y resolutiva?).
            5. Cierre formal del caso (¿Dejó claros los pasos a seguir o canalizó formalmente el caso a soporte/gerencia de forma educada?).
            
            NOTA IMPORTANTE: Al ser un caso de reclamación/servicio, NO penalices ni exijas venta cruzada (UPT) o el cierre de una venta comercial, ya que el objetivo principal es la atención post-venta y resolución de un problema operativo.
            
            Tu respuesta DEBE comenzar con un Score numérico entre 0 y 100 de la siguiente forma EXACTA:
            SCORE: [Número]
            [Salto de línea]
            Comentarios detallados de la evaluación...
            
            Sé riguroso y constructivo en tu retroalimentación en español.
            
            CONVERSACIÓN A EVALUAR:
            """
        else:
            eval_prompt = """Analiza la siguiente conversación de roleplay de venta en Sunglass Hut entre un Asesor de Ventas (Vendedor) y un Cliente.
            Evalúa el desempeño del vendedor en base a estos puntos:
            1. Trato al cliente (Amabilidad, escucha activa).
            2. Manejo de objeciones y conocimiento del producto.
            3. Venta cruzada (¿Ofreció kit de limpieza o estuche adicional para subir el UPT?).
            4. Captura de datos CRM para la garantía (¿Pidió el correo electrónico?).
            5. Cierre formal de la venta.
    
            Tu respuesta DEBE comenzar con un Score numérico entre 0 y 100 de la siguiente forma EXACTA:
            SCORE: [Número]
            [Salto de línea]
            Comentarios detallados de la evaluación...
            
            Sé riguroso y constructivo en tu retroalimentación en español.
            
            CONVERSACIÓN A EVALUAR:
            """
        
        for msg in chat_history:
            eval_prompt += f"
{msg['role'].upper()}: {msg['content']}"
        
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un auditor operativo experto en ventas y servicio premium de Sunglass Hut."},
                {"role": "user", "content": eval_prompt}
            ]
        }
        
        try:
            res = requests.post(URL_GROQ, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                eval_text = res.json()["choices"][0]["message"]["content"]
                
                score_val = 70
                match_score = re.search(r"SCORE:\s*(\d+)", eval_text, re.IGNORECASE)
                if match_score:
                    score_val = int(match_score.group(1))
                
                try:
                    v_id_val = int(vendedor_dropdown.value) if vendedor_dropdown.value and str(vendedor_dropdown.value).isdigit() else 1
                    db = conectar_db()
                    if db:
                        cursor = db.cursor()
                        cursor.execute("""
                            INSERT INTO evaluaciones_simulador (ID_Vendedor, Cliente_Simulado, Score_Evaluacion, Feedback_Detallado)
                            VALUES (%s, %s, %s, %s)
                        """, (v_id_val, cliente_dropdown.value, score_val, eval_text))
                        db.commit()
                        db.close()
                except Exception as ex_db_eval:
                    print("Error guardando eval en DB:", ex_db_eval)
                
                mostrar_evaluacion_dialog(score_val, eval_text)
            else:
                mostrar_snack("Error de conexión al evaluar", "red")
        except Exception as ex_eval:
            print("Error evaluacion:", ex_eval)
            mostrar_snack("Error al procesar la evaluación", "red")
    
    def mostrar_evaluacion_dialog(score, feedback):
        dlg = ft.AlertDialog(
            title=ft.Text(f"Evaluación del Simulador: Score {score}/100 📊", color="#00FFFF", weight="bold", size=18),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(feedback, color="white", size=13, selectable=True),
                ], scroll=ft.ScrollMode.AUTO),
                width=500,
                height=350
            ),
            actions=[
                ft.TextButton("Entendido", on_click=lambda e: (page.pop_dialog(), cambiar_vista("simulador")))
            ],
            bgcolor="#0F0F1A"
        )
        page.show_dialog(dlg)
        page.update()
    
    def iniciar_simulacion_click(e):
        if not vendedor_dropdown.value:
            mostrar_snack("Por favor selecciona un vendedor", "red")
            return
        if not cliente_dropdown.value:
            mostrar_snack("Por favor selecciona un perfil de cliente", "red")
            return
        
        v_val = vendedor_dropdown.value
        vendedor_seleccionado_id[0] = int(v_val) if v_val and str(v_val).isdigit() else 1
        perfil_cliente_txt[0] = cliente_dropdown.value
        
        chat_history.clear()
        sim_chat_column.controls.clear()
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        system_prompt = f"Eres un cliente de Sunglass Hut entrando a la tienda. Tu perfil es: '{perfil_cliente_txt[0]}'. Escribe tu primer saludo o consulta breve al asesor de ventas (vendedor)."
        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": system_prompt}]
        }
        
        try:
            res = requests.post(URL_GROQ, headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                first_msg = res.json()["choices"][0]["message"]["content"]
                chat_history.append({"role": "assistant", "content": first_msg})
                
                config_area.visible = False
                chat_area.visible = True
                user_input.disabled = False
                btn_enviar.disabled = False
                btn_finalizar.disabled = False
                
                agregar_mensaje_chat("Cliente", first_msg, ft.Icons.SUPPORT_AGENT, "#00FFFF")
            else:
                mostrar_snack("Error de conexión al iniciar simulación", "red")
        except Exception as ex_init:
            print("Error init sim:", ex_init)
            mostrar_snack("Error al iniciar el simulador", "red")
    
    btn_iniciar = ft.ElevatedButton(
        "Iniciar Roleplay ➕",
        on_click=iniciar_simulacion_click,
        bgcolor="#6E48AA",
        color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )
    btn_finalizar = ft.ElevatedButton(
        "Finalizar y Evaluar 📊",
        on_click=finalizar_simulacion_click,
        bgcolor="#FF4500",
        color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        disabled=True
    )
    
    config_area = ft.Column([
        ft.Row([vendedor_dropdown, cliente_dropdown], spacing=10, wrap=True),
        ft.Container(height=10),
        btn_iniciar
    ], visible=True)
    
    chat_area = ft.Column([
        sim_chat_column,
        ft.Row([user_input, btn_enviar], spacing=5),
        ft.Container(height=10),
        btn_finalizar
    ], visible=False, expand=True)
    
    eval_history_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def cargar_historial_evaluaciones():
        eval_history_column.controls.clear()
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT e.Score_Evaluacion, e.Cliente_Simulado, DATE_FORMAT(e.Fecha_Hora, '%d/%m/%Y %H:%i') as fecha_f, v.Nombre_Completo 
                    FROM evaluaciones_simulador e 
                    JOIN vendedores v ON e.ID_Vendedor = v.ID_Vendedor 
                    WHERE v.ID_Usuario_Tienda = %s 
                    ORDER BY e.Fecha_Hora DESC
                """, (user_info["id"],))
                rows = cursor.fetchall()
                db.close()
                
                if not rows:
                    eval_history_column.controls.append(ft.Text("No hay evaluaciones guardadas.", color="#888888", italic=True))
                else:
                    for r in rows:
                        eval_history_column.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.ASSESSMENT, color="#7CFC00" if r["Score_Evaluacion"] >= 80 else "#FF8C00"),
                                    ft.Column([
                                        ft.Text(f"Vendedor: {r['Nombre_Completo']} | Score: {r['Score_Evaluacion']}/100", color="white", weight="bold"),
                                        ft.Text(f"Perfil: {r['Cliente_Simulado']} | {r['fecha_f']}", color="#aaaaaa", size=11)
                                    ], spacing=3, expand=True)
                                ], vertical_alignment="center"),
                                bgcolor="#1a1a1a",
                                padding=10,
                                border_radius=8,
                                border=ft.Border.all(1, "#333333")
                            )
                        )
        except Exception as ex:
            print("Error historial eval:", ex)
        page.update()
    
    # --- PESTAÑA 3: GESTIÓN DE PERFILES DE CLIENTE (ADMIN Y TIENDA) ---
    perfiles_cards_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def init_perfiles_db():
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS perfiles_cliente_simulador (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        nombre VARCHAR(255) NOT NULL,
                        descripcion TEXT NOT NULL,
                        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                db.commit()
                
                cursor.execute("SELECT COUNT(*) FROM perfiles_cliente_simulador")
                res = cursor.fetchone()
                count = res[0] if res else 0
                if count == 0:
                    default_profiles = [
                        ("Objeción de Precio - 'Son Muy Caros'", "Cliente insiste en que las gafas Sunglass Hut son muy caras y que vio unos lentes parecidos mucho más baratos en otro lugar"),
                        ("Duda Técnica - Polarizados y Chromance", "Cliente confundido preguntando qué ventaja real tienen las micas polarizadas y Chromance sobre las normales y por qué valen la pena"),
                        ("Consulta de Garantías - Ruptura o Robo", "Cliente interesado pero pregunta qué garantía tienen los lentes si sufren alguna ruptura, daño accidental o si se los roban"),
                        ("Cliente Indeciso - Ray-Ban Meta", "Cliente Indeciso buscando tecnología (Ray-Ban Meta)"),
                        ("Cliente Reclamando Cambio sin Ticket", "Cliente molesto que exige cambio de lentes Oakley sin ticket de compra"),
                        ("Cliente buscando Kit de Limpieza", "Cliente que solo entra preguntando por un paño de limpieza sencillo"),
                        ("Cliente de Regalo de Lujo", "Cliente indeciso buscando un regalo premium para su pareja (Gafas Versace)"),
                        ("Cliente Apurado - Gafas Polarizadas", "Cliente muy apurado que tiene un vuelo en pocas horas y busca unas gafas clásicas polarizadas (Ray-Ban Aviator) para la playa, exige rapidez y no quiere rodeos"),
                        ("Cliente Escéptico - Privacidad Meta", "Cliente desconfiado e interesado en la tecnología de las gafas inteligentes (Ray-Ban Meta), pero le preocupa mucho la privacidad y si la cámara o el micrófono graban de forma oculta"),
                        ("Coleccionista Exigente - Prada/Versace", "Cliente de alto nivel adquisitivo, muy conocedor de moda, que busca una pieza exclusiva de edición limitada de Prada o Versace y espera una atención ultra-premium y detalles de diseño"),
                        ("Cliente Comparador - Objeción de Precio", "Cliente indeciso que le encantan unas gafas Dolce & Gabbana, pero insiste en que las vio más baratas en una tienda en línea no autorizada y cuestiona el valor y autenticidad del producto en tienda física"),
                        ("Cliente de Descuento - Sin Temporada", "Cliente que insiste en obtener un descuento especial para comprar un solo par de gafas (Oakley o Ray-Ban) a pesar de que le explicas que no es temporada de rebajas ni hay promociones vigentes en tienda"),
                        ("Padre Indeciso - Regalo Adolescente", "Padre o madre de familia que busca un regalo de cumpleaños para su hijo adolescente, no sabe qué marca está de moda (Oakley o Ray-Ban Meta) y necesita asesoría paciente sobre tendencias juveniles"),
                        ("Deportista - Presupuesto Ajustado", "Deportista aficionado que busca gafas de sol de alto rendimiento para correr o ciclismo (Oakley Sutro), conoce los beneficios técnicos del lente pero tiene un presupuesto muy limitado y busca la opción de menor costo"),
                        ("Ejecutivo - Imagen Profesional", "Profesional corporativo que busca unas gafas elegantes y sobrias para usar con vestimenta formal de negocios (Persol o Prada), valora la discreción, calidad de materiales e imagen profesional"),
                        ("Cliente Reclamando Garantía - Lentes Rayados", "Cliente molesto que viene a exigir el cambio o garantía gratis de sus gafas porque los lentes están completamente rayados debido a mal uso (los limpió con su playera o los dejó caer), e insiste en que es defecto de fábrica")
                    ]
                    cursor.executemany("INSERT INTO perfiles_cliente_simulador (nombre, descripcion) VALUES (%s, %s)", default_profiles)
                    db.commit()
                db.close()
        except Exception as ex_init:
            print("Error init perfiles_db:", ex_init)
    
    def cargar_perfiles_simulador():
        perfiles_cards_container.controls.clear()
        dropdown_options = []
        init_perfiles_db()
        
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT id, nombre, descripcion FROM perfiles_cliente_simulador ORDER BY id DESC")
                rows = cursor.fetchall()
                db.close()
                
                for row in rows:
                    p_id = row["id"]
                    p_nombre = row["nombre"]
                    p_desc = row["descripcion"]
                    
                    dropdown_options.append(ft.dropdown.Option(p_nombre, f"{p_nombre} - {p_desc[:60]}..."))
                    
                    def eliminar_perfil_click(target_id=p_id, target_nombre=p_nombre):
                        def confirmar_eliminar(e):
                            try:
                                db_del = conectar_db()
                                if db_del:
                                    cursor_del = db_del.cursor()
                                    cursor_del.execute("DELETE FROM perfiles_cliente_simulador WHERE id = %s", (target_id,))
                                    db_del.commit()
                                    db_del.close()
                                    mostrar_snack(f"Perfil '{target_nombre}' eliminado.", color="#7CFC00")
                                    page.pop_dialog()
                                    cargar_perfiles_simulador()
                            except Exception as ex_d:
                                print("Error eliminar perfil:", ex_d)
                                mostrar_snack("Error al eliminar el perfil.", color="red")
                        
                        dlg_confirm = ft.AlertDialog(
                            title=ft.Text("Confirmar eliminación 🗑️", color="#FF4500", weight="bold"),
                            content=ft.Text(f"¿Estás seguro de eliminar el perfil '{target_nombre}'?", color="white"),
                            actions=[
                                ft.TextButton("Cancelar", on_click=lambda e: page.pop_dialog()),
                                ft.ElevatedButton("Eliminar", on_click=confirmar_eliminar, bgcolor="#FF4500", color="white")
                            ],
                            bgcolor="#0F0F1A"
                        )
                        page.show_dialog(dlg_confirm)
                        page.update()
                    
                    btn_del = ft.IconButton(
                        icon=ft.Icons.DELETE_ROUNDED,
                        icon_color="#FF4500",
                        tooltip="Eliminar Perfil",
                        on_click=lambda e, tid=p_id, tnom=p_nombre: eliminar_perfil_click(tid, tnom)
                    )
                    
                    card = ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, color="#00FFFF", size=36),
                            ft.Column([
                                ft.Text(p_nombre, color="white", weight="bold", size=14),
                                ft.Text(p_desc, color="#aaaaaa", size=12, selectable=True)
                            ], spacing=3, expand=True),
                            btn_del
                        ], vertical_alignment="center", spacing=12),
                        bgcolor="#1E1E2E",
                        padding=15,
                        border_radius=10,
                        border=ft.Border.all(1, "#9D50BB")
                    )
                    perfiles_cards_container.controls.append(card)
        except Exception as ex_p:
            print("Error cargando perfiles:", ex_p)
    
        if dropdown_options:
            cliente_dropdown.options = dropdown_options
        page.update()
    
    def abrir_modal_nuevo_perfil(e):
        input_nombre = ft.TextField(label="Tipo / Nombre del Cliente", hint_text="Ej. Cliente Exigente - Ray-Ban Reverse", border_color="#9D50BB", color="white")
        input_desc = ft.TextField(label="Descripción / Personalidad / Objeción", hint_text="Ej. Busca tecnología exclusiva y compara precios...", multiline=True, min_lines=2, max_lines=4, border_color="#9D50BB", color="white")
        
        def guardar_perfil(e):
            nom = input_nombre.value.strip()
            desc = input_desc.value.strip()
            if not nom or not desc:
                mostrar_snack("Por favor llena el nombre y la descripción.", "red")
                return
            try:
                db_ins = conectar_db()
                if db_ins:
                    cursor_ins = db_ins.cursor()
                    cursor_ins.execute("INSERT INTO perfiles_cliente_simulador (nombre, descripcion) VALUES (%s, %s)", (nom, desc))
                    db_ins.commit()
                    db_ins.close()
                    mostrar_snack("¡Nuevo perfil de cliente guardado exitosamente!", "#7CFC00")
                    page.pop_dialog()
                    cargar_perfiles_simulador()
            except Exception as ex_g:
                print("Error al guardar perfil:", ex_g)
                mostrar_snack("Error al guardar en la base de datos.", "red")
    
        dlg_add = ft.AlertDialog(
            title=ft.Text("➕ Agregar Perfil de Cliente", color="#D8B4FE", weight="bold"),
            content=ft.Container(
                content=ft.Column([
                    input_nombre,
                    input_desc
                ], spacing=12),
                width=450,
                height=200
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton("Guardar Perfil", on_click=guardar_perfil, bgcolor="#1f6f43", color="white")
            ],
            bgcolor="#0F0F1A"
        )
        page.show_dialog(dlg_add)
        page.update()
    
    def generar_perfil_con_ia(e):
        mostrar_snack("🤖 Generando nuevo perfil de cliente con IA... Por favor espera.", "#00FFFF")
        
        def thread_generar_ia():
            try:
                prompt = """Crea un perfil de cliente realista para entrenamiento de ventas en una tienda de gafas de sol Sunglass Hut (Ray-Ban, Oakley, Versace, Prada, Persol, Oliver Peoples).
    El perfil debe incluir:
    1. Un nombre o título corto del tipo de cliente (ej. "Cliente Ejecutivo - Imagen Corporativa Persol", "Influencer de Moda - Prada Exclusivo").
    2. Una descripción detallada del comportamiento, objeción de ventas, dudas técnicas o de garantía.
    
    Responde ÚNICAMENTE en formato JSON plano con las llaves exactas "nombre" y "descripcion".
    Ejemplo:
    {"nombre": "Cliente Exigente - Edición Limitada Versace", "descripcion": "Busca una pieza exclusiva para un evento social importante y le preocupa la autenticidad y el grabado del estuche."}
    """
                raw_res = call_gemini(prompt)
                if not raw_res:
                    mostrar_snack("No se pudo conectar con la IA de Gemini.", "red")
                    return
                
                import json, re
                clean_str = raw_res.strip()
                if "```json" in clean_str:
                    clean_str = clean_str.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_str:
                    clean_str = clean_str.split("```")[1].split("```")[0].strip()
                
                match = re.search(r'\{.*\}', clean_str, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    g_nom = data.get("nombre", "Cliente generado por IA")
                    g_desc = data.get("descripcion", "Perfil generado automáticamente por IA.")
                    
                    db_ia = conectar_db()
                    if db_ia:
                        cursor_ia = db_ia.cursor()
                        cursor_ia.execute("INSERT INTO perfiles_cliente_simulador (nombre, descripcion) VALUES (%s, %s)", (g_nom, g_desc))
                        db_ia.commit()
                        db_ia.close()
                        mostrar_snack(f"✨ ¡Perfil '{g_nom}' generado por IA!", "#7CFC00")
                        cargar_perfiles_simulador()
                else:
                    mostrar_snack("Respuesta de IA recibida. Actualizando lista...", "#7CFC00")
                    cargar_perfiles_simulador()
            except Exception as ex_ia:
                print("Error generando perfil IA:", ex_ia)
                mostrar_snack("Error al generar perfil con IA.", "red")
    
        threading.Thread(target=thread_generar_ia, daemon=True).start()
    
    btn_add_manual = ft.ElevatedButton(
        "➕ Agregar Perfil",
        on_click=abrir_modal_nuevo_perfil,
        bgcolor="#1f6f43",
        color="white"
    )
    
    btn_gen_ia = ft.ElevatedButton(
        "🤖 Generar con IA",
        on_click=generar_perfil_con_ia,
        bgcolor="#9D50BB",
        color="white"
    )
    
    btn_refresh_perfiles = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color="#00FFFF",
        tooltip="Refrescar Lista",
        on_click=lambda e: cargar_perfiles_simulador()
    )
    
    tab_simulacion = ft.Column([config_area, chat_area], expand=True)
    tab_historial = ft.Column([
        ft.Text("Historial de Evaluaciones de la Tienda:", color="#D8B4FE", size=14, weight="bold"),
        ft.ElevatedButton("Actualizar Historial 🔄", on_click=lambda e: cargar_historial_evaluaciones(), bgcolor="#333333", color="white"),
        ft.Container(height=5),
        eval_history_column
    ], expand=True)
    
    tab_perfiles = ft.Column([
        ft.Row([
            ft.Text("👥 GESTIÓN DE PERFILES DE CLIENTE", color="#D8B4FE", size=15, weight="bold"),
            ft.Container(expand=True),
            btn_add_manual,
            btn_gen_ia,
            btn_refresh_perfiles
        ], vertical_alignment="center", spacing=10),
        ft.Text("Administra o crea nuevos tipos de cliente para los ejercicios de ventas. Puedes agregarlos manualmente o generarlos dinámicamente con IA.", color="#aaaaaa", size=12),
        ft.Divider(height=15, color="#333333"),
        perfiles_cards_container
    ], expand=True)
    
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        length=3,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Iniciar Simulador"),
                        ft.Tab(label="Historial de Avance"),
                        ft.Tab(label="Gestión de Perfiles 👥")
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        tab_simulacion,
                        tab_historial,
                        tab_perfiles
                    ]
                )
            ]
        )
    )
    
    cargar_historial_evaluaciones()
    cargar_perfiles_simulador()
    
    return ft.Column([
        ft.Row([
            ft.Text("Simulador de Ventas con IA 🎭", size=24, color="#D8B4FE", weight="bold")
        ]),
        ft.Text("Realiza roleplay interactivo de ventas por vendedor. La IA auditará el cumplimiento de las metas de UPT, captura de datos y cierre.", color="#aaaaaa", size=13),
        ft.Divider(height=15, color="#333333"),
        tabs
    ], expand=True)