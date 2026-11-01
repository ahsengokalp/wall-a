#pragma once

// Candidate GOOUUU layout from Espressif's esp32-camera camera_pinout.h.
// Matches the camera-marked GPIO group in the supplied PCB photographs.
// Exact board brand remains unknown; sensor probe and frame capture validate it.
// No SD card or other peripherals are initialized by this firmware.
constexpr int CAM_PWDN = -1;
constexpr int CAM_RESET = -1;
constexpr int CAM_XCLK = 15;
constexpr int CAM_SDA = 4;
constexpr int CAM_SCL = 5;
constexpr int CAM_D0 = 11;
constexpr int CAM_D1 = 9;
constexpr int CAM_D2 = 8;
constexpr int CAM_D3 = 10;
constexpr int CAM_D4 = 12;
constexpr int CAM_D5 = 18;
constexpr int CAM_D6 = 17;
constexpr int CAM_D7 = 16;
constexpr int CAM_VSYNC = 6;
constexpr int CAM_HREF = 7;
constexpr int CAM_PCLK = 13;
