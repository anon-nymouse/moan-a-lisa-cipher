#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#include <iostream>
#include <vector>
#include <string>

int main(int argc, char* argv[]) {
    if (argc < 4) return 1;

    const char* input_path = argv[1];
    std::string secret_text = argv[2];
    const char* output_path = argv[3];

    // 1. Load Image
    int width, height, channels;
    unsigned char* img = stbi_load(input_path, &width, &height, &channels, 0);
    if (!img) return 1;

    // 2. Convert text to bits
    std::vector<int> bits;
    secret_text += "###"; // Delimiter
    for (char c : secret_text) {
        for (int i = 7; i >= 0; --i) {
            bits.push_back((c >> i) & 1);
        }
    }

    // 3. Embed bits into pixels
    if (bits.size() > width * height * channels) {
        stbi_image_free(img);
        return 2;
    }

    for (size_t i = 0; i < bits.size(); ++i) {
        // Clear the LSB and OR it with our secret bit
        img[i] = (img[i] & 0xFE) | bits[i];
    }

    // 4. Save and Clean up
    stbi_write_png(output_path, width, height, channels, img, width * channels);
    stbi_image_free(img);

    return 0;
}
