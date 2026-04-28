from __future__ import annotations

from screeninfo import get_monitors


def get_screen_metrics():
    for m in get_monitors():
        if m.width_mm is None or m.height_mm is None:
            continue
        # 物理尺寸单位是毫米，分辨率单位是像素
        width_inches = m.width_mm / 25.4
        height_inches = m.height_mm / 25.4
        dpi = m.width / width_inches

        print(f"屏幕: {m.name}")
        print(f"分辨率: {m.width}x{m.height}")
        print(f"物理尺寸: {m.width_mm}mm x {m.height_mm}mm")
        print(f"对角线尺寸: {(width_inches**2 + height_inches**2) ** 0.5:.2f} 英寸")
        print(f"DPI: {dpi:.2f}\n")
        print(f"系统缩放比例: {(dpi / 96):.2f}")


if __name__ == "__main__":
    get_screen_metrics()
