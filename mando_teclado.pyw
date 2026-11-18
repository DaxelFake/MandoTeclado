import ctypes
import json
import os
import sys
import tempfile
import time
import tkinter as tk
from ctypes import wintypes
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '1'
import pygame
from pygame._sdl2 import controller as sdlc
CARPETA = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(os.environ.get('APPDATA', CARPETA), 'MandoTeclado')
os.makedirs(DATOS, exist_ok=True)
ARCHIVO_APRENDIDAS = os.path.join(DATOS, 'aprendidas.json')
ARCHIVO_AJUSTES = os.path.join(DATOS, 'ajustes.json')
SENAL_ABRIR = os.path.join(tempfile.gettempdir(), 'mando_teclado_abrir.flag')
CLAVE_RUN = 'Software\\Microsoft\\Windows\\CurrentVersion\\Run'
NOMBRE_RUN = 'MandoTeclado'

def orden_autoinicio():
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}" --vigilar'
    pyw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    return f'"{pyw}" "{os.path.abspath(__file__)}" --vigilar'

def autoinicio_activo():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE_RUN) as k:
            winreg.QueryValueEx(k, NOMBRE_RUN)
            return True
    except OSError:
        return False

def poner_autoinicio(activar):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE_RUN, 0, winreg.KEY_SET_VALUE) as k:
        if activar:
            winreg.SetValueEx(k, NOMBRE_RUN, 0, winreg.REG_SZ, orden_autoinicio())
        else:
            try:
                winreg.DeleteValue(k, NOMBRE_RUN)
            except OSError:
                pass
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass
ULONG_PTR = ctypes.c_size_t
INPUT_MOUSE, INPUT_KEYBOARD = (0, 1)
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP, KEYEVENTF_UNICODE = (1, 2, 4)
MOUSEEVENTF_MOVE = 1
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = (2, 4)
MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP = (8, 16)
VK_BACK, VK_TAB, VK_RETURN, VK_ESCAPE = (8, 9, 13, 27)
VK_CONTROL, VK_MENU, VK_LWIN = (17, 18, 91)
VK_END, VK_HOME, VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN, VK_DELETE = (35, 36, 37, 38, 39, 40, 46)
EXTENDIDAS = {VK_END, VK_HOME, VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN, VK_DELETE, VK_LWIN}
GWL_EXSTYLE = -20
WS_EX_TOPMOST = 8
WS_EX_TOOLWINDOW = 128
WS_EX_NOACTIVATE = 134217728
ERROR_ALREADY_EXISTS = 183

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG), ('mouseData', wintypes.DWORD), ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('dwExtraInfo', ULONG_PTR)]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD), ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('dwExtraInfo', ULONG_PTR)]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [('uMsg', wintypes.DWORD), ('wParamL', wintypes.WORD), ('wParamH', wintypes.WORD)]

class _INPUTUNION(ctypes.Union):
    _fields_ = [('mi', MOUSEINPUT), ('ki', KEYBDINPUT), ('hi', HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _anonymous_ = ('u',)
    _fields_ = [('type', wintypes.DWORD), ('u', _INPUTUNION)]
user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)

def _send(*inputs):
    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))

def _key(vk=0, scan=0, flags=0):
    if vk in EXTENDIDAS:
        flags |= KEYEVENTF_EXTENDEDKEY
    i = INPUT(type=INPUT_KEYBOARD)
    i.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
    return i

def send_text(text):
    for ch in text:
        code = ord(ch)
        _send(_key(scan=code, flags=KEYEVENTF_UNICODE), _key(scan=code, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))

def send_vk(vk, veces=1):
    for _ in range(veces):
        _send(_key(vk=vk), _key(vk=vk, flags=KEYEVENTF_KEYUP))

def send_combo(*vks):
    _send(*[_key(vk=v) for v in vks], *[_key(vk=v, flags=KEYEVENTF_KEYUP) for v in reversed(vks)])

def mouse_move(dx, dy):
    i = INPUT(type=INPUT_MOUSE)
    i.mi = MOUSEINPUT(int(dx), int(dy), 0, MOUSEEVENTF_MOVE, 0, 0)
    _send(i)

def mouse_click(down_flag, up_flag):
    a, b = (INPUT(type=INPUT_MOUSE), INPUT(type=INPUT_MOUSE))
    a.mi = MOUSEINPUT(0, 0, 0, down_flag, 0, 0)
    b.mi = MOUSEINPUT(0, 0, 0, up_flag, 0, 0)
    _send(a, b)
_SIN_TILDE = str.maketrans('áéíóúüñ', 'aeiouun')

def normalizar(p):
    return p.lower().translate(_SIN_TILDE)

class Diccionario:

    def __init__(self):
        self.palabras = []
        try:
            with open(os.path.join(CARPETA, 'palabras_es.txt'), encoding='utf-8') as f:
                lista = [l.strip() for l in f if l.strip()]
        except OSError:
            lista = []
        n = len(lista)
        self.base = {p: n - i for i, p in enumerate(lista)}
        self.aprendidas = {}
        try:
            with open(ARCHIVO_APRENDIDAS, encoding='utf-8') as f:
                self.aprendidas = json.load(f)
        except (OSError, ValueError):
            pass
        self._rehacer()

    def _rehacer(self):
        todas = dict(self.base)
        for p, veces in self.aprendidas.items():
            todas[p] = todas.get(p, 0) + 100000 * veces
        self.palabras = sorted(((normalizar(p), p, pts) for p, pts in todas.items()), key=lambda t: -t[2])

    def sugerir(self, prefijo, cuantas=3):
        if not prefijo:
            return []
        pre = normalizar(prefijo)
        res = []
        for norm, p, _ in self.palabras:
            if norm.startswith(pre) and p != prefijo.lower():
                res.append(p)
                if len(res) == cuantas:
                    break
        return res

    def aprender(self, palabra):
        p = palabra.lower()
        if len(p) < 2 or not p.isalpha():
            return
        self.aprendidas[p] = self.aprendidas.get(p, 0) + 1
        self._rehacer()
        try:
            with open(ARCHIVO_APRENDIDAS, 'w', encoding='utf-8') as f:
                json.dump(self.aprendidas, f, ensure_ascii=False)
        except OSError:
            pass

def _fila(chars):
    return [(c, 'c:' + c, 1) for c in chars]

def _fila_abajo(texto_layout, texto_atajos):
    return [('⇧', 'shift', 1), (texto_layout, 'layout', 2), (texto_atajos, 'atajos', 2), ('Espacio', 'space', 3), ('⌫', 'back', 1), ('⏎', 'enter', 1)]
LETRAS = [_fila('1234567890'), _fila('qwertyuiop'), _fila('asdfghjklñ'), _fila('zxcvbnm,.?'), _fila_abajo('123 #', 'Atajos')]
SIMBOLOS = [_fila('!"#$%&/()='), _fila("áéíóúü¿¡'+"), _fila('-_:;*[]{}\\'), _fila('<>|~^`@€ç·'), _fila_abajo('ABC', 'Atajos')]
ATAJOS = [[('Copiar', 'k:copiar', 2), ('Pegar', 'k:pegar', 2), ('Cortar', 'k:cortar', 2), ('Deshacer', 'k:deshacer', 2), ('Rehacer', 'k:rehacer', 2)], [('Selec. todo', 'k:todo', 2), ('Guardar', 'k:guardar', 2), ('Buscar', 'k:buscar', 2), ('Borrar palabra', 'k:borrapal', 2), ('Supr', 'k:supr', 2)], [('Esc', 'k:esc', 2), ('Tab', 'k:tab', 2), ('Alt+Tab', 'k:alttab', 2), ('Win', 'k:win', 2), ('Escritorio', 'k:escritorio', 2)], [('Inicio', 'k:inicio', 2), ('Fin', 'k:fin', 2), ('↑', 'k:arriba', 1), ('↓', 'k:abajo', 1), ('Vibración', 'k:vibra', 2), ('Con Windows', 'k:autoinicio', 2)], _fila_abajo('123 #', 'ABC')]
COMBOS = {'copiar': (VK_CONTROL, ord('C')), 'pegar': (VK_CONTROL, ord('V')), 'cortar': (VK_CONTROL, ord('X')), 'deshacer': (VK_CONTROL, ord('Z')), 'rehacer': (VK_CONTROL, ord('Y')), 'todo': (VK_CONTROL, ord('A')), 'guardar': (VK_CONTROL, ord('S')), 'buscar': (VK_CONTROL, ord('F')), 'borrapal': (VK_CONTROL, VK_BACK), 'supr': (VK_DELETE,), 'esc': (VK_ESCAPE,), 'tab': (VK_TAB,), 'alttab': (VK_MENU, VK_TAB), 'win': (VK_LWIN,), 'escritorio': (VK_LWIN, ord('D')), 'inicio': (VK_HOME,), 'fin': (VK_END,), 'arriba': (VK_UP,), 'abajo': (VK_DOWN,)}
FONDO = '#15171c'
TECLA = '#262a33'
TECLA_ESP = '#1f232b'
SUGER = '#1b1e25'
TEXTO = '#e8eaf0'
TEXTO_SUAVE = '#8a90a0'
ACENTO = '#e0453a'
ACTIVO = '#3a7bd5'
CELDA = 58
ALTO = 52
ALTO_SUG = 40
SEP = 6
BARRA = 34

def _estilo_sin_foco(ventana):
    ventana.update_idletasks()
    hwnd = user32.GetParent(ventana.winfo_id()) or ventana.winfo_id()
    estilo = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, estilo | WS_EX_NOACTIVATE | WS_EX_TOPMOST | WS_EX_TOOLWINDOW)

class MandoTeclado:

    def __init__(self, vigilar):
        pygame.init()
        sdlc.init()
        self.vigilar = vigilar
        self.mando = None
        self.prev = {}
        self.repeat_dir = None
        self.repeat_next = 0.0
        self.dic = Diccionario()
        self.ajustes = self._cargar_ajustes()
        self._autoinicio = autoinicio_activo()
        self.layout = LETRAS
        self.fila, self.col = (2, 0)
        self.mayus = 0
        self.palabra = ''
        self.sugerencias = []
        self.ultima_sugerencia = ''
        self.pos_antes = None
        self.visible = True
        self.estado = 'vigilando'
        self.dialogo = None
        self.dialogo_hasta = 0.0
        self._back_pulsado = False
        self.root = tk.Tk()
        self.root.title('Mando Teclado')
        self.root.overrideredirect(True)
        self.root.configure(bg=FONDO)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        ancho = 10 * CELDA + 11 * SEP
        alto = BARRA + ALTO_SUG + SEP + 5 * (ALTO + SEP) + 26
        self.canvas = tk.Canvas(self.root, width=ancho, height=alto, bg=FONDO, highlightthickness=0)
        self.canvas.pack()
        self.ancho, self.alto = (ancho, alto)
        sw, sh = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        self.root.geometry(f'{ancho}x{alto}+{(sw - ancho) // 2}+{sh - alto - 70}')
        self.canvas.bind('<ButtonPress-1>', self._raton_abajo)
        self.canvas.bind('<B1-Motion>', self._raton_arrastre)
        self._drag = None
        _estilo_sin_foco(self.root)
        self.root.withdraw()
        if not vigilar:
            self.abrir_teclado()
        self.root.after(50, self.bucle)

    def _cargar_ajustes(self):
        try:
            with open(ARCHIVO_AJUSTES, encoding='utf-8') as f:
                return {'vibracion': True, **json.load(f)}
        except (OSError, ValueError):
            return {'vibracion': True}

    def _guardar_ajustes(self):
        try:
            with open(ARCHIVO_AJUSTES, 'w', encoding='utf-8') as f:
                json.dump(self.ajustes, f)
        except OSError:
            pass

    def vibrar(self, fuerza=0.35, ms=35):
        if self.mando and self.ajustes.get('vibracion', True):
            try:
                self.mando.rumble(0.0, fuerza, ms)
            except Exception:
                pass

    def abrir_teclado(self):
        self.cerrar_dialogo()
        self.estado = 'teclado'
        self.visible = True
        self.prev = {}
        self.root.deiconify()
        self.root.attributes('-topmost', True)
        self.dibujar()

    def cerrar_teclado(self):
        if not self.vigilar:
            self.salir()
            return
        self.root.withdraw()
        self.estado = 'vigilando'
        self.reiniciar_palabra()

    def preguntar(self):
        self.estado = 'preguntando'
        self.prev = {}
        d = tk.Toplevel(self.root)
        d.overrideredirect(True)
        d.configure(bg=FONDO)
        d.attributes('-topmost', True)
        w, h = (420, 130)
        sw, sh = (d.winfo_screenwidth(), d.winfo_screenheight())
        d.geometry(f'{w}x{h}+{(sw - w) // 2}+{sh - h - 120}')
        cv = tk.Canvas(d, width=w, height=h, bg=FONDO, highlightthickness=1, highlightbackground=ACENTO)
        cv.pack()
        nombre = self.mando.name if self.mando else 'un mando'
        cv.create_text(w / 2, 28, fill=TEXTO, font=('Segoe UI', 11, 'bold'), text=f'🎮  Se conectó {nombre}')
        cv.create_text(w / 2, 54, fill=TEXTO_SUAVE, font=('Segoe UI', 10), text='¿Abrir el teclado para escribir con el mando?')
        cv.create_rectangle(60, 78, 200, 112, fill=ACENTO, outline='')
        cv.create_text(130, 95, fill=TEXTO, font=('Segoe UI', 10, 'bold'), text='✕  Sí, abrir')
        cv.create_rectangle(220, 78, 360, 112, fill=TECLA, outline='')
        cv.create_text(290, 95, fill=TEXTO, font=('Segoe UI', 10), text='○  Ahora no')

        def clic(e):
            if 78 <= e.y <= 112:
                if 60 <= e.x <= 200:
                    self.abrir_teclado()
                elif 220 <= e.x <= 360:
                    self.responder_no()
        cv.bind('<ButtonPress-1>', clic)
        _estilo_sin_foco(d)
        self.dialogo = d
        self.dialogo_hasta = time.monotonic() + 20

    def responder_no(self):
        self.cerrar_dialogo()
        self.estado = 'vigilando'

    def cerrar_dialogo(self):
        if self.dialogo is not None:
            try:
                self.dialogo.destroy()
            except tk.TclError:
                pass
            self.dialogo = None

    def salir(self):
        try:
            sdlc.quit()
            pygame.quit()
        finally:
            self.root.destroy()

    def _raton_abajo(self, e):
        if e.y < BARRA:
            if e.x > self.ancho - 34:
                self.cerrar_teclado()
                return
            self._drag = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())
        else:
            self._drag = None
            for (f, c), (x0, y0, x1, y1) in self._rects.items():
                if x0 <= e.x <= x1 and y0 <= e.y <= y1:
                    self.fila, self.col = (f, c)
                    self.pulsar()
                    return

    def _raton_arrastre(self, e):
        if self._drag:
            dx, dy = self._drag
            self.root.geometry(f'+{e.x_root - dx}+{e.y_root - dy}')

    def filas(self):
        sug = [(s, 's:' + s, 10 / 3) for s in self.sugerencias]
        sug += [('', 'nada', 10 / 3)] * (3 - len(sug))
        return [sug] + self.layout

    def _texto_tecla(self, etiqueta, accion):
        if accion.startswith('c:'):
            return etiqueta.upper() if self.mayus else etiqueta
        if accion.startswith('s:'):
            return self._con_mayus(etiqueta)
        if accion == 'shift':
            return ['⇧', '⇧¹', '⇪'][self.mayus]
        if accion == 'k:vibra':
            return 'Vibración ' + ('sí' if self.ajustes.get('vibracion', True) else 'no')
        if accion == 'k:autoinicio':
            return 'Con Windows ' + ('sí' if self._autoinicio else 'no')
        return etiqueta

    def dibujar(self):
        if self.estado != 'teclado':
            return
        cv = self.canvas
        cv.delete('all')
        self._rects = {}
        nombre = self.mando.name if self.mando else 'Conecta un mando…'
        cv.create_text(12, 17, anchor='w', fill=TEXTO_SUAVE, font=('Segoe UI', 10), text=f'🎮  {nombre}')
        estado = 'MAYÚS' if self.mayus == 2 else 'Atajos' if self.layout is ATAJOS else ''
        cv.create_text(self.ancho - 44, 17, anchor='e', fill=ACENTO, font=('Segoe UI', 10, 'bold'), text=estado)
        cv.create_text(self.ancho - 17, 17, fill=TEXTO_SUAVE, font=('Segoe UI', 12), text='✕')
        y = BARRA
        for f, fila in enumerate(self.filas()):
            alto = ALTO_SUG if f == 0 else ALTO
            x = SEP
            for c, (etq, acc, w) in enumerate(fila):
                ancho = w * CELDA + (w - 1) * SEP
                sel = f == self.fila and c == self.col
                encendida = acc == 'shift' and self.mayus or (acc == 'layout' and self.layout is SIMBOLOS) or (acc == 'atajos' and self.layout is ATAJOS)
                if sel:
                    color = ACENTO
                elif f == 0:
                    color = SUGER
                elif encendida:
                    color = ACTIVO
                elif acc.startswith('c:'):
                    color = TECLA
                else:
                    color = TECLA_ESP
                cv.create_rectangle(x, y, x + ancho, y + alto, fill=color, outline=ACENTO if sel else '', width=2)
                if acc.startswith('c:'):
                    tam = 17
                elif f == 0:
                    tam = 13
                else:
                    tam = 11
                cv.create_text(x + ancho / 2, y + alto / 2, fill=TEXTO, font=('Segoe UI', tam, 'bold' if sel else 'normal'), text=self._texto_tecla(etq, acc))
                self._rects[f, c] = (x, y, x + ancho, y + alto)
                x += ancho + SEP
            y += alto + SEP
        cv.create_text(self.ancho / 2, y + 10, fill=TEXTO_SUAVE, font=('Segoe UI', 8), text='✕ escribir · □ borrar · △ espacio · L2 mayús · R2 enter · R1 ir a sugerencias · L1 cursor ← · ○ ocultar')

    def _con_mayus(self, p):
        if self.mayus == 2:
            return p.upper()
        if self.mayus == 1 or self.palabra[:1].isupper():
            return p[:1].upper() + p[1:]
        return p

    def _actualizar_sugerencias(self):
        self.sugerencias = self.dic.sugerir(self.palabra) if self.layout is not ATAJOS else []

    def reiniciar_palabra(self, aprender=False):
        if aprender and self.palabra:
            self.dic.aprender(self.palabra)
        self.palabra = ''
        self.sugerencias = []
        self.ultima_sugerencia = ''
        self.pos_antes = None

    def _centro_x(self, f, c):
        fila = self.filas()[f]
        x0 = sum((w for _, _, w in fila[:c]))
        return x0 + fila[c][2] / 2

    def _col_en_x(self, f, cx):
        fila = self.filas()[f]
        acum = 0
        for c, (_, _, w) in enumerate(fila):
            if acum <= cx < acum + w:
                return c
            acum += w
        return len(fila) - 1

    def mover(self, dx, dy):
        filas = self.filas()
        if dy:
            cx = self._centro_x(self.fila, self.col)
            self.fila = (self.fila + dy) % len(filas)
            self.col = self._col_en_x(self.fila, cx)
        if dx:
            self.col = (self.col + dx) % len(filas[self.fila])
        self.dibujar()

    def pulsar(self):
        etq, acc, _ = self.filas()[self.fila][self.col]
        if acc == 'nada':
            return
        self.vibrar()
        if acc.startswith('c:'):
            self.escribir(acc[2:])
        elif acc.startswith('s:'):
            self.usar_sugerencia(acc[2:])
        elif acc.startswith('k:'):
            self.atajo(acc[2:])
        elif acc == 'shift':
            self.ciclo_mayus()
        elif acc == 'layout':
            self.cambiar_layout(SIMBOLOS if self.layout is LETRAS else LETRAS)
        elif acc == 'atajos':
            self.cambiar_layout(LETRAS if self.layout is ATAJOS else ATAJOS)
        elif acc == 'space':
            self.espacio()
        elif acc == 'back':
            self.borrar()
        elif acc == 'enter':
            self.enter()
        self.dibujar()

    def escribir(self, t):
        if self.mayus:
            t = t.upper()
        send_text(t)
        self.ultima_sugerencia = ''
        if t.isalpha():
            self.palabra += t
            self._actualizar_sugerencias()
        else:
            self.reiniciar_palabra(aprender=True)
        if self.mayus == 1:
            self.mayus = 0

    def usar_sugerencia(self, p):
        p = self._con_mayus(p)
        volver = self.pos_antes
        send_vk(VK_BACK, len(self.palabra))
        send_text(p + ' ')
        self.palabra = p
        self.reiniciar_palabra(aprender=True)
        self.ultima_sugerencia = p + ' '
        if self.mayus == 1:
            self.mayus = 0
        self.fila, self.col = volver or (2, 0)

    def espacio(self):
        send_text(' ')
        self.reiniciar_palabra(aprender=True)

    def enter(self):
        send_vk(VK_RETURN)
        self.reiniciar_palabra(aprender=True)

    def borrar(self):
        if self.ultima_sugerencia:
            send_vk(VK_BACK, len(self.ultima_sugerencia))
            self.ultima_sugerencia = ''
            self.palabra = ''
            self.sugerencias = []
            return
        send_vk(VK_BACK)
        if self.palabra:
            self.palabra = self.palabra[:-1]
            self._actualizar_sugerencias()

    def atajo(self, nombre):
        if nombre == 'vibra':
            self.ajustes['vibracion'] = not self.ajustes.get('vibracion', True)
            self._guardar_ajustes()
            self.vibrar(0.6, 120)
            return
        if nombre == 'autoinicio':
            try:
                poner_autoinicio(not self._autoinicio)
            except OSError:
                pass
            self._autoinicio = autoinicio_activo()
            return
        send_combo(*COMBOS[nombre])
        self.reiniciar_palabra()

    def ciclo_mayus(self):
        self.mayus = (self.mayus + 1) % 3
        self.dibujar()

    def cambiar_layout(self, nuevo):
        self.layout = nuevo
        self._actualizar_sugerencias()
        filas = self.filas()
        self.fila = min(self.fila, len(filas) - 1)
        self.col = min(self.col, len(filas[self.fila]) - 1)
        self.dibujar()

    def alternar_visible(self):
        self.visible = not self.visible
        if self.visible:
            self.root.deiconify()
            self.root.attributes('-topmost', True)
            self.dibujar()
        else:
            self.root.withdraw()

    def _buscar_mando(self):
        if self.mando and self.mando.attached():
            return False
        if self.mando:
            self.mando = None
            if self.estado == 'preguntando':
                self.responder_no()
            elif self.estado == 'teclado' and self.vigilar:
                self.cerrar_teclado()
            self.dibujar()
        for i in range(sdlc.get_count()):
            if sdlc.is_controller(i):
                self.mando = sdlc.Controller(i)
                self.prev = {}
                self.dibujar()
                return True
        return False

    def _flanco(self, nombre, pulsado):
        antes = self.prev.get(nombre, False)
        self.prev[nombre] = pulsado
        return pulsado and (not antes)

    def bucle(self):
        try:
            pygame.event.pump()
            nuevo = self._buscar_mando()
            if os.path.exists(SENAL_ABRIR):
                try:
                    os.remove(SENAL_ABRIR)
                except OSError:
                    pass
                self.abrir_teclado()
            elif nuevo and self.estado == 'vigilando':
                self.preguntar()
            if self.mando and self.estado == 'teclado':
                self._leer_mando()
            elif self.mando and self.estado == 'preguntando':
                self._leer_dialogo()
            if self.estado == 'preguntando' and time.monotonic() > self.dialogo_hasta:
                self.responder_no()
        except Exception as e:
            print('Error leyendo el mando:', e, file=sys.stderr)
            self.mando = None
        try:
            if self.root.winfo_exists():
                espera = 500 if self.estado == 'vigilando' else 16
                self.root.after(espera, self.bucle)
        except tk.TclError:
            pass

    def _leer_dialogo(self):
        m = self.mando
        si = self._flanco('a', bool(m.get_button(pygame.CONTROLLER_BUTTON_A)))
        no = self._flanco('b', bool(m.get_button(pygame.CONTROLLER_BUTTON_B)))
        if si:
            self.vibrar(0.5, 80)
            self.abrir_teclado()
            self.prev['a'] = True
        elif no:
            self.responder_no()

    def _leer_mando(self):
        m = self.mando
        B = lambda b: bool(m.get_button(b))
        ax = lambda a: m.get_axis(a) / 32767.0
        back, start = (B(pygame.CONTROLLER_BUTTON_BACK), B(pygame.CONTROLLER_BUTTON_START))
        if back and start:
            self.prev['start'] = True
            self._back_pulsado = False
            self.cerrar_teclado()
            return
        if self._flanco('back', back):
            self._back_pulsado = True
        if not back and self._back_pulsado:
            self._back_pulsado = False
            self.alternar_visible()
        rx, ry = (ax(pygame.CONTROLLER_AXIS_RIGHTX), ax(pygame.CONTROLLER_AXIS_RIGHTY))
        dz = 0.15
        if abs(rx) > dz or abs(ry) > dz:

            def vel(v):
                if abs(v) <= dz:
                    return 0
                v2 = (abs(v) - dz) / (1 - dz)
                return v2 ** 2 * 22 * (1 if v > 0 else -1)
            mouse_move(vel(rx), vel(ry))
        if self._flanco('r3', B(pygame.CONTROLLER_BUTTON_RIGHTSTICK)):
            mouse_click(MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP)
            self.reiniciar_palabra()
        if self._flanco('l3', B(pygame.CONTROLLER_BUTTON_LEFTSTICK)):
            mouse_click(MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP)
            self.reiniciar_palabra()
        if not self.visible:
            return
        lx, ly = (ax(pygame.CONTROLLER_AXIS_LEFTX), ax(pygame.CONTROLLER_AXIS_LEFTY))
        d = None
        if B(pygame.CONTROLLER_BUTTON_DPAD_UP) or ly < -0.6:
            d = (0, -1)
        elif B(pygame.CONTROLLER_BUTTON_DPAD_DOWN) or ly > 0.6:
            d = (0, 1)
        elif B(pygame.CONTROLLER_BUTTON_DPAD_LEFT) or lx < -0.6:
            d = (-1, 0)
        elif B(pygame.CONTROLLER_BUTTON_DPAD_RIGHT) or lx > 0.6:
            d = (1, 0)
        ahora = time.monotonic()
        if d is None:
            self.repeat_dir = None
        elif d != self.repeat_dir:
            self.repeat_dir = d
            self.repeat_inicio = ahora
            self.repeat_next = ahora + 0.25
            self.mover(*d)
        elif ahora >= self.repeat_next:
            mantenido = ahora - self.repeat_inicio
            intervalo = max(0.03, 0.09 - 0.06 * min(1.0, (mantenido - 0.25) / 0.8))
            self.repeat_next = ahora + intervalo
            self.mover(*d)
        if self._flanco('a', B(pygame.CONTROLLER_BUTTON_A)):
            self.pulsar()
        if self._flanco('b', B(pygame.CONTROLLER_BUTTON_B)):
            self.alternar_visible()
            return
        if self._flanco('x', B(pygame.CONTROLLER_BUTTON_X)):
            self.vibrar()
            self.borrar()
            self.dibujar()
        if self._flanco('y', B(pygame.CONTROLLER_BUTTON_Y)):
            self.vibrar()
            self.espacio()
            self.dibujar()
        if self._flanco('lb', B(pygame.CONTROLLER_BUTTON_LEFTSHOULDER)):
            send_vk(VK_LEFT)
            self.reiniciar_palabra()
            self.dibujar()
        if self._flanco('rb', B(pygame.CONTROLLER_BUTTON_RIGHTSHOULDER)):
            if self.sugerencias:
                if self.fila == 0:
                    self.col = (self.col + 1) % len(self.sugerencias)
                else:
                    self.pos_antes = (self.fila, self.col)
                    self.fila, self.col = (0, 0)
            else:
                send_vk(VK_RIGHT)
                self.reiniciar_palabra()
            self.dibujar()
        enter_r2 = self._flanco('rt', ax(pygame.CONTROLLER_AXIS_TRIGGERRIGHT) > 0.5)
        if self._flanco('start', start) or enter_r2:
            self.vibrar()
            self.enter()
            self.dibujar()
        if self._flanco('lt', ax(pygame.CONTROLLER_AXIS_TRIGGERLEFT) > 0.5):
            self.ciclo_mayus()

    def run(self):
        self.root.mainloop()

def ya_hay_otro():
    kernel32.CreateMutexW(None, False, 'Local\\MandoTecladoDaxel')
    return ctypes.get_last_error() == ERROR_ALREADY_EXISTS
if __name__ == '__main__':
    vigilar = '--vigilar' in sys.argv
    if ya_hay_otro():
        if not vigilar:
            open(SENAL_ABRIR, 'w').close()
        sys.exit(0)
    try:
        os.remove(SENAL_ABRIR)
    except OSError:
        pass
    MandoTeclado(vigilar).run()
