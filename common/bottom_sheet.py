from kivy.animation import Animation
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


def open_bottom_sheet(screen, build_content, height_fraction=0.8):
    """Slide a white, rounded-top panel up from the bottom of `screen`.

    `build_content(panel, close)` populates the panel; call `close()` to
    dismiss it (also triggered by tapping the dimmed backdrop).
    """
    backdrop = Button(background_normal="", background_color=(0, 0, 0, 0.55))

    panel_height = Window.height * height_fraction
    panel = BoxLayout(
        orientation="vertical",
        size_hint=(1, None),
        height=panel_height,
        pos=(0, -panel_height),
        padding=[24, 20, 24, 24],
        spacing=14,
    )
    with panel.canvas.before:
        Color(1, 1, 1, 1)
        bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[24, 24, 0, 0])

    def sync_bg(*_):
        bg.pos = panel.pos
        bg.size = panel.size

    panel.bind(pos=sync_bg, size=sync_bg)

    def close(*_):
        anim = Animation(pos=(0, -panel_height), duration=0.22, t="in_cubic")
        anim.bind(on_complete=lambda *_: (
            screen.remove_widget(panel),
            screen.remove_widget(backdrop),
        ))
        anim.start(panel)

    backdrop.bind(on_release=close)
    build_content(panel, close)

    screen.add_widget(backdrop)
    screen.add_widget(panel)
    Animation(pos=(0, 0), duration=0.25, t="out_cubic").start(panel)
    return close
