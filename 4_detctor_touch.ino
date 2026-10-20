// --- Práctica 4: Sensor de nivel de agua capacitivo ---
// Conecta el electrodo de papel aluminio al GPIO 8 (TOUCH8)

const int touchPin = 8; // Pin táctil (ajusta si usas otro)
int umbral = 40000;     // Umbral de calibración (ajústalo según tus lecturas)

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Sensor de nivel de agua con ESP32-S3");
  Serial.println("Acerca/aleja el agua para ver los valores...");
}

void loop() {
  // touchRead() devuelve un valor que cambia según la capacitancia.
  // En el ESP32-S3, el valor *baja* cuando tocas/llenas.
  int valor = touchRead(touchPin);

  Serial.print("Valor táctil: ");
  Serial.print(valor);

  // Lógica de decisión (ajusta el umbral según tu calibración)
  if (valor < umbral) {
    Serial.println("  -> ¡Recipiente LLENO detectado!");
  } else {
    Serial.println("  -> Recipiente vacío (o nivel bajo).");
  }

  delay(500);
}