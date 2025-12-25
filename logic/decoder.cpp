#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#include <iostream>
#include <vector>
#include <string>

int main(int argc, char* argv[]) {
    if (argc < 2) return 1;

    const char* input_path = argv[1];

    // 1. Load the encoded image
    int width, height, channels;
    unsigned char* img = stbi_load(input_path, &width, &height, &channels, 0);
    if (!img) return 1;

    std::string secret_text = "";
    unsigned char current_char = 0;
    int bit_count = 0;

    // 2. Iterate through pixels to extract bits
    int total_pixels = width * height * channels;
    for (int i = 0; i < total_pixels; ++i) {
        // Grab the LSB
        int bit = img[i] & 1;

        // Shift current_char and add the bit
        current_char = (current_char << 1) | bit;
        bit_count++;

        // Every 8 bits, we have a full character
        if (bit_count == 8) {
            secret_text += (char)current_char;
            current_char = 0;
            bit_count = 0;

            // Check if we found our delimiter
            if (secret_text.size() >= 3 && secret_text.substr(secret_text.size() - 3) == "###") {
                // Remove delimiter and print
                std::cout << secret_text.substr(0, secret_text.size() - 3);
                stbi_image_free(img);
                return 0;
            }
        }
    }

    stbi_image_free(img);
    return 0;
}
