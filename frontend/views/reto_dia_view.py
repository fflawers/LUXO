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

def _build_reto_dia_view(
    cambiar_vista,
    conectar_db,
    correcta_txt,
    el,
    elegida_txt,
    enviar_mensaje,
    id_manual_ref,
    id_pregunta,
    idm,
    input_msg,
    ip,
    letra,
    manual_forzado_trivia,
    mostrar_snack,
    opcion_elegida,
    page,
    pregunta_txt,
    res_obj,
    texto_opcion,
    user_info
):
    reto_container = ft.Container(padding=10, expand=True)
    
    def preguntar_a_luxo_pregunta(pregunta_txt, elegida_txt, correcta_txt, id_manual_ref=None):
        manual_forzado_trivia[0] = id_manual_ref
        input_msg.value = f"Hola LUXO, tengo una duda sobre la pregunta de trivia: '{pregunta_txt}'. Respondí '{elegida_txt}' pero la correcta era '{correcta_txt}'. ¿Me explicas en qué manual se basa y por qué es la correcta?"
        cambiar_vista("chat")
        page.update()
        enviar_mensaje(None)
    
    # Variables de estado del juego de Trivia (Persistidas por sesión de Flet/Vista)
    estado_trivia = {
        "preguntas": [],         # Las 5 preguntas elegidas
        "indice": 0,             # Índice actual (0 a 4)
        "respuestas": {},        # Registro de respuestas: {id_pregunta: {'elegida': X, 'correcta': Y, 'es_correcta': Z}}
        "iniciada": False,       # ¿Está jugando?
        "terminada": False,      # ¿Llegó al final?
        "retro_mostrada": False  # ¿Mostrando retroalimentación después de contestar una pregunta?
    }
    
    def iniciar_nueva_partida():
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                # Obtener 3 preguntas fáciles aleatorias
                cursor.execute("SELECT * FROM reto_preguntas WHERE Dificultad = 'Fácil' ORDER BY RAND() LIMIT 3")
                faciles = cursor.fetchall()
                # Obtener 2 preguntas difíciles aleatorias
                cursor.execute("SELECT * FROM reto_preguntas WHERE Dificultad = 'Difícil' ORDER BY RAND() LIMIT 2")
                dificiles = cursor.fetchall()
                
                preguntas_seleccionadas = faciles + dificiles
                
                # Si no hay suficientes por dificultad, rellenar con cualquier pregunta
                if len(preguntas_seleccionadas) < 5:
                    ids_existentes = [p["ID_Pregunta"] for p in preguntas_seleccionadas]
                    if ids_existentes:
                        format_strings = ','.join(['%s'] * len(ids_existentes))
                        cursor.execute(f"SELECT * FROM reto_preguntas WHERE ID_Pregunta NOT IN ({format_strings}) ORDER BY RAND() LIMIT %s", (*ids_existentes, 5 - len(preguntas_seleccionadas)))
                    else:
                        cursor.execute("SELECT * FROM reto_preguntas ORDER BY RAND() LIMIT 5")
                    preguntas_seleccionadas += cursor.fetchall()
                
                db.close()
                
                # Mezclar un poco para que no salgan siempre primero las fáciles
                import random
                random.shuffle(preguntas_seleccionadas)
                
                estado_trivia["preguntas"] = preguntas_seleccionadas[:5]
                estado_trivia["indice"] = 0
                estado_trivia["respuestas"] = {}
                estado_trivia["iniciada"] = True
                estado_trivia["terminada"] = False
                estado_trivia["retro_mostrada"] = False
                
                dibujar_ui()
        except Exception as ex:
            print("Error al iniciar partida de trivia:", ex)
            mostrar_snack(f"Error al iniciar la Trivia: {ex}", color="red")
    
    def registrar_respuesta_pregunta(id_pregunta, opcion_elegida):
        try:
            pregunta_actual = estado_trivia["preguntas"][estado_trivia["indice"]]
            correcta = pregunta_actual["Respuesta_Correcta"]
            es_correcta = (opcion_elegida == correcta)
            
            # Guardar en base de datos para estadísticas históricas del perfil
            db = conectar_db()
            if db:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO reto_respuestas_usuario (ID_Usuario, ID_Pregunta, Fecha_Respuesta, Respuesta_Elegida, Es_Correcta)
                    VALUES (%s, %s, CURDATE(), %s, %s)
                    ON DUPLICATE KEY UPDATE Respuesta_Elegida = %s, Es_Correcta = %s
                """, (user_info["id"], id_pregunta, opcion_elegida, 1 if es_correcta else 0, opcion_elegida, 1 if es_correcta else 0))
                db.commit()
                db.close()
            
            # Registrar en el estado local de la partida
            estado_trivia["respuestas"][id_pregunta] = {
                "pregunta": pregunta_actual["Pregunta"],
                "elegida": opcion_elegida,
                "correcta": correcta,
                "es_correcta": es_correcta,
                "explicacion": pregunta_actual["Explicacion"] or "Sin explicación.",
                "opcion_a": pregunta_actual["Opcion_A"],
                "opcion_b": pregunta_actual["Opcion_B"],
                "opcion_c": pregunta_actual["Opcion_C"],
                "opcion_d": pregunta_actual["Opcion_D"],
                "id_manual": pregunta_actual.get("ID_Manual")
            }
            
            estado_trivia["retro_mostrada"] = True
            dibujar_ui()
        except Exception as ex:
            print("Error al registrar respuesta de pregunta:", ex)
            mostrar_snack("Error al procesar tu respuesta.", color="red")
    
    def avanzar_pregunta():
        if estado_trivia["indice"] >= 4:
            estado_trivia["iniciada"] = False
            estado_trivia["terminada"] = True
        else:
            estado_trivia["indice"] += 1
            estado_trivia["retro_mostrada"] = False
        dibujar_ui()
    
    def dibujar_ui():
        reto_container.content = None
        
        # ----------------- CASO 1: VISTA DE BIENVENIDA (Partida no iniciada) -----------------
        if not estado_trivia["iniciada"] and not estado_trivia["terminada"]:
            # Cargar estadísticas generales históricas de la base de datos
            total_contestados = 0
            total_correctos = 0
            precision = 0
            
            try:
                db = conectar_db()
                if db:
                    cursor = db.cursor(dictionary=True)
                    cursor.execute("SELECT COUNT(*) as cant FROM reto_respuestas_usuario WHERE ID_Usuario = %s", (user_info["id"],))
                    total_contestados = cursor.fetchone()["cant"]
                    cursor.execute("SELECT COUNT(*) as cant FROM reto_respuestas_usuario WHERE ID_Usuario = %s AND Es_Correcta = 1", (user_info["id"],))
                    total_correctos = cursor.fetchone()["cant"]
                    db.close()
                    if total_contestados > 0:
                        precision = int((total_correctos / total_contestados) * 100)
            except Exception as ex:
                print("Error obteniendo estadísticas históricas de trivia:", ex)
    
            stats_box = ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Text("🏆", size=16),
                        ft.Text(f"Respondidos: {total_contestados}", color="white", size=12, weight="bold")
                    ], spacing=5),
                    ft.Row([
                        ft.Text("✅", size=16),
                        ft.Text(f"Correctos: {total_correctos}", color="white", size=12, weight="bold")
                    ], spacing=5),
                    ft.Row([
                        ft.Text("📈", size=16),
                        ft.Text(f"Precisión: {precision}%", color="white", size=12, weight="bold")
                    ], spacing=5)
                ], alignment="spaceAround", wrap=True),
                bgcolor="#0F0F1A",
                padding=12,
                border_radius=8,
                border=ft.Border.all(1, "#222222")
            )
    
            reto_container.content = ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("🧠", size=48),
                        ft.Text("Desafío de Trivia LUXO", size=20, color="white", weight="bold"),
                        ft.Text(
                            "Pon a prueba tus conocimientos sobre los manuales de Sunglass Hut. "
                            "El juego consta de un cuestionario de 5 preguntas consecutivas compuestas por preguntas fáciles y difíciles. "
                            "¡Completa el reto con puntaje perfecto para obtener la insignia de Auditor Estrella!",
                            color="#aaaaaa",
                            size=13,
                            text_align="center"
                        ),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "Comenzar Reto 🏆",
                            on_click=lambda e: iniciar_nueva_partida(),
                            bgcolor="#6E48AA",
                            color="white",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=18
                            )
                        )
                    ], horizontal_alignment="center", spacing=10),
                    bgcolor="#1e1e2e",
                    padding=30,
                    border_radius=12,
                    border=ft.Border.all(1.5, "#D8B4FE"),
                    alignment=ft.alignment.Alignment(0, 0)
                ),
                ft.Container(height=10),
                ft.Text("Tu Historial Acumulado:", color="#aaaaaa", size=12, weight="bold"),
                stats_box
            ], spacing=10, scroll=ft.ScrollMode.AUTO)
    
        # ----------------- CASO 2: VISTA DE PREGUNTA EN CURSO -----------------
        elif estado_trivia["iniciada"] and not estado_trivia["terminada"]:
            idx = estado_trivia["indice"]
            pregunta = estado_trivia["preguntas"][idx]
            id_preg = pregunta["ID_Pregunta"]
            dificultad = pregunta.get("Dificultad", "Fácil")
            
            # Color del indicador de dificultad
            color_dif = "#00FF7F" if dificultad == "Fácil" else "#FF1493"
            
            # Barra de progreso
            progress_value = (idx + 1) / 5
            
            opciones_controles = []
            if not estado_trivia["retro_mostrada"]:
                # Modo juego (esperando respuesta)
                for letra, texto_opcion in [
                    ("A", pregunta["Opcion_A"]),
                    ("B", pregunta["Opcion_B"]),
                    ("C", pregunta["Opcion_C"]),
                    ("D", pregunta["Opcion_D"])
                ]:
                    def make_click_handler(l=letra, ip=id_preg):
                        return lambda e: registrar_respuesta_pregunta(ip, l)
                        
                    opciones_controles.append(
                        ft.Container(
                            content=ft.ElevatedButton(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Text(letra, color="black", weight="bold", size=12),
                                        bgcolor="#D8B4FE",
                                        width=24,
                                        height=24,
                                        border_radius=12,
                                        alignment=ft.alignment.Alignment(0, 0)
                                    ),
                                    ft.Text(texto_opcion, color="white", size=13, weight="w500", overflow=ft.TextOverflow.FADE)
                                ], spacing=10),
                                bgcolor="#1e1e1e",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                    padding=15
                                ),
                                on_click=make_click_handler(),
                                expand=True
                            ),
                            expand=True
                        )
                    )
            else:
                # Modo retroalimentación (ya contestó esta pregunta)
                respuesta_usuario = estado_trivia["respuestas"][id_preg]
                elegida = respuesta_usuario["elegida"]
                correcta = respuesta_usuario["correcta"]
                fue_correcta = respuesta_usuario["es_correcta"]
                explicacion_txt = respuesta_usuario["explicacion"]
                
                for letra, texto_opcion in [
                    ("A", pregunta["Opcion_A"]),
                    ("B", pregunta["Opcion_B"]),
                    ("C", pregunta["Opcion_C"]),
                    ("D", pregunta["Opcion_D"])
                ]:
                    border_color = "#222222"
                    text_color = "#aaaaaa"
                    icon_review = None
                    
                    if letra == correcta:
                        border_color = "#00FF7F"
                        text_color = "white"
                        icon_review = ft.Icon(ft.Icons.CHECK, color="#00FF7F", size=16)
                    elif letra == elegida and not fue_correcta:
                        border_color = "#FF4500"
                        text_color = "white"
                        icon_review = ft.Icon(ft.Icons.CLOSE, color="#FF4500", size=16)
                        
                    opciones_controles.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Text(letra, color="black", weight="bold", size=12),
                                    bgcolor="#00FF7F" if letra == correcta else ("#FF4500" if letra == elegida else "#444444"),
                                    width=24,
                                    height=24,
                                    border_radius=12,
                                    alignment=ft.alignment.Alignment(0, 0)
                                ),
                                ft.Text(texto_opcion, color=text_color, size=13, weight="w500", expand=True),
                                icon_review if icon_review else ft.Container()
                            ], spacing=10),
                            padding=12,
                            bgcolor="#0F0F1A",
                            border_radius=8,
                            border=ft.Border.all(1, border_color)
                        )
                    )
    
            # Caja de retroalimentación
            caja_retro = ft.Container()
            if estado_trivia["retro_mostrada"]:
                resp_info = estado_trivia["respuestas"][id_preg]
                es_correcta_res = resp_info["es_correcta"]
                color_res = "#00FF7F" if es_correcta_res else "#FF4500"
                caja_retro = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINED, color=color_res, size=18),
                            ft.Text(
                                "Respuesta Correcta 🎉" if es_correcta_res else "Respuesta Incorrecta ❌",
                                color=color_res,
                                weight="bold",
                                size=13
                            )
                        ], spacing=5),
                        ft.Text(resp_info["explicacion"], size=12, color="white", italic=True),
                        ft.Container(height=5),
                        ft.Row([
                            ft.ElevatedButton(
                                "Siguiente Pregunta ➡️" if idx < 4 else "Ver Resultados del Reto 📊",
                                on_click=lambda e: avanzar_pregunta(),
                                bgcolor="#6E48AA",
                                color="white"
                            ),
                            ft.TextButton(
                                "Preguntar a LUXO 💬",
                                icon=ft.Icons.CHAT_ROUNDED,
                                on_click=lambda e, p=pregunta["Pregunta"], el=elegida, c=correcta, idm=pregunta.get("ID_Manual"): preguntar_a_luxo_pregunta(p, el, c, idm),
                                style=ft.ButtonStyle(color="#D8B4FE")
                            )
                        ], spacing=10)
                    ], spacing=8),
                    bgcolor="#0F0F1A",
                    padding=15,
                    border_radius=10,
                    border=ft.Border.all(1, "#333333")
                )
    
            reto_container.content = ft.Column([
                # Cabecera de progreso
                ft.Row([
                    ft.Text(f"Pregunta {idx + 1} de 5", color="#D8B4FE", size=13, weight="bold"),
                    ft.Container(
                        content=ft.Text(dificultad.upper(), color="black", size=10, weight="bold"),
                        bgcolor=color_dif,
                        padding=ft.padding.Padding(left=12, top=6, right=12, bottom=6),
                        border_radius=6
                    )
                ], alignment="spaceBetween"),
                ft.ProgressBar(value=progress_value, color="#D8B4FE", bgcolor="#141424"),
                ft.Container(height=5),
                
                # Tarjeta de pregunta
                ft.Container(
                    content=ft.Column([
                        ft.Text(pregunta["Pregunta"], color="white", size=15, weight="bold"),
                        ft.Container(height=10),
                        ft.Column(opciones_controles, spacing=10),
                        ft.Container(height=10),
                        caja_retro
                    ], spacing=10),
                    bgcolor="#1e1e2e",
                    padding=20,
                    border_radius=12,
                    border=ft.Border.all(1.5, "#D8B4FE")
                )
            ], spacing=10, scroll=ft.ScrollMode.AUTO)
    
        # ----------------- CASO 3: PANTALLA DE RESULTADOS (Partida terminada) -----------------
        elif estado_trivia["terminada"]:
            correctas_partida = sum(1 for r in estado_trivia["respuestas"].values() if r["es_correcta"])
            
            # Determinación de insignia/medalla y retroalimentación
            if correctas_partida == 5:
                insignia_titulo = "Auditor Estrella 🌟"
                insignia_desc = "¡Perfecto! Tienes un conocimiento impecable sobre los manuales operativos de la tienda."
                insignia_color = "#FFD700"
                insignia_icono = ft.Icons.EMOJI_EVENTS_ROUNDED
            elif correctas_partida >= 3:
                insignia_titulo = "Estudiante Aplicado 📚"
                insignia_desc = "¡Muy bien! Demuestras un excelente dominio de las normas y procesos de Sunglass Hut."
                insignia_color = "#C0C0C0"
                insignia_icono = ft.Icons.STAR_ROUNDED
            else:
                insignia_titulo = "Sigue Practicando 🔄"
                insignia_desc = "Te recomendamos repasar los manuales para afianzar tus conocimientos sobre las normas operativas."
                insignia_color = "#CD7F32"
                insignia_icono = ft.Icons.REFRESH_ROUNDED
            
            # Generar resumen de preguntas respondidas
            resumen_preguntas_controles = []
            for k_id, res_obj in estado_trivia["respuestas"].items():
                resumen_preguntas_controles.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE if res_obj["es_correcta"] else ft.Icons.CANCEL,
                                    color="#00FF7F" if res_obj["es_correcta"] else "#FF4500",
                                    size=18
                                ),
                                ft.Text(res_obj["pregunta"], color="white", size=13, weight="bold", expand=True)
                            ], spacing=8),
                            ft.Text(f"Tu respuesta: {res_obj['elegida']} | Correcta: {res_obj['correcta']}", size=11, color="#aaaaaa"),
                            ft.Text(f"Explicación: {res_obj['explicacion']}", size=11, color="white", italic=True),
                            ft.Row([
                                ft.TextButton(
                                    "Preguntar a LUXO 💬",
                                    icon=ft.Icons.CHAT_ROUNDED,
                                    on_click=lambda e, p=res_obj["pregunta"], el=res_obj["elegida"], c=res_obj["correcta"], idm=res_obj.get("id_manual"): preguntar_a_luxo_pregunta(p, el, c, idm),
                                    style=ft.ButtonStyle(color="#D8B4FE")
                                )
                            ], alignment="end"),
                            ft.Divider(height=10, color="#222222")
                        ], spacing=5),
                        padding=5
                    )
                )
    
            reto_container.content = ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(insignia_icono, size=55, color=insignia_color),
                        ft.Text(f"Puntaje: {correctas_partida} / 5", size=22, color="white", weight="bold"),
                        ft.Text(insignia_titulo, size=18, color=insignia_color, weight="bold"),
                        ft.Text(insignia_desc, size=12, color="#aaaaaa", text_align="center"),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "Intentar otro Reto 🔄",
                            on_click=lambda e: iniciar_nueva_partida(),
                            bgcolor="#6E48AA",
                            color="white"
                        )
                    ], horizontal_alignment="center", spacing=8),
                    bgcolor="#1e1e2e",
                    padding=20,
                    border_radius=12,
                    border=ft.Border.all(1.5, insignia_color)
                ),
                ft.Container(height=10),
                ft.Text("Desglose del Reto:", color="#aaaaaa", size=12, weight="bold"),
                ft.Container(
                    content=ft.Column(resumen_preguntas_controles, spacing=10),
                    bgcolor="#0F0F1A",
                    padding=15,
                    border_radius=10,
                    border=ft.Border.all(1, "#333333")
                )
            ], spacing=10, scroll=ft.ScrollMode.AUTO)
    
        try:
            page.update()
        except Exception:
            pass
    
    # Carga inicial de la UI en la bienvenida
    dibujar_ui()
    
    return ft.Column([
        ft.Row([
            ft.Text("Reto del Día 🏆", size=24, color="#D8B4FE", weight="bold"),
            ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: dibujar_ui(), icon_color="#00FFFF")
        ], alignment="spaceBetween", vertical_alignment="center"),
        ft.Text("Demuestra tu nivel respondiendo preguntas operativas y obtén insignias de desempeño.", color="#aaaaaa", size=13),
        ft.Divider(height=15, color="#333333"),
        reto_container
    ], expand=True, scroll=ft.ScrollMode.AUTO)