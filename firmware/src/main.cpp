#include <Arduino.h>
#include <WiFi.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include "camera_pins.h"
#include "wifi_config.h"

static const char *AP_NAME = "WALL-A-CAM";
static const char *AP_PASSWORD = "walla2026";
static esp_err_t cameraError = ESP_FAIL;
static uint16_t sensorPid = 0;
static bool accessPointMode = false;

static String deviceIP() {
  return accessPointMode ? WiFi.softAPIP().toString() : WiFi.localIP().toString();
}

static esp_err_t statusHandler(httpd_req_t *request) {
  char body[280];
  snprintf(body, sizeof(body),
    "{\"firmware\":\"wall-a-camera-0.1\",\"camera_ready\":%s,\"camera_error\":%d,"
    "\"sensor_pid\":%u,\"psram_bytes\":%u,\"flash_bytes\":%u,\"ip\":\"%s\",\"mode\":\"%s\"}",
    cameraError == ESP_OK ? "true" : "false", int(cameraError), sensorPid,
    unsigned(ESP.getPsramSize()), unsigned(ESP.getFlashChipSize()), deviceIP().c_str(), accessPointMode ? "ap" : "station");
  httpd_resp_set_type(request, "application/json");
  httpd_resp_set_hdr(request, "Cache-Control", "no-store");
  return httpd_resp_send(request, body, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t captureHandler(httpd_req_t *request) {
  if (cameraError != ESP_OK) {
    httpd_resp_set_status(request, "503 Service Unavailable");
    return httpd_resp_sendstr(request, "Camera unavailable. Check /status and serial log.");
  }
  // Drop the buffered frame so this request obtains a more recent exposure.
  camera_fb_t *frame = esp_camera_fb_get();
  if (frame) esp_camera_fb_return(frame);
  frame = esp_camera_fb_get();
  if (!frame) {
    httpd_resp_set_status(request, "503 Service Unavailable");
    return httpd_resp_sendstr(request, "Camera capture failed.");
  }
  if (frame->format != PIXFORMAT_JPEG) {
    esp_camera_fb_return(frame);
    httpd_resp_set_status(request, "500 Internal Server Error");
    return httpd_resp_sendstr(request, "Unexpected camera format.");
  }
  httpd_resp_set_type(request, "image/jpeg");
  httpd_resp_set_hdr(request, "Cache-Control", "no-store");
  const esp_err_t result = httpd_resp_send(request, reinterpret_cast<const char *>(frame->buf), frame->len);
  Serial.printf("CAPTURE %ux%u %u bytes result=%d\n", unsigned(frame->width), unsigned(frame->height), unsigned(frame->len), int(result));
  esp_camera_fb_return(frame);
  return result;
}

static esp_err_t indexHandler(httpd_req_t *request) {
  httpd_resp_set_type(request, "text/html; charset=utf-8");
  return httpd_resp_sendstr(request,
    "<!doctype html><meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>WALL-A Camera</title><body style='font:18px system-ui;background:#111715;color:#edf1e7;padding:24px'>"
    "<h1>WALL-A Camera</h1><p><a style='color:#d5f78a' href='/status'>Camera status</a></p>"
    "<button onclick=\"document.getElementById('photo').src='/capture?t='+Date.now()\">Take photo</button>"
    "<p><img id='photo' alt='Press Take photo' style='max-width:100%'></p>"
    "<p>Python panel camera address: <b id='ip'></b></p>"
    "<script>document.getElementById('ip').textContent=location.hostname</script>");
}

static esp_err_t initCamera() {
  if (!psramFound()) {
    Serial.println("CAMERA_ERROR PSRAM not available; check qio_opi build settings.");
    return ESP_ERR_NO_MEM;
  }
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = CAM_D0;
  config.pin_d1 = CAM_D1;
  config.pin_d2 = CAM_D2;
  config.pin_d3 = CAM_D3;
  config.pin_d4 = CAM_D4;
  config.pin_d5 = CAM_D5;
  config.pin_d6 = CAM_D6;
  config.pin_d7 = CAM_D7;
  config.pin_xclk = CAM_XCLK;
  config.pin_pclk = CAM_PCLK;
  config.pin_vsync = CAM_VSYNC;
  config.pin_href = CAM_HREF;
  config.pin_sccb_sda = CAM_SDA;
  config.pin_sccb_scl = CAM_SCL;
  config.pin_pwdn = CAM_PWDN;
  config.pin_reset = CAM_RESET;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  const esp_err_t result = esp_camera_init(&config);
  if (result != ESP_OK) {
    Serial.printf("CAMERA_ERROR init=0x%x\n", unsigned(result));
    return result;
  }
  sensor_t *sensor = esp_camera_sensor_get();
  if (sensor) sensorPid = sensor->id.PID;
  Serial.printf("CAMERA_READY sensor_pid=0x%04x frame=640x480\n", sensorPid);
  // Verify that the sensor can supply a JPEG, rather than only responding on SCCB.
  camera_fb_t *frame = esp_camera_fb_get();
  if (!frame) {
    Serial.println("CAMERA_ERROR first frame missing");
    esp_camera_deinit();
    return ESP_FAIL;
  }
  Serial.printf("FIRST_FRAME %ux%u %u bytes\n", unsigned(frame->width), unsigned(frame->height), unsigned(frame->len));
  const bool valid = frame->format == PIXFORMAT_JPEG && frame->len > 4 && frame->buf[0] == 0xff && frame->buf[1] == 0xd8;
  esp_camera_fb_return(frame);
  if (!valid) {
    esp_camera_deinit();
    return ESP_FAIL;
  }
  return ESP_OK;
}

void setup() {
  Serial.begin(115200);
  delay(800);
  Serial.printf("\nWALL_A_CAMERA_BOOT flash=%u psram=%u\n", unsigned(ESP.getFlashChipSize()), unsigned(ESP.getPsramSize()));
  cameraError = initCamera();
  if (strlen(WALL_A_WIFI_SSID) > 0) {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WALL_A_WIFI_SSID, WALL_A_WIFI_PASSWORD);
    Serial.println("WIFI_CONNECTING timeout=25s");
    const uint32_t started = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - started < 25000) delay(250);
  }
  if (WiFi.status() != WL_CONNECTED) {
    accessPointMode = true;
    WiFi.disconnect();
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(IPAddress(192,168,4,1), IPAddress(192,168,4,1), IPAddress(255,255,255,0));
    if (!WiFi.softAP(AP_NAME, AP_PASSWORD, 6, false, 2)) {
      Serial.println("AP_ERROR failed to start");
      return;
    }
  }
  WiFi.setSleep(false);
  httpd_config_t settings = HTTPD_DEFAULT_CONFIG();
  settings.stack_size = 8192;
  settings.send_wait_timeout = 10;
  httpd_handle_t server = nullptr;
  if (httpd_start(&server, &settings) != ESP_OK) {
    Serial.println("HTTP_ERROR failed to start");
    return;
  }
  httpd_uri_t root = {};
  root.uri = "/"; root.method = HTTP_GET; root.handler = indexHandler;
  httpd_register_uri_handler(server, &root);
  httpd_uri_t status = {};
  status.uri = "/status"; status.method = HTTP_GET; status.handler = statusHandler;
  httpd_register_uri_handler(server, &status);
  httpd_uri_t capture = {};
  capture.uri = "/capture"; capture.method = HTTP_GET; capture.handler = captureHandler;
  httpd_register_uri_handler(server, &capture);
  Serial.printf("NETWORK_READY mode=%s ip=%s camera_ready=%s\n", accessPointMode ? "ap" : "station", deviceIP().c_str(), cameraError == ESP_OK ? "true" : "false");
}

void loop() { delay(100); }
