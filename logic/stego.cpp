#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#include <iostream>
#include <vector>
#include <string>

void encode(std::string input, std::string msg, std::string output) {
    int w, h, c;
    unsigned char* img = stbi_load(input.c_str(), &w, &h, &c, 0);
    if (!img) { std::cerr << "Load failed"; exit(1); }

    msg += "###"; // Delimiter
    std::vector<int> bits;
    for (char ch : msg) {
        for (int i = 7; i >= 0; --i) bits.push_back((ch >> i) & 1);
    }

    if (bits.size() > (size_t)w * h * c) { std::cerr << "Too long"; exit(1); }

    for (size_t i = 0; i < bits.size(); ++i) {
        img[i] = (img[i] & 0xFE) | bits[i];
    }

    stbi_write_png(output.c_str(), w, h, c, img, w * c);
    stbi_image_free(img);
}

void decode(std::string input) {
    int w, h, c;
    unsigned char* img = stbi_load(input.c_str(), &w, &h, &c, 0);
    if (!img) exit(1);

    std::string msg = "";
    unsigned char ch = 0;
    int bit_count = 0;

    for (int i = 0; i < w * h * c; ++i) {
        ch = (ch << 1) | (img[i] & 1);
        bit_count++;
        if (bit_count == 8) {
            msg += (char)ch;
            ch = 0; bit_count = 0;
            if (msg.size() >= 3 && msg.substr(msg.size() - 3) == "###") {
                std::cout << msg.substr(0, msg.size() - 3);
                stbi_image_free(img);
                return;
            }
        }
    }
    stbi_image_free(img);
}

int main(int argc, char* argv[]) {
    if (argc < 2) return 1;
    std::string mode = argv[1];
    if (mode == "-e" && argc == 5) encode(argv[2], argv[3], argv[4]);
    else if (mode == "-d" && argc == 3) decode(argv[2]);
    return 0;
}
