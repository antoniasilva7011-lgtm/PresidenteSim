import math

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Mesh, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget

from v05_app import (
    APP_NAME as V05_NAME,
    BG,
    CYAN,
    GLASS,
    GLASS_DARK,
    GREEN,
    MUTED,
    RED,
    TEXT,
    GameApp as V05GameApp,
    GlassPanel,
    MediaMapRoot,
    SmallButton,
    label,
)

APP_NAME = "Presidente Simulator V0.6"


COUNTRY_POINTS = [
    # Americas
    ("Canada", -106, 57, 1.10), ("Estados Unidos", -100, 38, 1.00), ("Mexico", -102, 23, 1.15),
    ("Cuba", -79, 21.5, 1.70), ("Colombia", -74, 4, 1.35), ("Venezuela", -66, 7, 1.45),
    ("Brasil", -52, -14, 1.00), ("Peru", -75, -10, 1.35), ("Bolivia", -64, -17, 1.55),
    ("Chile", -71, -31, 1.35), ("Argentina", -64, -34, 1.10), ("Uruguai", -56, -33, 1.85),
    # Europe
    ("Reino Unido", -3, 55, 1.30), ("Franca", 2, 46, 1.15), ("Espanha", -4, 40, 1.35),
    ("Portugal", -8, 39, 1.80), ("Alemanha", 10, 51, 1.20), ("Italia", 12, 42, 1.35),
    ("Polonia", 19, 52, 1.55), ("Ucrania", 31, 49, 1.40), ("Noruega", 9, 61, 1.65),
    ("Suecia", 16, 62, 1.70), ("Grecia", 22, 39, 1.85),
    # Africa / Middle East
    ("Marrocos", -6, 32, 1.65), ("Argelia", 2, 28, 1.45), ("Egito", 30, 27, 1.30),
    ("Nigeria", 8, 9, 1.35), ("Etiopia", 40, 9, 1.60), ("Quenia", 37, 0, 1.60),
    ("Africa do Sul", 24, -30, 1.15), ("Arabia Saudita", 45, 24, 1.40), ("Israel", 35, 31.5, 2.10),
    ("Ira", 53, 32, 1.45), ("Turquia", 35, 39, 1.40),
    # Asia / Oceania
    ("Russia", 90, 60, 1.00), ("China", 104, 35, 1.00), ("India", 79, 22, 1.00),
    ("Paquistao", 69, 30, 1.55), ("Japao", 138, 37, 1.25), ("Coreia do Sul", 128, 36, 1.80),
    ("Indonesia", 118, -3, 1.40), ("Tailandia", 101, 15, 1.70), ("Vietnam", 108, 16, 1.80),
    ("Filipinas", 122, 12, 1.75), ("Australia", 134, -25, 1.00), ("Nova Zelandia", 173, -41, 1.65),
]

CONTINENT_LABELS = [
    ("AMERICA DO NORTE", -105, 47), ("AMERICA DO SUL", -60, -20), ("EUROPA", 15, 53),
    ("AFRICA", 20, 5), ("ASIA", 90, 43), ("OCEANIA", 135, -28),
]

LAND_POLYGONS = [
    [(-168, 72), (-145, 70), (-130, 58), (-115, 52), (-100, 72), (-80, 58), (-52, 50),
     (-60, 32), (-82, 24), (-96, 15), (-111, 29), (-130, 39), (-155, 55)],
    [(-98, 18), (-88, 20), (-80, 9), (-83, 7), (-91, 14)],
    [(-82, 12), (-69, 11), (-50, 3), (-35, -8), (-39, -22), (-54, -55), (-68, -51),
     (-76, -34), (-81, -10)],
    [(-60, 82), (-20, 82), (-18, 66), (-42, 59), (-58, 68)],
    [(-11, 72), (15, 72), (40, 65), (42, 54), (31, 45), (15, 36), (-5, 36), (-10, 50)],
    [(-17, 37), (10, 38), (35, 32), (51, 12), (43, -35), (20, -35), (7, -25), (-5, -5), (-17, 15)],
    [(34, 31), (58, 27), (53, 13), (42, 12), (35, 20)],
    [(30, 72), (80, 77), (135, 72), (180, 63), (168, 48), (145, 43), (132, 31),
     (118, 19), (108, 5), (88, 7), (70, 23), (52, 39), (35, 48)],
    [(67, 24), (78, 28), (89, 22), (80, 7), (73, 10)],
    [(95, 22), (113, 18), (120, 4), (107, -5), (99, 6)],
    [(130, 46), (143, 45), (146, 31), (135, 32)],
    [(112, -10), (132, -10), (154, -20), (149, -40), (120, -36)],
    [(166, -34), (178, -38), (174, -47), (166, -43)],
]


class CountryName(Button):
    def __init__(self, country, threshold, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.country = country
        self.threshold = threshold
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0.015, 0.035, 0.05, 0.55)
        self.color = TEXT
        self.font_size = dp(7.0)
        self.bold = True
        self.size_hint = (None, None)
        self.size = (dp(92), dp(24))
        self.text = country.upper()
        self.opacity = 0
        self.disabled = True
        if callback:
            self.bind(on_release=lambda *_: callback(country))
        with self.canvas.after:
            Color(CYAN[0], CYAN[1], CYAN[2], 0.32)
            self._line = Line(rounded_rectangle=(0, 0, 10, 10, dp(5)), width=0.55)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(5))


class FlatWorldContent(FloatLayout):
    def __init__(self, game, on_country=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.on_country = on_country
        self.country_widgets = []
        self.continent_widgets = []
        self.bind(pos=self.redraw, size=self._layout_labels)
        Clock.schedule_once(self._build_labels, 0)
        Clock.schedule_once(self.redraw, 0)

    def project(self, lon, lat):
        return (
            self.x + (lon + 180.0) / 360.0 * self.width,
            self.y + (lat + 90.0) / 180.0 * self.height,
        )

    def redraw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.005, 0.018, 0.040, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.02, 0.14, 0.25, 0.35)
            for lon in range(-150, 181, 30):
                x1, y1 = self.project(lon, -85)
                x2, y2 = self.project(lon, 85)
                Line(points=[x1, y1, x2, y2], width=0.55)
            for lat in range(-60, 61, 30):
                x1, y1 = self.project(-180, lat)
                x2, y2 = self.project(180, lat)
                Line(points=[x1, y1, x2, y2], width=0.55)

            Color(0.52, 0.62, 0.68, 0.65)
            x1, y1 = self.project(-180, -90)
            x2, y2 = self.project(180, -70)
            Rectangle(pos=(x1, y1), size=(x2 - x1, y2 - y1))

            for poly in LAND_POLYGONS:
                verts = []
                for lon, lat in poly:
                    px, py = self.project(lon, lat)
                    verts.extend([px, py, 0, 0])
                Color(0.06, 0.34, 0.23, 0.98)
                Mesh(vertices=verts, indices=list(range(len(poly))), mode="triangle_fan")
                Color(0.16, 0.76, 0.76, 0.32)
                points = []
                for lon, lat in poly + [poly[0]]:
                    px, py = self.project(lon, lat)
                    points.extend([px, py])
                Line(points=points, width=0.65)

    def _build_labels(self, *_):
        for text, lon, lat in CONTINENT_LABELS:
            lab = label(text, color=(0.68, 0.78, 0.86, 0.82), font_size=dp(10), bold=True,
                        halign="center", size_hint=(None, None), size=(dp(150), dp(28)))
            lab._geo = (lon, lat)
            self.add_widget(lab)
            self.continent_widgets.append(lab)

        for name, lon, lat, threshold in COUNTRY_POINTS:
            item = CountryName(name, threshold, callback=self.on_country)
            item._geo = (lon, lat)
            self.add_widget(item)
            self.country_widgets.append(item)
        self._layout_labels()
        self.set_zoom(1.0)

    def _layout_labels(self, *_):
        for item in self.continent_widgets + self.country_widgets:
            lon, lat = item._geo
            px, py = self.project(lon, lat)
            item.center = (px, py)
        self.redraw()

    def set_zoom(self, scale):
        for item in self.country_widgets:
            visible = scale >= item.threshold
            item.opacity = 1.0 if visible else 0.0
            item.disabled = not visible
        for item in self.continent_widgets:
            item.opacity = max(0.0, min(1.0, 2.0 - scale))


class ZoomableWorldMap(FloatLayout):
    def __init__(self, game, on_country=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.on_country = on_country
        self.scatter = Scatter(
            do_rotation=False,
            do_translation=True,
            do_scale=True,
            scale_min=1.0,
            scale_max=4.0,
            size_hint=(None, None),
        )
        self.content = FlatWorldContent(game, on_country=on_country, size_hint=(None, None))
        self.scatter.add_widget(self.content)
        self.add_widget(self.scatter)
        self.scatter.bind(scale=self._on_zoom)
        self.bind(size=self._fit, pos=self._fit)
        Clock.schedule_once(self._fit, 0)

        controls = GlassPanel(
            orientation="vertical", spacing=dp(4), padding=dp(4), bg=(0.02, 0.05, 0.08, 0.88),
            size_hint=(None, None), width=dp(46), height=dp(142),
            pos_hint={"right": 0.985, "center_y": 0.52},
        )
        plus = SmallButton(text="+", font_size=dp(16))
        minus = SmallButton(text="-", font_size=dp(16))
        reset = SmallButton(text="R", font_size=dp(8))
        plus.bind(on_release=lambda *_: self.zoom_by(1.30))
        minus.bind(on_release=lambda *_: self.zoom_by(1 / 1.30))
        reset.bind(on_release=lambda *_: self.reset_view())
        controls.add_widget(plus)
        controls.add_widget(minus)
        controls.add_widget(reset)
        self.add_widget(controls)

        hint = GlassPanel(
            orientation="horizontal", padding=(dp(8), dp(2)), bg=(0.02, 0.04, 0.06, 0.72),
            size_hint=(0.38, None), height=dp(28), pos_hint={"center_x": 0.55, "y": 0.018},
        )
        hint.add_widget(label("ARRASTE PARA MOVER  |  PINCA PARA ZOOM  |  NOMES SURGEM AO APROXIMAR",
                              color=MUTED, font_size=dp(5.9), halign="center"))
        self.add_widget(hint)

    def _fit(self, *_):
        if self.width <= 1 or self.height <= 1:
            return
        self.scatter.size = self.size
        self.scatter.pos = self.pos
        self.content.size = self.size
        self.content.pos = self.pos
        if self.scatter.scale < 1.001:
            self.scatter.scale = 1.0

    def _on_zoom(self, *_):
        self.content.set_zoom(self.scatter.scale)

    def zoom_by(self, factor):
        self.scatter.scale = max(1.0, min(4.0, self.scatter.scale * factor))
        self.content.set_zoom(self.scatter.scale)

    def reset_view(self):
        self.scatter.scale = 1.0
        self.scatter.pos = self.pos
        self.content.set_zoom(1.0)


class V06Root(MediaMapRoot):
    def __init__(self, game, **kwargs):
        super().__init__(game, **kwargs)
        old_globe = self.globe
        self.remove_widget(old_globe)
        self.globe = ZoomableWorldMap(game, on_country=self._country_selected, size_hint=(1, 1))
        self.add_widget(self.globe, index=len(self.children))

        badge = GlassPanel(
            orientation="horizontal", padding=(dp(8), dp(2)), bg=(0.02, 0.05, 0.08, 0.80),
            size_hint=(None, None), width=dp(160), height=dp(28), pos_hint={"x": 0.072, "top": 0.90},
        )
        badge.add_widget(label("MAPA ESTRATEGICO 2D  |  V0.6", color=CYAN, font_size=dp(6.5), bold=True))
        self.add_widget(badge)


class GameApp(V05GameApp):
    title = APP_NAME

    def build(self):
        Window.clearcolor = BG
        from v03_app import GameState
        from v05_app import ensure_media_state

        self.state = GameState()
        self.state.load()
        ensure_media_state(self.state.d)
        self.playing = False
        self.overlay_open = False
        self.drawer = None
        self.news_overlay = None
        self._play_accumulator = 0.0
        self.root_view = V06Root(self)
        Clock.schedule_interval(self._tick, 0.25)
        Clock.schedule_interval(lambda _dt: self.root_view.refresh(), 0.8)
        self.root_view.refresh()
        return self.root_view
