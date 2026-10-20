#!/usr/bin/env python3
"""
Práctica 2 - Lector de LEDs binarios (caja oscura con barreras)
- Pregunta cuántos bits
- Diálogo para seleccionar foto
- Imprime binario y decimal en la terminal
"""
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox


def ask_num_bits():
    root = tk.Tk()
    root.withdraw()
    n = simpledialog.askinteger(
        "Número de bits",
        "¿Cuántos LEDs (bits) tiene tu arreglo?",
        minvalue=1, maxvalue=32, initialvalue=4,
    )
    root.destroy()
    return n


def ask_image_path():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Selecciona la foto del arreglo de LEDs",
        filetypes=[
            ("Imágenes", "*.jpg *.jpeg *.png *.bmp"),
            ("Todos los archivos", "*.*"),
        ],
    )
    root.destroy()
    return path


def read_binary(img, n_bits, margin=0.05, inner_margin=0.15,
                y_band=(0.20, 0.80), v_thresh=200, min_pixels=15):
    """
    Parámetros ajustables:
      margin      : % a ignorar en cada lado de la imagen
      inner_margin: % a ignorar dentro de cada segmento (protege contra barreras)
      y_band      : banda vertical a analizar (ignora arriba/abajo)
      v_thresh    : brillo mínimo (0-255) para considerar un píxel "encendido"
      min_pixels  : mínimo de píxeles brillantes para declarar bit = 1
    """
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


def visualize(img, n_bits, binary, margin=0.05, inner_margin=0.15,
              y_band=(0.20, 0.80)):
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
    cv2.putText(vis, f"Bin: {binary}   Dec: {total}",
                (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (0, 255, 255), 2)
    return vis


def main():
    n_bits = ask_num_bits()
    if not n_bits:
        print("Cancelado.")
        return

    while True:
        path = ask_image_path()
        if not path:
            print("Cancelado.")
            return

        img = cv2.imread(path)
        if img is None:
            print(f"❌ No se pudo leer {path}")
            continue

        binary, decimal, diag = read_binary(img, n_bits)

        print("\n" + "=" * 45)
        print(f"  Imagen:   {path}")
        print(f"  Binario:  {binary}   (izq → der, izq = MSB)")
        print(f"  Decimal:  {decimal}")
        print("=" * 45)
        for i, d in enumerate(diag):
            print(f"  LED {i+1}: bit={binary[i]}  "
                  f"maxV={d['max_v']:3d}  bright_px={d['bright_px']}")
        print()

        root = tk.Tk(); root.withdraw()
        ver = messagebox.askyesno("Resultado",
                                   "¿Ver imagen con los bits detectados?")
        root.destroy()
        if ver:
            vis = visualize(img, n_bits, binary)
            cv2.imshow("Detección de bits", vis)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        root = tk.Tk(); root.withdraw()
        otra = messagebox.askyesno("Continuar", "¿Leer otra foto?")
        root.destroy()
        if not otra:
            print("Listo.")
            return


if __name__ == "__main__":
    main()