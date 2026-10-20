import serial
import time

# Ajusta el puerto COM y la velocidad
# En Windows suele ser 'COM3', 'COM4', etc.
# En Linux/Mac suele ser '/dev/ttyUSB0' o '/dev/ttyACM0'
PUERTO = 'COM3'
BAUDIOS = 115200
UMBRAL = 50000  # El mismo umbral que calibraste en Arduino

try:
    arduino = serial.Serial(PUERTO, BAUDIOS, timeout=1)
    time.sleep(2)  # Espera a que Arduino se reinicie
    print(f"Conectado a {PUERTO}. Leyendo datos...")

    while True:
        linea = arduino.readline().decode('utf-8').strip()
        if linea:
            print(linea)
            # Aquí podrías añadir lógica extra en Python
            # Por ejemplo, si "valor" está en la línea, extraerlo y decidir.
            if "LLENO" in linea:
                print(">>> Python: El recipiente está LLENO <<<")
            elif "vacío" in linea:
                print(">>> Python: El recipiente está VACÍO <<<")

except serial.SerialException as e:
    print(f"Error al abrir el puerto {PUERTO}: {e}")
except KeyboardInterrupt:
    print("\nPrograma detenido por el usuario.")
    if 'arduino' in locals() and arduino.is_open:
        arduino.close()