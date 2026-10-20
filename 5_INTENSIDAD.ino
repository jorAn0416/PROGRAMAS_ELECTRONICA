#include "esp_camera.h"

// --- Configuración de pines (tu misma config OV3660) ---
#define PWDN_GPIO_NUM    -1
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM    15
#define SIOD_GPIO_NUM    4
#define SIOC_GPIO_NUM    5
#define Y9_GPIO_NUM      16
#define Y8_GPIO_NUM      17
#define Y7_GPIO_NUM      18
#define Y6_GPIO_NUM      12
#define Y5_GPIO_NUM      10
#define Y4_GPIO_NUM      8
#define Y3_GPIO_NUM      9
#define Y2_GPIO_NUM      11
#define VSYNC_GPIO_NUM   6
#define HREF_GPIO_NUM    7
#define PCLK_GPIO_NUM    13

// ===== PARÁMETROS AJUSTABLES =====
#define FIXED_AEC_VALUE   300   // 0-1200. Baja si satura, sube si no ve nada
#define FIXED_AGC_GAIN    0     // 0-30. Generalmente 0
#define ROI_FRACTION      0.30  // Fracción central a analizar (0.30 = 30%)

void setup() {
  Serial.begin(115200);
  delay(1000);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;

  // GRAYSCALE: cada píxel es directamente un valor 0-255 de brillo
  // Más rápido que JPEG y mucho más simple de leer
  config.pixel_format = PIXFORMAT_GRAYSCALE;
  config.frame_size   = FRAMESIZE_QVGA;   // 320x240 es suficiente
  config.fb_count     = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Error al inicializar cámara: 0x%x\n", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  s->set_gain_ctrl(s, 0);      // AGC off
  s->set_exposure_ctrl(s, 0);  // AEC off
  s->set_whitebal(s, 0);
  s->set_awb_gain(s, 0);
  s->set_bpc(s, 0);
  s->set_wpc(s, 0);
  s->set_lenc(s, 0);

  // Exposición fija: es lo que hace que el brillo sea proporcional al LED
  s->set_aec_value(s, FIXED_AEC_VALUE);
  s->set_agc_gain(s, FIXED_AGC_GAIN);
}

void loop() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println(0);
    delay(500);
    return;
  }

  // Región de interés: cuadrado central
  int cx = fb->width  / 2;
  int cy = fb->height / 2;
  int r  = (int)(fb->width * ROI_FRACTION / 2);

  uint32_t sum = 0;
  uint32_t count = 0;
  for (int y = cy - r; y < cy + r; y++) {
    for (int x = cx - r; x < cx + r; x++) {
      sum += fb->buf[y * fb->width + x];   // 0-255 directo
      count++;
    }
  }
  uint32_t avg = count ? (sum / count) : 0;

  // Igual que tu ejemplo: solo el número y salto de línea
  Serial.println(avg);

  esp_camera_fb_return(fb);
  delay(500);
}