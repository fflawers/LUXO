import bcrypt
import urllib.parse
import flet as ft

def hash_password(plain_password: str) -> str:
    """Genera un hash seguro de bcrypt para la contraseña recibida."""
    if not plain_password:
        return ""
    pwd_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt(12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verifica una contraseña recibida contra la contraseña encriptada en BD.
    Soporta contraseñas encriptadas con bcrypt ($2b$, $2a$) y contraseñas legacy en texto plano.
    """
    try:
        if not plain_password or not stored_password:
            return False
        # Si la contraseña guardada en BD es un hash de bcrypt:
        if stored_password.startswith("$2b$") or stored_password.startswith("$2a$"):
            return bcrypt.checkpw(plain_password.encode('utf-8'), stored_password.encode('utf-8'))
        # Compatibilidad con contraseñas legacy en texto plano:
        return plain_password == stored_password
    except Exception as ex:
        print("Error en verificación de contraseña bcrypt:", ex)
        return False

def run_async_sync(coro, page):
    import threading
    event = threading.Event()
    result = [None]
    error = [None]
    async def wrapper():
        try:
            result[0] = await coro
        except Exception as e:
            error[0] = e
        finally:
            event.set()
    page.run_task(wrapper)
    event.wait()
    if error[0]:
        raise error[0]
    return result[0]

def ejecutar_js_flet(page: ft.Page, js_code: str):
    """Ejecuta código JavaScript de forma 100% segura en Flet Web."""
    if not page:
        return
    try:
        encoded = urllib.parse.quote(js_code)
        target_url = f"javascript:void(eval(decodeURIComponent('{encoded}')))"
        async def _do_launch():
            try:
                res = page.launch_url(target_url)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e_l:
                print("Notice inner launch_url:", e_l)
        page.run_task(_do_launch)
    except Exception as ex_ej:
        print("Error al ejecutar JS en Flet:", ex_ej)
