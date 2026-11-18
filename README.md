# Mando Teclado

Escribe en cualquier programa de Windows usando un mando de consola, con controles parecidos al teclado de la PS5.

El teclado aparece encima de todas las ventanas sin quitarles el foco, así que lo que escribes va directo al navegador, al chat, a Word o a donde tengas el cursor.

Funciona con mandos de PlayStation (DualSense, DualShock 4), Xbox, Switch Pro y la mayoría de los genéricos, por cable o Bluetooth.

## Descargar

1. Ve a [Releases](../../releases/latest) y descarga **MandoTeclado.exe**.
2. Ábrelo. No necesita instalación.

> Windows puede mostrar un aviso de SmartScreen porque el programa no está firmado. Pulsa **Más información → Ejecutar de todas formas**.

## Controles

| PlayStation | Xbox | Acción |
|---|---|---|
| Cruceta / stick izquierdo | Cruceta / stick izquierdo | Moverse por el teclado (mantén pulsado para ir más rápido) |
| ✕ | A | Escribir la tecla elegida |
| □ | X | Borrar (justo después de usar una sugerencia, borra la palabra entera) |
| △ | Y | Espacio |
| ○ | B | Ocultar el teclado |
| R1 | RB | Ir a las sugerencias (otra vez: la siguiente) |
| L1 | LB | Mover el cursor a la izquierda |
| L2 | LT | Mayúsculas: una letra → fijas → apagadas |
| R2 / Options | RT / Start | Enter |
| Create | Back | Mostrar u ocultar el teclado |
| Stick derecho | Stick derecho | Mover el ratón |
| R3 / L3 | R3 / L3 | Clic izquierdo / clic derecho |
| Create + Options | Back + Start | Cerrar el teclado |

## Funciones

- **Sugerencias de palabras.** Mientras escribes aparecen tres palabras arriba. Con R1 saltas a ellas y con ✕ eliges una.
- **Aprende tus palabras.** Las palabras nuevas que escribes se recuerdan y te las sugiere la próxima vez.
- **Símbolos y acentos.** La tecla «123 #» abre los símbolos, la ñ y las vocales con tilde.
- **Atajos.** Copiar, pegar, cortar, deshacer, seleccionar todo, buscar, Alt+Tab, tecla Windows y más.
- **Modo Programador.** En «Atajos», la tecla «</> Programador» abre una pantalla con símbolos de código (`( ) [ ] { } < > = ; => ->`...) y atajos de editor: tabular, comentar y descomentar, mover, duplicar o borrar líneas, seleccionar la siguiente coincidencia, paleta de comandos, abrir archivo, autocompletar, renombrar (F2), ir a definición (F12), terminal, ejecutar (F5), formatear e ir a línea. Los atajos son los de VS Code y funcionan con cualquier idioma de teclado.
- **Vibración** al pulsar cada tecla. Se activa o desactiva en «Atajos».
- **Arranque con Windows.** En «Atajos», activa «Con Windows». El programa se queda esperando sin molestar y, cuando conectas un mando, pregunta si quieres abrir el teclado.

## Licencia

El código está bajo la [licencia MIT](LICENSE).

La lista de palabras para las sugerencias (`palabras_es.txt`) viene de [FrequencyWords](https://github.com/hermitdave/FrequencyWords) de Hermit Dave y mantiene su licencia original, CC BY-SA 4.0.
