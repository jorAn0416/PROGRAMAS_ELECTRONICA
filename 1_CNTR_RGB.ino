// ============================================================
//  Control de LED RGB en ciclo - Práctica 5 (identificación de color)
//  Cambia de color automáticamente y acepta comandos por serial
// ============================================================

// --- Pines PWM (ajusta según tu placa) ---
#define PIN_R 4
#define PIN_G 5
#define PIN_B 6

// --- Tipo de LED: 0 = cátodo común, 1 = ánodo común ---
#define COMMON_ANODE 0

// --- Tiempo por color (ms) ---
unsigned long dwellMs   = 3000;
unsigned long lastChange = 0;
int  currentIndex = 0;
bool autoCycle    = true;

struct Color { const char* name; uint8_t r, g, b; };

// Los nombres coinciden EXACTAMENTE con los que imprime el
// detector de Python (detector_led.py)
Color colors[] = {
  {"rojo",     255,   0,   0},
  {"naranja",  255, 100,   0},
  {"amarillo", 255, 255,   0},
  {"verde",      0, 255,   0},
  {"cian",       0, 255, 255},
  {"azul",       0,   0, 255},
  {"morado",   128,   0, 255},
  {"rosa",     255, 100, 180},
  {"blanco",   255, 255, 255},
  {"negro",      0,   0,   0},   // LED apagado
  {"gris",     128, 128, 128},
};
const int NUM_COLORS = sizeof(colors) / sizeof(colors[0]);

void setRGB(uint8_t r, uint8_t g, uint8_t b) {
  #if COMMON_ANODE
    analogWrite(PIN_R, 255 - r);
    analogWrite(PIN_G, 255 - g);
    analogWrite(PIN_B, 255 - b);
  #else
    analogWrite(PIN_R, r);
    analogWrite(PIN_G, g);
    analogWrite(PIN_B, b);
  #endif
}

void showColor(int index, bool notify = true) {
  if (index < 0 || index >= NUM_COLORS) return;
  Color c = colors[index];
  setRGB(c.r, c.g, c.b);
  if (notify) {
    Serial.print("COLOR:");
    Serial.println(c.name);   // Python puede leer esta línea
  }
}

void handleCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  // C:<nombre>  -> fija un color específico
  if (cmd.startsWith("C:") || cmd.startsWith("c:")) {
    String name = cmd.substring(2); name.trim();
    for (int i = 0; i < NUM_COLORS; i++) {
      if (name.equalsIgnoreCase(colors[i].name)) {
        autoCycle = false;
        currentIndex = i;
        showColor(i);
        return;
      }
    }
    Serial.print("Color desconocido: "); Serial.println(name);
    return;
  }

  // N:<ms>  -> tiempo por color
  if (cmd.startsWith("N:") || cmd.startsWith("n:")) {
    unsigned long ms = cmd.substring(2).toInt();
    if (ms >= 200 && ms <= 60000) {
      dwellMs = ms;
      Serial.printf("Dwell: %lu ms\n", dwellMs);
    } else {
      Serial.println("N fuera de rango (200-60000)");
    }
    return;
  }

  // P  -> pausa/reanuda
  if (cmd == "P" || cmd == "p") {
    autoCycle = !autoCycle;
    Serial.printf("Auto-ciclo: %s\n", autoCycle ? "ON" : "OFF");
    lastChange = millis();
    return;
  }

  // A  -> reactiva el ciclo
  if (cmd == "A" || cmd == "a") {
    autoCycle = true;
    lastChange = millis();
    Serial.println("Auto-ciclo ON");
    return;
  }

  // L  -> lista los colores disponibles
  if (cmd == "L" || cmd == "l") {
    for (int i = 0; i < NUM_COLORS; i++)
      Serial.printf("  %d: %s\n", i, colors[i].name);
    return;
  }

  Serial.print("Comando no reconocido: "); Serial.println(cmd);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_R, OUTPUT);
  pinMode(PIN_G, OUTPUT);
  pinMode(PIN_B, OUTPUT);
  setRGB(0, 0, 0);
  delay(500);

  Serial.println("=== RGB LED controller ===");
  Serial.println("Comandos:");
  Serial.println("  C:<nombre>  - fija color (ej: C:rojo)");
  Serial.println("  N:<ms>      - tiempo por color (ej: N:5000)");
  Serial.println("  P           - pausa/reanuda ciclo");
  Serial.println("  A           - activa ciclo automático");
  Serial.println("  L           - lista colores");
  Serial.println("Colores:");
  for (int i = 0; i < NUM_COLORS; i++)
    Serial.printf("  %d: %s\n", i, colors[i].name);

  currentIndex = 0;
  showColor(0);           // arranca en rojo
  lastChange = millis();
}

void loop() {
  // Atiende comandos seriales
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    handleCommand(cmd);
  }

  // Ciclo automático
  if (autoCycle && millis() - lastChange >= dwellMs) {
    currentIndex = (currentIndex + 1) % NUM_COLORS;
    showColor(currentIndex);
    lastChange = millis();
  }
}
