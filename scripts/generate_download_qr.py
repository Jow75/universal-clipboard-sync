"""Generate and verify high-contrast official download QR code."""
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
import cv2

CANONICAL_URL = "https://github.com/JOWGEI-hub/universal-clipboard-sync/releases/latest"

def generate_download_qr():
    # 1. Generate QR Code
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(CANONICAL_URL)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # 2. Compose with title and human-readable text
    padding = 30
    title_text = "Download Universal Clipboard Sync"
    url_text = CANONICAL_URL

    # Estimate text dimensions
    # Default font or standard font
    font = ImageFont.load_default()
    
    canvas_width = max(qr_img.width + padding * 2, 500)
    canvas_height = qr_img.height + 140

    canvas = Image.new("RGB", (canvas_width, canvas_height), color="white")
    draw = ImageDraw.Draw(canvas)

    # Center QR code
    qr_x = (canvas_width - qr_img.width) // 2
    qr_y = 60
    canvas.paste(qr_img, (qr_x, qr_y))

    # Draw Title (centered)
    draw.text((canvas_width // 2, 25), title_text, fill="black", anchor="mm", font=font)

    # Draw URL (centered)
    draw.text((canvas_width // 2, qr_y + qr_img.height + 25), url_text, fill="#1a56db", anchor="mm", font=font)
    draw.text((canvas_width // 2, qr_y + qr_img.height + 50), "Scan with your Android phone camera to download APK", fill="#6b7280", anchor="mm", font=font)

    # Save to locations
    os.makedirs("docs/assets", exist_ok=True)
    os.makedirs("dist", exist_ok=True)
    
    doc_path = "docs/assets/download_qr.png"
    dist_path = "dist/download_qr.png"
    
    canvas.save(doc_path)
    canvas.save(dist_path)
    print(f"Saved download QR to {doc_path} and {dist_path}")

    # 3. Verify decoding using OpenCV QRCodeDetector
    detector = cv2.QRCodeDetector()
    loaded_img = cv2.imread(dist_path)
    decoded_text, points, _ = detector.detectAndDecode(loaded_img)

    if decoded_text == CANONICAL_URL:
        print(f"SUCCESS: Decoded text exactly matches canonical URL: {decoded_text}")
    else:
        # If OpenCV detector fails on the framed canvas, try on raw qr_img
        qr_cv = cv2.imread("dist/raw_qr.png") if os.path.exists("dist/raw_qr.png") else None
        print(f"Decoded from framed canvas: '{decoded_text}' (expected: '{CANONICAL_URL}')")
        assert decoded_text == CANONICAL_URL, f"QR decode verification failed: {decoded_text}"

if __name__ == "__main__":
    generate_download_qr()
