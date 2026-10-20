#!/usr/bin/env python3
"""
Práctica 6 - Contador de parpadeos LED
- Lee el valor de brillo del ESP32 por puerto serie
- Detecta caídas abruptas (transición ON -> OFF)
- Cuenta parpadeos hasta Ctrl+C
"""
import serial
import time
import argparse


def main():
    p = argparse.ArgumentParser(description="Contador de parpadeos LED")
    p.add_argument("--port", default="COM4",
                   help="Puerto serie (COM4, /dev/ttyUSB0, etc.)")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--list-ports", action="store_true",
                   help="Solo lista los puertos y sale")
    p.add_argument("--calibrate-samples", type=int, default=10,
                   help="Muestras iniciales para calibrar baseline")
    p.add_argument("--drop-ratio", type=float, default=0.5,
                   help="Fracción del baseline para considerar 'apagado' (0.5 = 50%%)")
    p.add_argument("--off-absolute", type=int, default=40,
                   help="Valor mínimo absoluto para considerar 'apagado'")
    p.add_argument("--rearm-ratio", type=float, default=0.8,
                   help="Fracción del baseline para volver a estado ON")
    p.add_argument("--cooldown", type=float, default=0.15,
                   help="Segundos mínimos entre parpadeos (anti-doble-conteo)")
    p.add_argument("--csv", default=None,
                   help="Archivo CSV opcional con log de muestras")
    args = p.parse_args()

    if args.list_ports:
        from serial.tools import list_ports
        print("Puertos disponibles:")
        for lp in list_ports.comports():
            print(f"  {lp.device}: {lp.description}")
        return

    # --- Abrir puerto ---
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f" Error abriendo {args.port}: {e}")
        print("   Usa --list-ports para ver los puertos disponibles.")
        return

    time.sleep(2)
    ser.reset_input_buffer()
    print(f"📡 Leyendo de {args.port} @ {args.baud} baudios")

    # --- Calibración ---
    print(f"Calibrando línea base ({args.calibrate_samples} muestras).")
    print(f"  Asegúrate de que el LED esté ENCENDIDO durante la calibración.\n")
    samples = []
    while len(samples) < args.calibrate_samples:
        try:
            line = ser.readline().decode().strip()
            if line:
                v = int(line)
                samples.append(v)
                print(f"   {len(samples)}/{args.calibrate_samples}: {v}")
        except (ValueError, UnicodeDecodeError):
            pass

    baseline = sum(samples) / len(samples)
    off_threshold = max(args.off_absolute, baseline * args.drop_ratio)
    rearm_threshold = baseline * args.rearm_ratio

    print(f"\n   Baseline:        {baseline:.1f}")
    print(f"   Umbral apagado:  {off_threshold:.1f}  (caer por debajo = parpadeo)")
    print(f"   Umbral rearme:   {rearm_threshold:.1f}  (subir por encima = listo)")

    if baseline < 50:
        print(f"   Baseline muy bajo ({baseline:.0f}). ¿Está el LED encendido?")

    print(f"\n  Detectando parpadeos... Ctrl+C para detener.\n")

    # --- Bucle de detección ---
    count = 0
    state = "ON"
    last_blink_time = 0.0
    start_time = time.time()
    log_rows = []
    warned_stuck = False

    try:
        while True:
            line = ser.readline().decode().strip()
            if not line:
                continue
            try:
                v = int(line)
            except ValueError:
                continue

            now = time.time()
            elapsed = now - start_time

            if state == "ON":
                # Actualiza baseline suavemente con muestras encendidas
                baseline = 0.98 * baseline + 0.02 * v
                off_threshold = max(args.off_absolute, baseline * args.drop_ratio)
                rearm_threshold = baseline * args.rearm_ratio

                if v < off_threshold and (now - last_blink_time) > args.cooldown:
                    count += 1
                    state = "OFF"
                    last_blink_time = now
                    print(f"[{elapsed:7.2f}s]  Parpadeo #{count:<3d}  "
                          f"(v={v}, baseline={baseline:.0f})")
            else:  # OFF
                if v > rearm_threshold:
                    state = "ON"
                    warned_stuck = False
                elif (now - last_blink_time) > 3.0 and not warned_stuck:
                    print(f"  Llevamos {now - last_blink_time:.0f}s en OFF. "
                          f"¿Se apagó el LED manualmente?")
                    warned_stuck = True

            if args.csv:
                log_rows.append((elapsed, v, state, count))

    except KeyboardInterrupt:
        print("\n\n Detenido por el usuario.")
    finally:
        ser.close()

    # --- Resumen ---
    total_time = time.time() - start_time
    print("\n" + "=" * 42)
    print("  RESUMEN")
    print("=" * 42)
    print(f"  Tiempo total:      {total_time:.1f} s")
    print(f"  Parpadeos totales: {count}")
    if total_time > 0:
        print(f"  Frecuencia media:  {count / total_time * 60:.1f} parpadeos/min")
    print("=" * 42)

    if args.csv:
        with open(args.csv, "w") as f:
            f.write("tiempo_s,valor,estado,conteo\n")
            for t, v, st, c in log_rows:
                f.write(f"{t:.3f},{v},{st},{c}\n")
        print(f"Datos guardados en {args.csv}")


if __name__ == "__main__":
    main()

