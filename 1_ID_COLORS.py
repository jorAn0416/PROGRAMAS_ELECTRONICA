import cv2
import numpy as np
import csv
import argparse
from pathlib import Path
from collections import Counter

# ---------------------------------------------------------------
# Rangos HSV ajustados (S_min más bajo para tu montaje)
# ---------------------------------------------------------------
def classify_hsv(h, s, v):
    if v < 40:
        return "negro"
    if s < 30:                       # ← antes era 40
        return "blanco" if v > 200 else "gris"
    if h < 8 or h >= 170: return "rojo"
    if h < 20:            return "naranja"
    if h < 35:            return "amarillo"
    if h < 85:            return "verde"
    if h < 100:           return "cian"
    if h < 130:           return "azul"
    if h < 160:           return "morado"
    return "rosa"


# ---------------------------------------------------------------
# Análisis con filtrado de sobreexpuestos
# ---------------------------------------------------------------
def dominant_color_hsv(image_bgr, k=5, crop=0.7,
                       v_overexposed=250, s_min=25, v_min=40):
    h, w = image_bgr.shape[:2]
    ch, cw = int(h * crop), int(w * crop)
    y0, x0 = (h - ch) // 2, (w - cw) // 2
    roi = image_bgr[y0:y0 + ch, x0:x0 + cw]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    # Máscara: descartamos píxeles quemados, oscuros o casi sin color
    valid = (V < v_overexposed) & (V > v_min) & (S > s_min)
    n_valid = int(valid.sum())
    n_total = valid.size

    diagnostics = {
        "V_mean": float(V.mean()),
        "S_mean": float(S.mean()),
        "pct_quemado": float((V >= v_overexposed).mean() * 100),
        "pct_valido":  float(n_valid / n_total * 100) if n_total else 0.0,
    }

    # Caso 1: casi toda la imagen está oscura → LED apagado
    if V.mean() < v_min:
        return "negro", diagnostics

    # Caso 2: sobreexposición extrema (todo quemado) → bajar exposición
    if diagnostics["pct_quemado"] > 60:
        diagnostics["alerta"] = "IMAGEN SOBREEXPUESTA - baja exposición o intensidad del LED"
        return "blanco_quemado", diagnostics

    # Caso 3: no hay suficientes píxeles con color → probablemente blanco puro
    if n_valid < 200:
        return ("blanco" if V.mean() > 200 else "gris"), diagnostics

    # K-means sobre píxeles válidos
    pixels = hsv[valid].astype(np.float32)
    if len(pixels) > 20000:
        idx = np.random.choice(len(pixels), 20000, replace=False)
        pixels = pixels[idx]

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS
    )

    counts = Counter(labels.flatten())
    votes = Counter()
    for label, count in counts.items():
        hh, ss, vv = centers[label]
        votes[classify_hsv(hh, ss, vv)] += count

    winner = votes.most_common(1)[0][0]
    diagnostics["votos"] = dict(votes)
    return winner, diagnostics


# ---------------------------------------------------------------
# Procesar carpeta
# ---------------------------------------------------------------
def process_folder(folder, output_csv="resultados_led.csv",
                   show=False, crop=0.7, k=5, debug=False):
    folder = Path(folder)
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    images = sorted([p for p in folder.iterdir() if p.suffix.lower() in exts])
    if not images:
        print(f"Sin imágenes en {folder.resolve()}")
        return

    print(f"Procesando {len(images)} imágenes...\n")
    results = []
    for img_path in images:
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"No se pudo leer {img_path.name}")
            continue

        color, diag = dominant_color_hsv(img, k=k, crop=crop)
        results.append((img_path.name, color))

        line = f"✓ {img_path.name:30s} -> {color:15s}"
        if debug:
            line += (f" [V={diag['V_mean']:.0f} S={diag['S_mean']:.0f} "
                     f"quem={diag['pct_quemado']:.1f}% "
                     f"valid={diag['pct_valido']:.1f}%]")
        print(line)
        if "alerta" in diag:
            print(f"   {diag['alerta']}")

        if show:
            vis = img.copy()
            cv2.putText(vis, color.upper(), (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.imshow("LED RGB", vis)
            cv2.waitKey(400)

    if show:
        cv2.destroyAllWindows()

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["archivo", "color"])
        writer.writerows(results)
    print(f"\nResultados guardados en {output_csv}")


if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog, messagebox

    # Ocultar la ventanita principal de tkinter
    root = tk.Tk()
    root.withdraw()

    # 1) Pedir la carpeta de fotos
    carpeta = filedialog.askdirectory(
        title="Selecciona la carpeta con las fotos del LED"
    )
    if not carpeta:
        print("No seleccionaste carpeta. Saliendo.")
        raise SystemExit(0)

    # 2) Pedir dónde guardar el CSV (opcional, puedes cancelar)
    csv_path = filedialog.asksaveasfilename(
        title="¿Dónde guardar los resultados? (Cancelar = por defecto)",
        defaultextension=".csv",
        initialfile="resultados_led.csv",
        filetypes=[("Archivo CSV", "*.csv"), ("Todos", "*.*")],
    )
    if not csv_path:
        csv_path = "resultados_led.csv"

    # 3) Confirmación simple de opciones
    show = messagebox.askyesno(
        "Mostrar imágenes",
        "¿Quieres ver cada imagen mientras se procesa?"
    )

    # 4) Ejecutar
    process_folder(
        folder=carpeta,
        output_csv=csv_path,
        show=show,
        crop=0.7,
        k=5,
        debug=True,     # deja True para ver V, S, % quemado por imagen
    )