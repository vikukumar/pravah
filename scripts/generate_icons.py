import os
import shutil
from pathlib import Path
from PIL import Image

def generate_device_icons():
    root_dir = Path(__file__).resolve().parent.parent
    icon_src = root_dir / "assets" / "icons" / "icon.png"
    images_src = root_dir / "assets" / "images"
    
    web_public = root_dir / "apps" / "web" / "public"
    web_images = web_public / "images"
    web_icons = web_public / "icons"
    
    web_public.mkdir(parents=True, exist_ok=True)
    web_images.mkdir(parents=True, exist_ok=True)
    web_icons.mkdir(parents=True, exist_ok=True)
    
    if not icon_src.exists():
        print(f"Error: Icon source not found at {icon_src}")
        return
        
    print(f"Loading master icon from {icon_src}...")
    img = Image.open(icon_src).convert("RGBA")
    
    sizes = [
        (16, "favicon-16x16.png"),
        (32, "favicon-32x32.png"),
        (48, "favicon-48x48.png"),
        (64, "favicon-64x64.png"),
        (96, "favicon-96x96.png"),
        (128, "favicon-128x128.png"),
        (144, "favicon-144x144.png"),
        (180, "apple-touch-icon.png"),
        (192, "android-chrome-192x192.png"),
        (256, "favicon-256x256.png"),
        (384, "android-chrome-384x384.png"),
        (512, "android-chrome-512x512.png"),
    ]
    
    for size, filename in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        out_path = web_public / filename
        resized.save(out_path, format="PNG")
        print(f"Generated {out_path} ({size}x{size})")
        
        # Also copy into web_icons
        resized.save(web_icons / filename, format="PNG")
        
    # Generate multi-size favicon.ico (16, 32, 48)
    ico_path = web_public / "favicon.ico"
    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"Generated {ico_path}")
    
    # Copy master logos to public images directory
    for logo_file in ["pravah_horizontal_logo.png", "pravah_vertical_logo.png"]:
        src = images_src / logo_file
        if src.exists():
            dest = web_images / logo_file
            shutil.copy2(src, dest)
            print(f"Copied {logo_file} to {dest}")
            
    shutil.copy2(icon_src, web_images / "icon.png")
    
    # Generate site.webmanifest
    manifest = """{
  "name": "PRAVAH - AI Social Media Management & Automation",
  "short_name": "PRAVAH",
  "icons": [
    {
      "src": "/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "theme_color": "#4f46e5",
  "background_color": "#090d16",
  "display": "standalone"
}
"""
    with open(web_public / "site.webmanifest", "w", encoding="utf-8") as f:
        f.write(manifest)
    print("Generated site.webmanifest")
    
    # Generate robots.txt
    robots = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
Disallow: /dashboard/

Sitemap: https://pravah.app/sitemap.xml
"""
    with open(web_public / "robots.txt", "w", encoding="utf-8") as f:
        f.write(robots)
    print("Generated robots.txt")

if __name__ == "__main__":
    generate_device_icons()
