import math

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Mesh, Rectangle
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget

from countries_data import WORLD_COUNTRIES
from v04_app import TopBar, IconButton, GlassPanel, SmallButton, label
from v05_app import BG, CYAN, MUTED, MediaDrawer, MediaNewsOverlay, GameApp as V05GameApp, ensure_media_state

APP_NAME = "Presidente Simulator V0.6.2"
WORLD_MAP_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/"
    "World_map_geographical.jpg/1280px-World_map_geographical.jpg"
)

CONTINENT_LABELS = [
    ("AMÉRICA DO NORTE", -105, 51),
    ("AMÉRICA DO SUL", -61, -23),
    ("EUROPA", 16, 55),
    ("ÁFRICA", 20, 6),
    ("ÁSIA", 92, 47),
    ("OCEANIA", 136, -29),
]

# Fallback silhouettes in lon/lat coordinates. The real map image is drawn over them
# when available, but these keep the map usable even without a network image.
FALLBACK_LAND = [
    [(-168, 71), (-145, 60), (-130, 51), (-124, 32), (-110, 23), (-97, 17), (-85, 9), (-77, 20), (-66, 45), (-55, 55), (-80, 70), (-120, 74)],
    [(-81, 12), (-69, 8), (-50, 2), (-35, -8), (-44, -24), (-55, -36), (-67, -55), (-76, -42), (-80, -15)],
    [(-11, 36), (3, 44), (25, 48), (40, 56), (57, 61), (80, 70), (115, 72), (145, 60), (170, 52), (150, 40), (120, 30), (105, 18), (82, 8), (65, 23), (48, 30), (35, 34), (20, 31), (10, 36)],
    [(-17, 35), (5, 36), (25, 31), (42, 14), (51, 5), (44, -20), (32, -35), (17, -35), (4, -28), (-8, -5)],
    [(112, -10), (153, -11), (151, -31), (136, -43), (116, -35), (110, -22)],
    [(166, -34), (179, -37), (178, -47), (166, -46)],
    [(-53, 60), (-42, 76), (-18, 82), (-22, 62)],
]


def _power_for(name):
    seed = sum((i + 1) * ord(ch) for i, ch in enumerate(name))
    return 20 + seed % 76


def ensure_world_countries(data):
    countries = data.setdefault("countries", {})
    for name, _lon, _lat, _threshold in WORLD_COUNTRIES:
        countries.setdefault(name, {"relation": 0, "power": _power_for(name)})
    aliases = {"Rússia": "Russia", "Índia": "India", "França": "Franca", "Irã": "Ira"}
    for canonical, old in aliases.items():
        if old in countries:
            countries[canonical] = countries[old]


class CountryLabel(Label):
    def __init__(self, country, threshold, **kwargs):
        super().__init__(**kwargs)
        self.country = country
        self.threshold = threshold
        self.size_hint = (None, None)
        self.size = (dp(64), dp(14))
        self.font_size = dp(4.7)
        self.bold = True
        self.color = (0.92, 0.96, 1.0, 0.90)
        self.halign = "center"
        self.valign = "middle"
        self.text_size = self.size
        self.opacity = 0


class WorldFallback(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_once(self.redraw, 0)

    def project(self, lon, lat):
        return (
            self.x + (lon + 180.0) / 360.0 * self.width,
            self.y + (lat + 90.0) / 180.0 * self.height,
        )

    def redraw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 2 or h < 2:
            return
        with self.canvas:
            Color(0.015, 0.075, 0.11, 1)
            Rectangle(pos=(x, y), size=(w, h))
            Color(0.055, 0.16, 0.19, 1)
            for poly in FALLBACK_LAND:
                verts = []
                for lon, lat in poly:
                    px, py = self.project(lon, lat)
                    verts.extend([px, py, 0, 0])
                Mesh(vertices=verts, indices=list(range(len(poly))), mode="triangle_fan")
            Color(0.14, 0.58, 0.72, 0.18)
            for poly in FALLBACK_LAND:
                pts = []
                for lon, lat in poly:
                    pts.extend(self.project(lon, lat))
                if len(pts) >= 4:
                    pts.extend(pts[:2])
                    Line(points=pts, width=0.55)


class RealWorldContent(FloatLayout):
    def __init__(self, game, on_country=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.on_country = on_country
        self.country_widgets = []
        self.continent_widgets = []

        self.fallback = WorldFallback(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.add_widget(self.fallback)

        self.map_image = AsyncImage(
            source=WORLD_MAP_URL,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.add_widget(self.map_image)

        self.grid = Widget(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.grid.bind(pos=self._draw_grid, size=self._draw_grid)
        self.add_widget(self.grid)

        Clock.schedule_once(self._build_labels, 0.05)
        self.bind(pos=self._layout_labels, size=self._layout_labels)

    def _draw_grid(self, *_):
        self.grid.canvas.clear()
        x, y, w, h = self.grid.x, self.grid.y, self.grid.width, self.grid.height
        with self.grid.canvas:
            Color(0.0, 0.025, 0.055, 0.12)
            Rectangle(pos=(x, y), size=(w, h))
            Color(CYAN[0], CYAN[1], CYAN[2], 0.075)
            for i in range(1, 12):
                gx = x + w * i / 12.0
                Line(points=[gx, y, gx, y + h], width=0.32)
            for i in range(1, 6):
                gy = y + h * i / 6.0
                Line(points=[x, gy, x + w, gy], width=0.32)

    def project(self, lon, lat):
        return (
            self.x + (lon + 180.0) / 360.0 * self.width,
            self.y + (lat + 90.0) / 180.0 * self.height,
        )

    def _build_labels(self, *_):
        if self.width < 200 or self.height < 100:
            Clock.schedule_once(self._build_labels, 0.08)
            return
        if self.country_widgets:
            return

        for text, lon, lat in CONTINENT_LABELS:
            lab = label(
                text,
                color=(0.80, 0.88, 0.94, 0.42),
                font_size=dp(5.6),
                bold=True,
                halign="center",
                size_hint=(None, None),
                size=(dp(105), dp(18)),
            )
            lab._geo = (lon, lat)
            self.continent_widgets.append(lab)
            self.add_widget(lab)

        for name, lon, lat, threshold in WORLD_COUNTRIES:
            lab = CountryLabel(name, threshold, text=name.upper())
            lab._geo = (lon, lat)
            self.country_widgets.append(lab)
            self.add_widget(lab)

        self._layout_labels()
        self.set_zoom(1.0)

    def _layout_labels(self, *_):
        if self.width < 10 or self.height < 10:
            return
        for item in self.continent_widgets + self.country_widgets:
            lon, lat = item._geo
            item.center = self.project(lon, lat)

    def set_zoom(self, scale):
        for item in self.country_widgets:
            item.opacity = 0.90 if scale >= item.threshold else 0.0
            item.font_size = dp(max(3.6, 4.9 / max(1.0, scale ** 0.22)))
        for item in self.continent_widgets:
            item.opacity = max(0.0, min(0.40, 1.45 - scale * 0.72))

    def select_nearest(self, local_x, local_y, scale):
        best_name = None
        best_dist = dp(38) / max(1.0, scale)
        for name, lon, lat, _threshold in WORLD_COUNTRIES:
            px, py = self.project(lon, lat)
            dist = math.hypot(local_x - px, local_y - py)
            if dist < best_dist:
                best_dist, best_name = dist, name
        if best_name and self.on_country:
            self.on_country(best_name)


class CountryScatter(Scatter):
    def __init__(self, content=None, **kwargs):
        super().__init__(**kwargs)
        self.map_content = content

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.ud["presim_map_origin"] = touch.pos
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        origin = touch.ud.get("presim_map_origin")
        handled = super().on_touch_up(touch)
        if origin and self.map_content:
            moved = math.hypot(touch.x - origin[0], touch.y - origin[1])
            if moved < dp(8):
                lx, ly = self.to_local(touch.x, touch.y)
                self.map_content.select_nearest(lx, ly, self.scale)
        return handled


class InteractiveWorldMap(FloatLayout):
    def __init__(self, game, on_country=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.content = RealWorldContent(
            game,
            on_country=on_country,
            size_hint=(None, None),
            pos=(0, 0),
        )
        self.scatter = CountryScatter(
            content=self.content,
            do_rotation=False,
            do_translation=True,
            do_scale=True,
            translation_touches=1,
            scale_min=1.0,
            scale_max=6.0,
            auto_bring_to_front=False,
            size_hint=(None, None),
        )
        self.scatter.add_widget(self.content)
        self.scatter.bind(scale=self._on_zoom)
        self.add_widget(self.scatter)
        self.bind(pos=self._fit, size=self._fit)
        Clock.schedule_once(self._fit, 0)
        Clock.schedule_once(self._fit, 0.15)

    def _fit(self, *_):
        if self.width < 200 or self.height < 100:
            return

        # Critical V0.6.2 fix: always synchronize map geometry with the real viewport.
        # The old code captured Kivy's initial 100x100 default and never resized again.
        at_base_zoom = self.scatter.scale <= 1.01
        self.scatter.size = self.size
        self.content.size = self.size
        self.content.pos = (0, 0)
        if at_base_zoom:
            self.scatter.pos = self.pos
        self.content._layout_labels()

    def _on_zoom(self, *_):
        self.content.set_zoom(self.scatter.scale)

    def zoom_by(self, factor):
        viewport_center = self.center
        target = max(
            self.scatter.scale_min,
            min(self.scatter.scale_max, self.scatter.scale * factor),
        )
        self.scatter.scale = target
        self.scatter.center = viewport_center
        self.content.set_zoom(target)

    def reset_view(self):
        self.scatter.scale = 1.0
        self.scatter.size = self.size
        self.content.size = self.size
        self.content.pos = (0, 0)
        self.scatter.pos = self.pos
        self.content.set_zoom(1.0)
        self.content._layout_labels()


class SelectedCountryPanel(GlassPanel):
    def __init__(self, root_view, **kwargs):
        super().__init__(
            orientation="horizontal",
            padding=(dp(7), dp(2)),
            spacing=dp(4),
            bg=(0.02, 0.05, 0.08, 0.92),
            **kwargs,
        )
        self.root_view = root_view
        self.name_label = label(
            "BRASIL",
            color=CYAN,
            font_size=dp(5.8),
            bold=True,
            size_hint_x=0.27,
        )
        self.info_label = label(
            "TOQUE EM UM PAÍS",
            color=MUTED,
            font_size=dp(5.0),
            size_hint_x=0.51,
        )
        self.action = SmallButton(
            text="DIPLOMACIA",
            font_size=dp(4.8),
            size_hint_x=0.22,
        )
        self.action.bind(on_release=lambda *_: self.root_view.open_section("dip"))
        self.add_widget(self.name_label)
        self.add_widget(self.info_label)
        self.add_widget(self.action)

    def set_country(self, name):
        country = self.root_view.game.state.d.get("countries", {}).get(
            name,
            {"relation": 0, "power": 50},
        )
        self.name_label.text = name.upper()
        self.info_label.text = (
            f"RELAÇÃO {country.get('relation', 0):+d}  |  "
            f"PODER {country.get('power', 50)}/100"
        )


class V06Root(FloatLayout):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.selected_country = "Brasil"

        self.globe = InteractiveWorldMap(
            game,
            on_country=self._country_selected,
            size_hint=(1, 1),
        )
        self.add_widget(self.globe)

        self.topbar = TopBar(
            game,
            size_hint=(0.83, None),
            height=dp(38),
            pos_hint={"center_x": 0.55, "top": 0.988},
        )
        self.add_widget(self.topbar)

        toolbar = GlassPanel(
            orientation="vertical",
            padding=dp(2),
            spacing=dp(2),
            bg=(0.02, 0.05, 0.075, 0.90),
            size_hint=(None, None),
            width=dp(38),
            height=dp(218),
            pos_hint={"x": 0.010, "center_y": 0.53},
        )
        for icon, hint, section in [
            ("gov", "POL", "gov"),
            ("eco", "ECO", "eco"),
            ("def", "MIL", "def"),
            ("dip", "DIP", "dip"),
            ("news", "MID", "news"),
            ("save", "SAVE", "save"),
        ]:
            b = IconButton(icon=icon, hint=hint, size_hint_y=None, height=dp(32))
            if section == "save":
                b.bind(on_release=lambda *_: self.game.save_game())
            else:
                b.bind(on_release=lambda _btn, s=section: self.open_section(s))
            toolbar.add_widget(b)
        self.add_widget(toolbar)

        zoom = GlassPanel(
            orientation="vertical",
            padding=dp(2),
            spacing=dp(2),
            bg=(0.02, 0.05, 0.075, 0.90),
            size_hint=(None, None),
            width=dp(37),
            height=dp(111),
            pos_hint={"right": 0.987, "center_y": 0.52},
        )
        zoom_items = [
            ("+", dp(11), lambda *_: self.globe.zoom_by(1.35)),
            ("-", dp(11), lambda *_: self.globe.zoom_by(1 / 1.35)),
            ("RESET", dp(4.5), lambda *_: self.globe.reset_view()),
        ]
        for txt, font_size, cb in zoom_items:
            b = SmallButton(
                text=txt,
                font_size=font_size,
                size_hint_y=None,
                height=dp(33),
            )
            b.bind(on_release=cb)
            zoom.add_widget(b)
        self.add_widget(zoom)

        bottom = GlassPanel(
            orientation="horizontal",
            padding=dp(2),
            spacing=dp(2),
            bg=(0.02, 0.045, 0.07, 0.92),
            size_hint=(0.58, None),
            height=dp(32),
            pos_hint={"center_x": 0.50, "y": 0.012},
        )
        for title, section in [
            ("GABINETE", "gov"),
            ("ECONOMIA", "eco"),
            ("POLÍTICA", "gov"),
            ("MILITAR", "def"),
            ("DIPLOMACIA", "dip"),
            ("MÍDIA", "news"),
        ]:
            b = SmallButton(text=title, font_size=dp(4.9))
            b.bind(on_release=lambda _btn, s=section: self.open_section(s))
            bottom.add_widget(b)
        self.add_widget(bottom)

        # Keep auxiliary HUD above the bottom menu instead of overlapping it.
        self.country_panel = SelectedCountryPanel(
            self,
            size_hint=(0.31, None),
            height=dp(27),
            pos_hint={"x": 0.058, "y": 0.068},
        )
        self.add_widget(self.country_panel)

        self.status = GlassPanel(
            orientation="horizontal",
            padding=(dp(6), dp(2)),
            bg=(0.02, 0.04, 0.06, 0.80),
            size_hint=(0.27, None),
            height=dp(25),
            pos_hint={"right": 0.985, "y": 0.070},
        )
        self.status_label = label("", color=MUTED, font_size=dp(5.0))
        self.status.add_widget(self.status_label)
        self.add_widget(self.status)

        self.drawer = MediaDrawer(game, size_hint=(1, 1))
        game.drawer = self.drawer
        self.add_widget(self.drawer)

        self.news_overlay = MediaNewsOverlay(game, size_hint=(1, 1))
        game.news_overlay = self.news_overlay
        self.add_widget(self.news_overlay)

        self.country_panel.set_country("Brasil")
        Clock.schedule_once(lambda *_: self.globe.reset_view(), 0.2)

    def open_section(self, section):
        if self.game.drawer:
            self.game.drawer.open(section)

    def _country_selected(self, name):
        self.selected_country = name
        self.country_panel.set_country(name)
        country = self.game.state.d.get("countries", {}).get(name)
        if country:
            self.status_label.text = (
                f"{name.upper()}  |  REL {country['relation']:+d}  |  "
                f"PODER {country['power']}/100"
            )

    def refresh(self):
        self.topbar.refresh()
        d = self.game.state.d
        if self.selected_country:
            country = d.get("countries", {}).get(self.selected_country)
            if country:
                self.country_panel.set_country(self.selected_country)
        if not self.status_label.text:
            self.status_label.text = (
                f"MERCADO {d['market_sentiment']:.0f}%  |  "
                f"CONGRESSO {d['congress']:.0f}%  |  "
                f"CRISE {d['crisis_risk']:.0f}%"
            )
        if self.drawer and not self.drawer.disabled:
            self.drawer.rebuild()


class GameApp(V05GameApp):
    title = APP_NAME

    def build(self):
        Window.clearcolor = BG
        from v03_app import GameState

        self.state = GameState()
        self.state.load()
        ensure_media_state(self.state.d)
        ensure_world_countries(self.state.d)
        self.state.save()

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
