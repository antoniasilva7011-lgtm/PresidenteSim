import v02_app

from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.button import Button


class CommandButton(Button):
    """Botao do jogo com nome proprio para nao colidir com ActionButton do Kivy."""

    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.045, 0.115, 0.165, 1))
        kwargs.setdefault("color", v02_app.TEXT)
        kwargs.setdefault("font_size", dp(10))
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)
        with self.canvas.after:
            Color(v02_app.CYAN[0], v02_app.CYAN[1], v02_app.CYAN[2], 0.70)
            self.outline = Line(
                rounded_rectangle=(0, 0, 100, 100, dp(8)),
                width=0.8,
            )
        self.bind(pos=self._sync_outline, size=self._sync_outline)

    def _sync_outline(self, *_):
        self.outline.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(8),
        )


# v02_app usava o nome ActionButton, que colide com um widget interno do Kivy.
# Substituimos o global do modulo por esta classe antes de criar qualquer tela.
v02_app.ActionButton = CommandButton
GameApp = v02_app.GameApp


if __name__ == "__main__":
    GameApp().run()
