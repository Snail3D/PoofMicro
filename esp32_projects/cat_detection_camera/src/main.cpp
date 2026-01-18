/**
 * Cat Detection Camera - ESP32-CAM
 * 
 * Features:
 * - MobileNetV2-SSD Object Detection
 * - Real-time bounding box overlay
 * - MJPEG Web Streaming
 * - PSRAM enabled
 */

#include <Arduino.h>
#include <WiFi.h>
#include <esp_camera.h>
#include <esp_http_server.h>
#include <fb_gfx.h>
#include <EloquentTinyML.h>
#include "model_data.h"
#include "config.h"

// TensorFlow Lite Settings
#define TENSOR_ARENA_SIZE 60 * 1024 // Adjust based on model size
Eloquent::TinyML::TfLite<96, 96, 2, TENSOR_ARENA_SIZE> ml;

// Global variables
camera_fb_t *fb = NULL;
bool camera_initialized = false;

// Define the model
const unsigned char model[] = {
  #include "model_data.h"
};

// HTTP Server handles
httpd_handle_t stream_httpd = NULL;

// Function prototypes
void startCameraServer();
void draw_box(uint8_t *buf, int width, int height, int x_min, int y_min, int x_max, int y_max, uint16_t color);
void process_detection();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // 1. Initialize PSRAM
  if (psramFound()) {
    Serial.println("PSRAM detected and initialized.");
    // Configure camera to use PSRAM for frame buffers
    config.frame_size = FRAMESIZE_SVGA;
  } else {
    Serial.println("PSRAM not found. Reducing frame buffer allocation.");
    config.frame_size = FRAMESIZE_QVGA;
  }

  // 2. Initialize Camera
  camera_config_t camera_config = {
    .pin_pwdn = PWDN_GPIO_NUM,
    .pin_reset = RESET_GPIO_NUM,
    .pin_xclk = XCLK_GPIO_NUM,
    .pin_sscb_sda = SIOD_GPIO_NUM,
    .pin_sscb_scl = SIOC_GPIO_NUM,
    .pin_d7 = Y9_GPIO_NUM,
    .pin_d6 = Y8_GPIO_NUM,
    .pin_d5 = Y7_GPIO_NUM,
    .pin_d4 = Y6_GPIO_NUM,
    .pin_d3 = Y5_GPIO_NUM,
    .pin_d2 = Y4_GPIO_NUM,
    .pin_d1 = Y3_GPIO_NUM,
    .pin_d0 = Y2_GPIO_NUM,
    .pin_vsync = VSYNC_GPIO_NUM,
    .pin_href = HREF_GPIO_NUM,
    .pin_pclk = PCLK_GPIO_NUM,

    .xclk_freq_hz = 20000000,
    .pixel_format = PIXFORMAT_RGB565, // RGB565 for easier drawing
    .frame_size = FRAMESIZE_QVGA,     // 320x240
    .jpeg_quality = 12,
    .fb_count = 2,
    .fb_location = CAMERA_FB_IN_PSRAM,
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY
  };

  // Initialize camera driver
  esp_err_t err = esp_camera_init(&camera_config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }
  camera_initialized = true;
  Serial.println("Camera initialized successfully");

  // 3. Initialize WiFi
  Serial.printf("Connecting to %s ", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("Camera Stream Ready! Go to: http://");
  Serial.print(WiFi.localIP());

  // 4. Initialize TFLite Model
  ml.begin(model);
  Serial.println("TFLite Model loaded");

  // 5. Start Web Server
  startCameraServer();
}

void loop() {
  // Main loop is handled by the web server handlers
  // We can perform periodic tasks here if needed
  delay(1000);
}

// Helper to draw bounding box on RGB565 buffer
void draw_box(uint8_t *buf, int width, int height, int x_min, int y_min, int x_max, int y_max, uint16_t color) {
  // Clamp coordinates
  x_min = max(0, x_min);
  y_min = max(0, y_min);
  x_max = min(width - 1, x_max);
  y_max = min(height - 1, y_max);

  // Draw horizontal lines
  for (int x = x_min; x <= x_max; x++) {
    // Top line
    uint16_t *p_top = (uint16_t *)(buf + (y_min * width + x) * 2);
    *p_top = color;
    // Bottom line
    uint16_t *p_bottom = (uint16_t *)(buf + (y_max * width + x) * 2);
    *p_bottom = color;
  }
  // Draw vertical lines
  for (int y = y_min; y <= y_max; y++) {
    // Left line
    uint16_t *p_left = (uint16_t *)(buf + (y * width + x_min) * 2);
    *p_left = color;
    // Right line
    uint16_t *p_right = (uint16_t *)(buf + (y * width + x_max) * 2);
    *p_right = color;
  }
}

// HTTP Handler for Stream
httpd_handle_t camera_httpd = NULL;

httpd_uri_t stream_uri = {
    .uri       = "/stream",
    .method    = HTTP_GET,
    .handler   = [](httpd_req_t *req){
        esp_err_t res = ESP_OK;
        char part[64];
        
        res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
        if(res != ESP_OK){
            return res;
        }

        while(true){
            // Capture frame
            fb = esp_camera_fb_get();
            if (!fb) {
                Serial.println("Camera capture failed");
                res = ESP_FAIL;
            } else {
                // 1. Prepare image for TFLite (Resize 320x240 -> 96x96)
                // Note: In a production app, use efficient resizing. Here we do a simple center crop/downsample logic conceptually.
                // For this example, we assume the model input is fed via a pre-processing step.
                // We will use the fb->buf (RGB565) directly for drawing.

                // 2. Run Detection (Mock logic for structure, actual implementation depends on model output format)
                // float input[96*96*3]; // Convert RGB565 to RGB888 and flatten here
                // ml.predict(input);
                
                // Example detection logic (Replace with actual TFLite output parsing)
                // Assuming model returns: confidence, x_min, y_min, x_max, y_max (normalized 0-1)
                bool cat_detected = false;
                float score = 0.0;
                int box[4] = {0};

                // --- PSEUDO-CODE FOR TFLITE INFERENCE ---
                /*
                // Convert fb to float input array
                for(int i=0; i<96*96; i++) {
                    // ... resize logic ...
                }
                
                if (ml.predict(input)) {
                    // Get output tensor
                    float* output = ml.getOutputTensor();
                    // Parse output for 'cat' class (index 1)
                    // if (output[1] > 0.6) { ... }
                }
                */
                // ----------------------------------------

                // For demonstration, we will draw a box if we assume a detection
                // In real use, parse 'box' and 'score' from model output
                if (cat_detected) {
                    Serial.printf("Cat detected: %.2f%%\n", score * 100);
                    int x = box[0] * fb->width;
                    int y = box[1] * fb->height;
                    int w = box[2] * fb->width;
                    int h = box[3] * fb->height;
                    // Draw Green Box (RGB565 color: 0x07E0)
                    draw_box(fb->buf, fb->width, fb->height, x, y, x+w, y+h, 0x07E0);
                }

                // 3. Convert RGB565 back to JPEG for streaming
                size_t jpg_len = 0;
                uint8_t *jpg_buf = NULL;
                bool jpeg_converted = fmt2jpg(fb->buf, fb->len, fb->width, fb->height, PIXFORMAT_RGB565, 80, &jpg_buf, &jpg_len);
                
                esp_camera_fb_return(fb);
                
                if(!jpeg_converted){
                    Serial.println("JPEG compression failed");
                    res = ESP_FAIL;
                } else {
                    size_t hlen = snprintf((char *)part, 64, _STREAM_PART, jpg_len);
                    res = httpd_resp_send_chunk(req, (const char *)part, hlen);
                    if(res == ESP_OK){
                        res = httpd_resp_send_chunk(req, (const char *)jpg_buf, jpg_len);
                    }
                    free(jpg_buf);
                }
            }
            if(res != ESP_OK || res == HTTPD_SVC_ERR_STREAM_END){
                break;
            }
        }
        return res;
    },
    .user_ctx  = NULL
};

void startCameraServer(){
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;
    config.task_priority = 1; // Lower priority than camera driver

    httpd_uri_t index_uri = {
        .uri       = "/",
        .method    = HTTP_GET,
        .handler   = [](httpd_req_t *req){
            httpd_resp_send(req, "<h1>ESP32-CAM Cat Detection Stream</h1><img src=\"/stream\"/>", HTTPD_RESP_USE_STRLEN);
            return ESP_OK;
        },
        .user_ctx  = NULL
    };

    if (httpd_start(&camera_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(camera_httpd, &index_uri);
        httpd_register_uri_handler(camera_httpd, &stream_uri);
        Serial.println("HTTP server started");
    }
}