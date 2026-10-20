#!/usr/bin/env python3
"""
Práctica 3 - Sumador binario desde dos fotos (caja oscura con barreras)
- Pregunta cuántos bits
- Pide seleccionar foto A
- Pide seleccionar foto B
- Identifica cada número, los suma
- Imprime binario y decimal de A, B y el resultado
"""
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox


# ------------------------------------------------------------------
# Diálogos (mismo estilo que el programa 2)
# ------------------------------------------------------------------
def ask_num_bits():
    root = tk.Tk(); root.withdraw()
    n = simpledialog.askinteger(
        "Número de bits",
        "¿Cuántos LEDs (bits) tiene tu arreglo?",
        minvalue=1, maxvalue=32, initialvalue=4,
    )
    root.destroy()
    return n


def ask_image_path(titulo):
    root = tk.Tk(); root.withdraw()
    path = filedialog.askopenfilename(
        title=titulo,
        filetypes=[
            ("Imágenes", "*.jpg *.jpeg *.png *.bmp"),
            ("Todos los archivos", "*.*"),
        ],
    )
    root.destroy()
    return path


# ------------------------------------------------------------------
# Lectura (misma lógica que el programa 2)
# ------------------------------------------------------------------
def read_binary(img, n_bits, margin=0.05, inner_margin=0.15,
                y_band=(0.20, 0.80), v_thresh=200, min_pixels=15):
    h, w = img.shape[:2]
    v = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 2]

    y0 = int(h * y_band[0])
    y1 = int(h * y_band[1])
    x_start = int(w * margin)
    x_end = int(w * (1 - margin))
    seg_w = (x_end - x_start) / n_bits

    bits, diag = [], []
    for i in range(n_bits):
        seg_x0 = x_start + i * seg_w
        seg_x1 = x_start + (i + 1) * seg_w
        inner_x0 = int(seg_x0 + inner_margin * seg_w)
        inner_x1 = int(seg_x1 - inner_margin * seg_w)
        roi = v[y0:y1, inner_x0:inner_x1]
        bright = int((roi > v_thresh).sum())
        max_v = int(roi.max()) if roi.size else 0
        on = bright >= min_pixels
        bits.append("1" if on else "0")
        diag.append({"max_v": max_v, "bright_px": bright})

    binary = "".join(bits)
    decimal = int(binary, 2) if binary else 0
    return binary, decimal, diag


# ------------------------------------------------------------------
# Visualización (para una imagen individual, marca sus bits)
# ------------------------------------------------------------------
def visualize_bits(img, n_bits, binary, label="",
                   margin=0.05, inner_margin=0.15, y_band=(0.20, 0.80)):
    h, w = img.shape[:2]
    vis = img.copy()
    x_start = int(w * margin)
    x_end = int(w * (1 - margin))
    seg_w = (x_end - x_start) / n_bits
    y0 = int(h * y_band[0])
    y1 = int(h * y_band[1])

    for i in range(n_bits):
        seg_x0 = int(x_start + i * seg_w)
        seg_x1 = int(x_start + (i + 1) * seg_w)
        inner_x0 = int(seg_x0 + inner_margin * seg_w)
        inner_x1 = int(seg_x1 - inner_margin * seg_w)
        color = (0, 255, 0) if binary[i] == "1" else (0, 0, 255)
        cv2.rectangle(vis, (seg_x0, y0), (seg_x1, y1), (100, 100, 100), 1)
        cv2.rectangle(vis, (inner_x0, y0), (inner_x1, y1), color, 2)
        cx = (seg_x0 + seg_x1) // 2
        cv2.putText(vis, binary[i], (cx - 10, y0 - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

    total = int(binary, 2) if binary else 0
    cv2.putText(vis, f"{label}  Bin: {binary}   Dec: {total}",
                (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (0, 255, 255), 2)
    return vis


# ------------------------------------------------------------------
# Suma y presentación tipo "escuela"
# ------------------------------------------------------------------
def pretty_addition(bin_a, bin_b, bin_sum):
    width = len(bin_sum)
    a = bin_a.zfill(width)
    b = bin_b.zfill(width)
    line = "  " + "─" * width
    return (
        f"    {a}\n"
        f"  + {b}\n"
        f"  {line}\n"
        f"    {bin_sum}"
    )


def add_binaries(bin_a, bin_b):
    a = int(bin_a, 2) if bin_a else 0
    b = int(bin_b, 2) if bin_b else 0
    total = a + b
    width = max(len(bin_a), len(bin_b)) + 1   # +1 para el acarreo
    bin_sum = format(total, f"0{width}b")
    return a, b, total, bin_sum


# ------------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------------
def main():
    n_bits = ask_num_bits()
    if not n_bits:
        print("Cancelado.")
        return

    while True:
        # --- Foto A ---
        path_a = ask_image_path("Selecciona la foto del número A")
        if not path_a:
            print("Cancelado.")
            return
        img_a = cv2.imread(path_a)
        if img_a is None:
            print(f"❌ No se pudo leer {path_a}")
            continue

        # --- Foto B ---
        path_b = ask_image_path("Selecciona la foto del número B")
        if not path_b:
            print("Cancelado.")
            return
        img_b = cv2.imread(path_b)
        if img_b is None:
            print(f"❌ No se pudo leer {path_b}")
            continue

        # --- Lectura de ambas ---
        bin_a, dec_a, diag_a = read_binary(img_a, n_bits)
        bin_b, dec_b, diag_b = read_binary(img_b, n_bits)

        # --- Suma ---
        a, b, total, bin_sum = add_binaries(bin_a, bin_b)

        # --- Salida en terminal (mismo formato que práctica 2) ---
        print("\n" + "=" * 55)
        print(f"  Foto A:  {path_a}")
        print(f"    Binario: {bin_a}   Decimal: {dec_a}")
        print(f"  Foto B:  {path_b}")
        print(f"    Binario: {bin_b}   Decimal: {dec_b}")
        print("-" * 55)
        print(pretty_addition(bin_a, bin_b, bin_sum))
        print("-" * 55)
        print(f"  Resultado binario:  {bin_sum}")
        print(f"  Resultado decimal:  {total}")
        print("=" * 55)

        print("\n  Diagnóstico LED por LED:")
        print(f"  {'LED':>3} | {'A':^15} | {'B':^15}")
        print(f"  {'':>3} | {'bit':>3} {'maxV':>5} {'brPx':>5} | "
              f"{'bit':>3} {'maxV':>5} {'brPx':>5}")
        for i in range(n_bits):
            da, db = diag_a[i], diag_b[i]
            print(f"  {i+1:>3} | {bin_a[i]:>3} {da['max_v']:>5} "
                  f"{da['bright_px']:>5} | {bin_b[i]:>3} "
                  f"{db['max_v']:>5} {db['bright_px']:>5}")
        print()

        # --- Mostrar visualmente ---
        root = tk.Tk(); root.withdraw()
        ver = messagebox.askyesno(
            "Resultado",
            f"A = {bin_a} ({dec_a})\n"
            f"B = {bin_b} ({dec_b})\n\n"
            f"Suma = {bin_sum} ({total})\n\n"
            f"¿Ver imágenes con los bits detectados?"
        )
        root.destroy()

        if ver:
            vis_a = visualize_bits(img_a, n_bits, bin_a, "A")
            vis_b = visualize_bits(img_b, n_bits, bin_b, "B")
            header = np.zeros((60, max(vis_a.shape[1], vis_b.shape[1]), 3),
                              dtype=np.uint8)
            txt = f"{bin_a}({dec_a}) + {bin_b}({dec_b}) = {bin_sum}({total})"
            cv2.putText(header, txt, (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            combined = np.vstack([header, vis_a, vis_b])
            cv2.imshow("Sumador binario", combined)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        # --- ¿Otra suma? ---
        root = tk.Tk(); root.withdraw()
        otra = messagebox.askyesno("Continuar", "¿Hacer otra suma?")
        root.destroy()
        if not otra:
            print("Listo.")
            return


if __name__ == "__main__":
    main()