# import dearpygui.dearpygui as dpg

# dpg.create_context()
# dpg.create_viewport(title="Custom Title", width=600, height=200)
# dpg.setup_dearpygui()
# dpg.set_global_font_scale(3.0)
# with dpg.window(
#     label="Example Window",
#     no_title_bar=True,
#     no_move=True,
#     no_collapse=True,
#     width=600,
#     height=200,
# ):  # type: ignore
#     dpg.add_text("Hello, world")

# dpg.show_viewport()

# # below replaces, start_dearpygui()
# while dpg.is_dearpygui_running():
#     # insert here any code you would like to run in the render loop
#     # you can manually stop by using stop_dearpygui()
#     print("this will run every frame")
#     dpg.render_dearpygui_frame()

# dpg.destroy_context()


from screeninfo import get_monitors


def get_screen_metrics():
    for m in get_monitors():
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
