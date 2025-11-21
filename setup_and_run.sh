#!/bin/bash

echo "--- 1. ⚙️ Tạo Môi Trường Ảo (.venv) ---"
python3 -m venv .venv
echo "--- ✅ Đã tạo .venv ---"

echo "\n--- 2. ⚡ Kích Hoạt Môi Trường Ảo ---"
source .venv/bin/activate
echo "--- ✅ Đã kích hoạt .venv ---"

echo "\n--- 3. 📦 Cài Đặt Thư Viện từ requirements.txt ---"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "ERROR: ❌ Không tìm thấy file requirements.txt!"
    exit 1
fi
echo "--- ✅ Đã cài đặt các thư viện ---"

echo "\n--- 4. 🤖 Cài Đặt Trình Duyệt Playwright ---"
playwright install
echo "--- ✅ Đã cài đặt Playwright ---"

echo "\n--- 5. 🔑 Kiểm Tra File .env ---"
if [ -f ".env" ]; then
    echo "--- ✅ Đã tìm thấy file .env ---"
else
    echo "ERROR: ❌ Không tìm thấy file .env!"
    echo "Vui lòng tạo file .env và điền API keys trước khi chạy."
    exit 1
fi

echo "\n--- 🚀 BẮT ĐẦU CHẠY SCRIPT scraper.py ---"
python scraper.py
echo "\n--- ✨ SCRIPT ĐÃ CHẠY XONG ---"