/**
 * model_data.h
 * 
 * Instructions:
 * 1. Train your MobileNetV2-SSD model (96x96 input) for Cat Detection.
 * 2. Convert .tflite model to C array using:
 *    xxd -i model.tflite > model_data.h
 * 3. Paste the content of the generated array below.
 * 4. Ensure the array is named 'model'.
 */

#ifndef MODEL_DATA_H
#define MODEL_DATA_H

// Placeholder for model data. Replace this array with your actual model.
// This is a dummy array to allow compilation.
const unsigned char model[] = {
  0x1C, 0x00, 0x00, 0x00, 0x54, 0x46, 0x4C, 0x33, 0x00, 0x00, 0x00, 0x00,
  0x14, 0x00, 0x20, 0x00, 0x1C, 0x00, 0x18, 0x00, 0x0C, 0x00, 0x08, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
  // ... (Rest of your model data goes here) ...
};

const unsigned int model_len = 32; // Update this to actual model size

#endif