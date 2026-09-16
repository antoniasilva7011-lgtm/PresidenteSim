from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.image import AsyncImage
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget

from v05_app import (
    BG,
    CYAN,
    GLASS,
    GREEN,
    MUTED,
    TEXT,
    GameApp as V05GameApp,
    GlassPanel,
    MediaMapRoot,
    SmallButton,
    label,
)

APP_NAME = "Presidente Simulator V0.6"

# Public-domain Natural Earth physical world map.
# Source: https://commons.wikimedia.org/wiki/File:World_map_geographical.jpg
WORLD_MAP_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/"
    "World_map_geographical.jpg/1280px-World_map_geographical.jpg"
)

COUNTRY_POINTS = [
    ("Canada", -106, 57, 1.10), ("Estados Unidos", -100, 38, 1.00), ("Mexico", -102, 23, 1.15),
    ("Cuba", -79, 21.5, 1.85), ("Colombia", -74, 4, 1.30), ("Venezuela", -66, 7, 1.45),
    ("Brasil", -52, -14, 1.00), ("Peru", -75, -10, 1.35), ("Bolivia", -64, -17, 1.55),
    ("Chile", -71, -31, 1.40), ("Argentina", -64, -34, 1.10), ("Uruguai", -56, -33, 1.90),
    ("Reino Unido", -3, 55, 1.30), ("Franca", 2, 46, 1.25), ("Espanha", -4, 40, 1.40),
    ("Portugal", -8, 39, 1.80), ("Alemanha", 10, 51, 1.20), ("Italia", 12, 42, 1.45),
    ("Polonia", 19, 52, 1.55), ("Ucrania", 31, 49, 1.40), ("Noruega", 9, 61, 1.70),
    ("Suecia", 16, 62, 1.75), ("Grecia", 22, 39, 1.85),
    ("Marrocos", -6, 32, 1.65), ("Argelia", 2, 28, 1.45), ("Egito", 30, 27, 1.30),
    ("Nigeria", 8, 9, 1.35), ("Etiopia", 40, 9, 1.60), ("Quenia", 37, 0, 1.65),
    ("Africa do Sul", 24, -30, 1.20), ("Arabia Saudita", 45, 24, 1.45),
    ("Israel", 35, 31.5, 2.10), ("Ira", 53, 32, 1.45), ("Turquia", 35, 39, 1.40),
    ("Russia", 90, 60, 1.00), ("China", 104, 35, 1.00), ("India", 79, 22, 1.00),
    ("Paquistao", 69, 30, 1.55), ("Japao", 138, 37, 1.25), ("Coreia do Sul", 128, 36, 1.80),
    ("Indonesia", 118, -3, 1.45), ("Tailandia", 101, 15, 1.70), ("Vietnam", 108, 16, 1.80),
    ("Filipinas", 122, 12, 1.75), ("Australia", 134, -25, 1.00), ("Nova Zelandia", 173, -41, 1.65),
]

CONTINENT_LABELS = [
    ("AMERICA DO NORTE", -107, 48),
    ("AMERICA DO SUL", -61, -22),
    ("EUROPA", 16, 54),
    ("AFRICA", 20, 5),
    ("ASIA", 92, 44),
    ("OCEANIA", 137, -29),
]


class CountryMarker(Button):
    def __init__(self, country, threshold, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.country = country
        self.threshold = threshold
        self.size_hint = (None, None)
        self.size = (dp(96), dp(24))
        self.text = country.upper()
        self.font_size = dp(6.6)
        self.bold = True
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0.015, 0.04, 0.065, 0.68)
        self.color = TEXT
        self.opacity = 0
        self.disabled = True
        if callback:
            self.bind(on_release=lambda *_: callback(country))
        with self.canvas.after:
            Color(CYAN[0], CYAN[1], CYAN[2], 0.48)
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(6)),
                width=0.75,
            )
        self.bind(pos=self._sync, size=self._sync, state=self._state)

    def _sync(self, *_):
        self._border.rounded_rectangle = (
            self.x, self.y, self.width, self.height, dp(6)
        )

    def _state(self, *_):
        if self.state == "down":
            self.background_color = (0.03, 0.26, 0.34, 0.92)
        else:
            self.background_color = (0.015, 0.04, 0.065, 0.68)


class RealWorldContent(FloatLayout):
    def __init__(self, game, on_country=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.on_country = on_country
        self.country_widgets = []
        self.continent_widgets = []

        # Real geographic base map. The old V0.6 fake continent polygons are gone.
        self.map_image = AsyncImage(
            source=WORLD_MAP_URL,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.add_widget(self.map_image)

        # Dark strategy-game treatment over the physical map.
        self.overlay = Widget(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        with self.overlay.canvas:
            Color(0.0, 0.055, 0.105, 0.32)
            self._tint = Rectangle(pos=self.overlay.pos, size=self.overlay.size)
            Color(CYAN[0], CYAN[1], CYAN[2], 0.11)
        self.overlay.bind(pos=self._sync_overlay, size=self._sync_overlay)
        self.add_widget(self.overlay)

        self.bind(size=self._layout_labels, pos=self._layout_labels)
        Clock.schedule_once(self._build_labels, 0)

    def _sync_overlay(self, *_):
        self._draw_grid()

    def _draw_grid(self):
        # Rebuild overlay canvas so the map has a geopolitical HUD grid.
        self.overlay.canvas.clear()
        with self.overlay.canvas:
            Color(0.0, 0.03, 0.07, 0.28)
            self._tint = Rectangle(pos=self.overlay.pos, size=self.overlay.size)
            Color(CYAN[0], CYAN[1], CYAN[2], 0.10)
            x, y, w, h = self.overlay.x, self.overlay.y, self.overlay.width, self.overlay.height
            for i in range(1, 12):
                gx = x + w * i / 12.0
                Line(points=[gx, y, gx, y + h], width=0.45)
            for i in range(1, 6):
                gy = y + h * i / 6.0
                Line(points=[x, gy, x + w, gy], width=0.45)

    def project(self, lon, lat):
        return (
            self.x + (lon + 180.0) / 360.0 * self.width,
            self.y + (lat + 90.0) / 180.0 * self.height,
        )

    def _build_labels(self, *_):
        for text, lon, lat in CONTINENT_LABELS:
            lab = label(
                text,
                color=(0.79, 0.88, 0.94, 0.72),
                font_size=dp(8.5),
                bold=True,
                halign="center",
                size_hint=(None, None),
                size=(dp(150), dp(26)),
            )
            lab._geo = (lon, lat)
            self.add_widget(lab)
            self.continent_widgets.append(lab)

        for name, lon, lat, threshold in COUNTRY_POINTS:
            marker = CountryMarker(name, threshold, callback=self.on_country)
            marker._geo = (lon, lat)
            self.add_widget(marker)
            self.country_widgets.append(marker)

        self._layout_labels()
        self.set_zoom(1.0)

    def _layout_labels(self, *_):
        for item in self.continent_widgets + self.country_widgets:
            lon, lat = item._geo
            item.center = self.project(lon, lat)

    def set_zoom(self, scale):
        for item in self.country_widgets:
            visible = scale >= item.threshold
            item.opacity = 1.0 if visible else 0.0
            item.disabled = not visible

        for item in self.continent_widgets:
            item.opacity = max(0.0, min(0.85, 1.9 - scale))


class InteractiveWorldMap(FloatLayout):
    def __init__(self, game, on_country=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.on_country = on_country
        self._laid_out = False

        self.scatter = Scatter(
            do_rotation=False,
            do_translation=True,
            do_scale=True,
            scale_min=1.0,
            scale_max=5.0,
            auto_bring_to_front=False,
            size_hint=(None, None),
        )
        self.content = RealWorldContent(
            game, on_country=on_country, size_hint=(None, None), pos=(0, 0)
        )
        self.scatter.add_widget(self.content)
        self.add_widget(self.scatter)
        self.scatter.bind(scale=self._on_zoom)
        self.bind(size=self._fit, pos=self._fit)
        Clock.schedule_once(self._fit, 0)

        # Touch-friendly map controls.
        controls = GlassPanel(
            orientation="vertical",
            padding=dp(4),
            spacing=dp(5),
            bg=(0.02, 0.055, 0.09, 0.92),
            size_hint=(None, None),
            width=dp(54),
            height=dp(174),
            pos_hint={"right": 0.985, "center_y": 0.52},
        )
        plus = SmallButton(text="+", font_size=dp(18), size_hint_y=None, height=dp(50))
        minus = SmallButton(text="-", font_size=dp(18), size_hint_y=None, height=dp(50))
        reset = SmallButton(text="CENTRAR", font_size=dp(5.8), size_hint_y=None, height=dp(50))
        plus.bind(on_release=lambda *_: self.zoom_by(1.35))
        minus.bind(on_release=lambda *_: self.zoom_by(1.0 / 1.35))
        reset.bind(on_release=lambda *_: self.reset_view())
        controls.add_widget(plus)
        controls.add_widget(minus)
        controls.add_widget(reset)
        self.add_widget(controls)

        hint = GlassPanel(
            orientation="horizontal",
            padding=(dp(10), dp(3)),
            bg=(0.02, 0.045, 0.07, 0.88),
            size_hint=(0.48, None),
            height=dp(31),
            pos_hint={"center_x": 0.55, "y": 0.018},
        )
        hint.add_widget(
            label(
                "ARRASTE PARA MOVER   |   PINCA COM 2 DEDOS PARA ZOOM",
                color=MUTED,
                font_size=dp(6.2),
                halign="center",
                bold=True,
            )
        )
        self.add_widget(hint)

    def _fit(self, *_):
        if self.width <= 2 or self.height <= 2:
            return
        # Only recenter automatically before the player starts navigating.
        if not self._laid_out:
            self.scatter.size = self.size
            self.content.size = self.size
            self.scatter.pos = self.pos
            self._laid_out = True

    def _on_zoom(self, *_):
        self.content.set_zoom(self.scatter.scale)

    def zoom_by(self, factor):
        target = max(1.0, min(5.0, self.scatter.scale * factor))
        self.scatter.scale = target
        self.content.set_zoom(target)

    def reset_view(self):
        self.scatter.scale = 1.0
        self.scatter.size = self.size
        self.content.size = self.size
        self.scatter.pos = self.pos
        self.content.set_zoom(1.0)


class V06Root(MediaMapRoot):
    def __init__(self, game, **kwargs):
        super().__init__(game, **kwargs)

        old_globe = self.globe
        self.remove_widget(old_globe)
        self.globe = InteractiveWorldMap(
            game,
            on_country=self._country_selected,
            size_hint=(1, 1),
        )
        # Put the map behind top bar, toolbar, drawers and overlays.
        self.add_widget(self.globe, index=len(self.children))

        badge = GlassPanel(
            orientation="horizontal",
            padding=(dp(9), dp(2)),
            bg=(0.02, 0.055, 0.09, 0.90),
            size_hint=(None, None),
            width=dp(176),
            height=dp(30),
            pos_hint={"x": 0.073, "top": 0.90},
        )
        badge.add_widget(
            label(
                "MAPA ESTRATEGICO 2D  |  V0.6",
                color=CYAN,
                font_size=dp(6.5),
                bold=True,
            )
        )
        self.add_widget(badge)

        # Functional bottom navigation inspired by grand-strategy interfaces.
        nav = GlassPanel(
            orientation="horizontal",
            spacing=dp(4),
            padding=dp(4),
            bg=(0.02, 0.045, 0.075, 0.94),
            size_hint=(0.60, None),
            height=dp(43),
            pos_hint={"center_x": 0.50, "y": 0.012},
        )
        for title, section in (
            ("ECONOMIA", "eco"),
            ("POLITICA", "gov"),
            ("DIPLOMACIA", "dip"),
            ("FORCAS ARMADAS", "def"),
            ("GABINETE", "gov"),
        ):
            btn = SmallButton(text=title, font_size=dp(6.2))
            btn.bind(on_release=lambda _btn, sec=section: self._open_section(sec))
            nav.add_widget(btn)
        self.add_widget(nav)

        # Move the live geopolitical status to the lower-right to avoid collisions.
        self.status.size_hint = (0.29, None)
        self.status.height = dp(34)
        self.status.pos_hint = {"right": 0.985, "y": 0.012}

    def _open_section(self, section):
        if self.game.drawer:
            self.game.drawer.open(section)


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
