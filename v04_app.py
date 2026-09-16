import math
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from v03_app import GameState, clamp, fmt_money, DEFAULT_RELATED_NEWS

APP_NAME = "Presidente Simulator V0.4"
BG = (0.02, 0.035, 0.055, 1)
GLASS = (0.055, 0.085, 0.12, 0.86)
GLASS_DARK = (0.025, 0.045, 0.07, 0.90)
GLASS_LIGHT = (0.08, 0.12, 0.17, 0.86)
TEXT = (0.94, 0.97, 1.0, 1)
MUTED = (0.60, 0.70, 0.80, 1)
CYAN = (0.12, 0.72, 0.95, 1)
GREEN = (0.20, 0.82, 0.48, 1)
AMBER = (1.0, 0.66, 0.20, 1)
RED = (0.95, 0.22, 0.28, 1)


def label(text="", **kwargs):
    kwargs.setdefault("color", TEXT)
    kwargs.setdefault("font_size", dp(9))
    kwargs.setdefault("halign", "left")
    kwargs.setdefault("valign", "middle")
    out = Label(text=text, **kwargs)
    out.bind(size=lambda inst, _value: setattr(inst, "text_size", (inst.width, inst.height)))
    return out


class GlassPanel(BoxLayout):
    def __init__(self, bg=GLASS, radius=12, border=True, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
            if border:
                Color(CYAN[0], CYAN[1], CYAN[2], 0.18)
                self._border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(radius)), width=0.7)
            else:
                self._border = None
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        if self._border is not None:
            self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(12))


class SmallButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.07, 0.13, 0.18, 0.94))
        kwargs.setdefault("color", TEXT)
        kwargs.setdefault("font_size", dp(7.5))
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)
        with self.canvas.after:
            Color(CYAN[0], CYAN[1], CYAN[2], 0.42)
            self._line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(7)), width=0.75)
        self.bind(pos=self._sync_line, size=self._sync_line)

    def _sync_line(self, *_):
        self._line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(7))


class IconButton(Button):
    def __init__(self, icon="gov", hint="", **kwargs):
        kwargs.setdefault("text", "")
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.04, 0.075, 0.105, 0.90))
        super().__init__(**kwargs)
        self.icon = icon
        self.hint = hint
        self.bind(pos=self._redraw_icon, size=self._redraw_icon, state=self._redraw_icon)
        Clock.schedule_once(self._redraw_icon, 0)

    def _redraw_icon(self, *_):
        self.canvas.after.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        cx, cy = x + w * 0.5, y + h * 0.58
        s = min(w, h) * 0.24
        accent = CYAN if self.state == "normal" else GREEN
        with self.canvas.after:
            Color(*accent)
            if self.icon == "gov":
                Line(points=[cx - s, cy + s * 0.45, cx, cy + s, cx + s, cy + s * 0.45], width=1.25)
                Line(rectangle=(cx - s * 0.86, cy - s * 0.78, s * 1.72, s * 1.15), width=1.05)
                for off in (-0.52, 0, 0.52):
                    Line(points=[cx + off * s, cy - s * 0.70, cx + off * s, cy + s * 0.24], width=1.0)
            elif self.icon == "eco":
                Line(points=[cx - s, cy - s * 0.65, cx - s * 0.4, cy - s * 0.05, cx + s * 0.1, cy - s * 0.25, cx + s, cy + s * 0.75], width=1.5)
            elif self.icon == "def":
                pts = [cx, cy + s, cx + s * 0.78, cy + s * 0.48, cx + s * 0.62, cy - s * 0.42, cx, cy - s, cx - s * 0.62, cy - s * 0.42, cx - s * 0.78, cy + s * 0.48, cx, cy + s]
                Line(points=pts, width=1.3)
            elif self.icon == "dip":
                Line(circle=(cx, cy, s), width=1.2)
                Line(ellipse=(cx - s, cy - s * 0.35, s * 2, s * 0.70), width=0.9)
                Line(ellipse=(cx - s * 0.42, cy - s, s * 0.84, s * 2), width=0.9)
            elif self.icon == "news":
                Line(rectangle=(cx - s, cy - s * 0.76, s * 2, s * 1.48), width=1.15)
                Line(points=[cx - s * 0.72, cy + s * 0.35, cx + s * 0.62, cy + s * 0.35], width=1.0)
                Line(points=[cx - s * 0.72, cy, cx + s * 0.62, cy], width=1.0)
                Line(points=[cx - s * 0.72, cy - s * 0.35, cx + s * 0.15, cy - s * 0.35], width=1.0)
            elif self.icon == "save":
                Line(rectangle=(cx - s * 0.8, cy - s * 0.8, s * 1.6, s * 1.6), width=1.1)
                Line(rectangle=(cx - s * 0.45, cy + s * 0.12, s * 0.9, s * 0.46), width=1.0)
                Line(rectangle=(cx - s * 0.36, cy - s * 0.55, s * 0.72, s * 0.42), width=1.0)
            elif self.icon == "play":
                Mesh(vertices=[cx - s * 0.55, cy - s * 0.8, 0, 0, cx - s * 0.55, cy + s * 0.8, 0, 0, cx + s * 0.8, cy, 0, 0], indices=[0, 1, 2], mode="triangles")
            elif self.icon == "pause":
                Rectangle(pos=(cx - s * 0.62, cy - s * 0.78), size=(s * 0.38, s * 1.56))
                Rectangle(pos=(cx + s * 0.22, cy - s * 0.78), size=(s * 0.38, s * 1.56))
            else:
                Line(circle=(cx, cy, s), width=1.2)
        if self.hint:
            self.text = self.hint
            self.color = MUTED
            self.font_size = dp(5.6)
            self.valign = "bottom"
            self.halign = "center"
            self.text_size = (w, h * 0.34)
        else:
            self.text = ""


class GlobeWidget(Widget):
    MARKERS = [("Brasil", -52, -14), ("Estados Unidos", -98, 39), ("Argentina", -64, -34), ("Franca", 2, 46), ("Russia", 80, 58), ("India", 79, 22), ("China", 104, 35), ("Japao", 138, 37)]

    def __init__(self, game, on_country=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.on_country = on_country
        self.rotation = 25.0
        self._drag_x = None
        self._marker_cache = []
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_once(self.redraw, 0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._drag_x = touch.x
            touch.ud["globe_dragged"] = False
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._drag_x is not None and self.collide_point(*touch.pos):
            dx = touch.x - self._drag_x
            if abs(dx) > dp(2):
                touch.ud["globe_dragged"] = True
            self.rotation = (self.rotation + dx * 0.22) % 360
            self._drag_x = touch.x
            self.redraw()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._drag_x is not None:
            dragged = touch.ud.get("globe_dragged", False)
            self._drag_x = None
            if not dragged:
                nearest, best = None, dp(30)
                for name, mx, my in self._marker_cache:
                    dist = math.hypot(touch.x - mx, touch.y - my)
                    if dist < best:
                        best, nearest = dist, name
                if nearest and self.on_country:
                    self.on_country(nearest)
            return True
        return super().on_touch_up(touch)

    def redraw(self, *_):
        self.canvas.clear()
        self._marker_cache = []
        x, y, w, h = self.x, self.y, self.width, self.height
        cx, cy = x + w * 0.53, y + h * 0.47
        r = min(w * 0.40, h * 0.43)
        with self.canvas:
            Color(0.004, 0.010, 0.018, 1)
            Rectangle(pos=(x, y), size=(w, h))
            Color(0.07, 0.18, 0.25, 0.20)
            step = max(dp(34), w / 24)
            gx = x
            while gx < x + w:
                Line(points=[gx, y, gx, y + h], width=0.45)
                gx += step
            gy = y
            while gy < y + h:
                Line(points=[x, gy, x + w, gy], width=0.45)
                gy += step
            Color(0.0, 0.02, 0.04, 0.80)
            Ellipse(pos=(cx - r * 1.04, cy - r * 1.04), size=(r * 2.08, r * 2.08))
            Color(0.018, 0.12, 0.19, 1)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
            Color(0.08, 0.38, 0.52, 0.32)
            Ellipse(pos=(cx - r * 0.88, cy - r * 0.94), size=(r * 1.48, r * 1.62))
            Color(CYAN[0], CYAN[1], CYAN[2], 0.24)
            phase = math.radians(self.rotation)
            for i in range(-3, 4):
                squish = abs(math.cos(phase + i * 0.45))
                ww = r * 2 * max(0.10, squish)
                Line(ellipse=(cx - ww / 2, cy - r, ww, r * 2), width=0.55)
            for frac in (-0.66, -0.33, 0, 0.33, 0.66):
                yy = cy + r * frac
                rr = math.sqrt(max(0.0, 1 - frac * frac))
                Line(ellipse=(cx - r * rr, yy - r * 0.06, r * rr * 2, r * 0.12), width=0.55)
            Color(0.08, 0.32, 0.24, 0.95)
            for poly in [[(-0.78, 0.42), (-0.52, 0.70), (-0.18, 0.52), (-0.30, 0.18), (-0.58, -0.08), (-0.82, 0.10)], [(-0.28, -0.12), (-0.05, -0.02), (0.05, -0.36), (-0.10, -0.72), (-0.34, -0.52)], [(0.02, 0.58), (0.38, 0.76), (0.80, 0.55), (0.72, 0.20), (0.40, 0.02), (0.04, 0.18)], [(0.42, -0.08), (0.70, 0.02), (0.86, -0.22), (0.58, -0.42)]]:
                verts = []
                for px, py in poly:
                    verts.extend([cx + px * r, cy + py * r, 0, 0])
                Mesh(vertices=verts, indices=list(range(len(poly))), mode="triangle_fan")
            countries = self.game.state.d.get("countries", {})
            for name, lon, lat in self.MARKERS:
                theta = math.radians(lon + self.rotation)
                z = math.cos(theta)
                if z < -0.18:
                    continue
                mx = cx + r * 0.88 * math.sin(theta)
                my = cy + r * 0.78 * math.sin(math.radians(lat))
                relation = countries.get(name, {}).get("relation", 0)
                Color(*(GREEN if relation >= 20 else AMBER if relation >= -10 else RED))
                radius = dp(4.2 if name == "Brasil" else 3.2) * (0.65 + max(0.2, z) * 0.5)
                Ellipse(pos=(mx - radius, my - radius), size=(radius * 2, radius * 2))
                self._marker_cache.append((name, mx, my))


class TopBar(GlassPanel):
    def __init__(self, game, **kwargs):
        super().__init__(orientation="horizontal", padding=(dp(10), dp(4)), spacing=dp(9), bg=(0.03, 0.055, 0.08, 0.84), **kwargs)
        self.game = game
        self.stats = []
        for title in ("APROVACAO", "PIB", "INFLACAO", "DATA"):
            box = BoxLayout(orientation="vertical", size_hint_x=0.15 if title != "DATA" else 0.18)
            box.add_widget(label(title, color=MUTED, font_size=dp(5.8), bold=True))
            value = label("", color=TEXT, font_size=dp(9), bold=True)
            box.add_widget(value)
            self.add_widget(box)
            self.stats.append(value)
        self.add_widget(Widget())
        self.play_btn = IconButton(icon="play", size_hint_x=None, width=dp(40))
        self.play_btn.bind(on_release=lambda *_: self.game.toggle_play())
        self.add_widget(self.play_btn)
        for text, days in (("1D", 1), ("7D", 7), ("30D", 30)):
            b = SmallButton(text=text, size_hint_x=None, width=dp(46))
            b.bind(on_release=lambda _btn, amount=days: self.game.advance(amount))
            self.add_widget(b)

    def refresh(self):
        d = self.game.state.d
        self.stats[0].text = f"{d['approval']:.0f}%"
        self.stats[1].text = fmt_money(d["gdp"])
        self.stats[2].text = f"{d['inflation']:.1f}%"
        self.stats[3].text = d["day"]
        self.play_btn.icon = "pause" if self.game.playing else "play"
        self.play_btn._redraw_icon()


class Drawer(FloatLayout):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.section = None
        self.panel = GlassPanel(orientation="vertical", padding=dp(10), spacing=dp(6), bg=(0.035, 0.060, 0.085, 0.94), size_hint=(0.36, 0.80), pos_hint={"x": 0.055, "y": 0.08})
        self.add_widget(self.panel)
        self.opacity = 0
        self.disabled = True

    def close(self):
        self.opacity = 0
        self.disabled = True
        self.section = None

    def open(self, section):
        if self.section == section and not self.disabled:
            self.close()
            return
        self.section = section
        self.disabled = False
        self.opacity = 1
        self.rebuild()

    def _header(self, text):
        row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(5))
        row.add_widget(label(text, color=CYAN, font_size=dp(12), bold=True))
        close = SmallButton(text="X", size_hint_x=None, width=dp(34))
        close.bind(on_release=lambda *_: self.close())
        row.add_widget(close)
        self.panel.add_widget(row)

    def _stat_row(self, title_text, value_text, color=TEXT):
        row = GlassPanel(orientation="horizontal", size_hint_y=None, height=dp(34), padding=(dp(7), dp(2)), bg=GLASS_LIGHT)
        row.add_widget(label(title_text, color=MUTED, font_size=dp(7.2)))
        row.add_widget(label(value_text, color=color, font_size=dp(9), bold=True, halign="right"))
        self.panel.add_widget(row)

    def _action(self, text, callback):
        b = SmallButton(text=text, size_hint_y=None, height=dp(34))
        b.bind(on_release=callback)
        self.panel.add_widget(b)

    def rebuild(self):
        self.panel.clear_widgets()
        d = self.game.state.d
        if self.section == "gov":
            self._header("GOVERNO")
            self._stat_row("Aprovacao", f"{d['approval']:.0f}%", GREEN if d["approval"] >= 50 else RED)
            self._stat_row("Congresso", f"{d['congress']:.0f}%")
            self._stat_row("Estabilidade", f"{d['stability']:.0f}%")
            self._stat_row("Risco de impeachment", f"{d['impeachment_risk']:.0f}%", AMBER)
            self._action("COLETIVA DE IMPRENSA", lambda *_: self.game.show_press_overlay())
            self._action("SALVAR PARTIDA", lambda *_: self.game.save_game())
        elif self.section == "eco":
            self._header("ECONOMIA")
            self._stat_row("PIB", fmt_money(d["gdp"]), CYAN)
            self._stat_row("Inflacao", f"{d['inflation']:.1f}%")
            self._stat_row("Desemprego", f"{d['unemployment']:.1f}%")
            self._stat_row("Divida/PIB", f"{d['debt_ratio']:.1f}%")
            grid = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(74))
            for text, key, amount in [("IMPOSTO -1", "tax_rate", -1), ("IMPOSTO +1", "tax_rate", 1), ("JUROS -0,5", "interest_rate", -0.5), ("GASTO SOCIAL +1", "social_spending", 1)]:
                b = SmallButton(text=text)
                b.bind(on_release=lambda _btn, k=key, a=amount, t=text: self.game.economic_action(k, a, t))
                grid.add_widget(b)
            self.panel.add_widget(grid)
        elif self.section == "def":
            self._header("DEFESA")
            self._stat_row("Orcamento militar", f"{d['military_budget']:.1f}% do PIB")
            self._stat_row("Estabilidade", f"{d['stability']:.0f}%")
            self._stat_row("Risco de golpe", f"{d['coup_risk']:.0f}%", AMBER)
            self._action("AUMENTAR ORCAMENTO", lambda *_: self.game.military_action("Aumentar orcamento militar", 0.2))
            self._action("REDUZIR ORCAMENTO", lambda *_: self.game.military_action("Reduzir orcamento militar", -0.2))
            self._action("REALIZAR EXERCICIO", lambda *_: self.game.military_action("Realizar exercicio militar", 1.0))
        elif self.section == "dip":
            self._header("DIPLOMACIA")
            scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
            body = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
            body.bind(minimum_height=body.setter("height"))
            for name, country in d["countries"].items():
                if name == "Brasil":
                    continue
                row = GlassPanel(orientation="horizontal", size_hint_y=None, height=dp(42), padding=dp(4), spacing=dp(4), bg=GLASS_LIGHT)
                row.add_widget(label(f"{name}   {country['relation']:+d}", font_size=dp(7.2)))
                b = SmallButton(text="NEGOCIAR", size_hint_x=0.36)
                b.bind(on_release=lambda _btn, n=name: self.game.negotiate(n))
                row.add_widget(b)
                body.add_widget(row)
            scroll.add_widget(body)
            self.panel.add_widget(scroll)
        elif self.section == "news":
            self._header("MIDIA / NOTICIAS")
            self._stat_row("Mercado", f"{d['market_sentiment']:.0f}%")
            self._stat_row("Risco de crise", f"{d['crisis_risk']:.0f}%", AMBER)
            hero = GlassPanel(orientation="vertical", padding=dp(7), spacing=dp(3), size_hint_y=None, height=dp(104), bg=GLASS_LIGHT)
            hero.add_widget(label("ULTIMA HORA", color=RED, font_size=dp(7), bold=True))
            hero.add_widget(label(d["headline"], font_size=dp(9.5), bold=True))
            hero.add_widget(label(d["last_news"], color=MUTED, font_size=dp(7)))
            self.panel.add_widget(hero)
            self._action("ABRIR TELEJORNAL", lambda *_: self.game.show_newsroom())
        self.panel.add_widget(Widget())


class AnchorVisual(Widget):
    def __init__(self, tactical=False, **kwargs):
        super().__init__(**kwargs)
        self.tactical = tactical
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_once(self.redraw, 0)

    def redraw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        with self.canvas:
            Color(0.02, 0.05, 0.075, 1)
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[dp(12)])
            Color(0.07, 0.18, 0.25, 0.6)
            step = max(dp(24), w / 10)
            gx = x
            while gx < x + w:
                Line(points=[gx, y, gx, y + h], width=0.45)
                gx += step
            gy = y
            while gy < y + h:
                Line(points=[x, gy, x + w, gy], width=0.45)
                gy += step
            Color(0.58, 0.68, 0.76, 0.85)
            Ellipse(pos=(x + w * 0.40, y + h * 0.54), size=(w * 0.20, w * 0.20))
            Color(0.20, 0.32, 0.42, 0.95)
            RoundedRectangle(pos=(x + w * 0.29, y + h * 0.12), size=(w * 0.42, h * 0.48), radius=[dp(16)])
            Color(0.04, 0.11, 0.17, 1)
            RoundedRectangle(pos=(x + w * 0.12, y + h * 0.05), size=(w * 0.76, h * 0.16), radius=[dp(8)])
            if self.tactical:
                Color(RED[0], RED[1], RED[2], 0.65)
                Line(points=[x + w * 0.12, y + h * 0.80, x + w * 0.34, y + h * 0.68, x + w * 0.58, y + h * 0.82, x + w * 0.86, y + h * 0.62], width=1.2)


class NewsOverlay(FloatLayout):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.event = None
        with self.canvas.before:
            Color(0.0, 0.0, 0.0, 0.70)
            self._shade = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_shade, size=self._sync_shade)
        self.opacity = 0
        self.disabled = True
        self.card = GlassPanel(orientation="vertical", padding=dp(10), spacing=dp(7), bg=(0.025, 0.045, 0.065, 0.97), size_hint=(0.86, 0.82), pos_hint={"x": 0.07, "y": 0.09})
        self.add_widget(self.card)

    def _sync_shade(self, *_):
        self._shade.pos = self.pos
        self._shade.size = self.size

    def hide(self):
        self.opacity = 0
        self.disabled = True
        self.event = None
        self.game.overlay_open = False

    def show_news(self, headline=None, text=None, related=None):
        d = self.game.state.d
        self.event = None
        self._build(headline or d["headline"], text or d["last_news"], related or d.get("related_news", DEFAULT_RELATED_NEWS), False, None)

    def show_event(self, event):
        self.event = event
        title = event["title"]
        tactical = any(word in title.lower() for word in ("guerra", "ataque", "militar", "conflito", "fronteira"))
        self._build(title, event["text"], self.game.state.d.get("related_news", DEFAULT_RELATED_NEWS), tactical, event["choices"])

    def _build(self, title, text, related, tactical, choices):
        self.card.clear_widgets()
        self.opacity = 1
        self.disabled = False
        self.game.overlay_open = True
        top = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(6))
        top.add_widget(label("PRESIDENTE NEWS  |  PLANTAO AO VIVO", color=RED, font_size=dp(9), bold=True))
        if not choices:
            close = SmallButton(text="X", size_hint_x=None, width=dp(34))
            close.bind(on_release=lambda *_: self.game.close_news_overlay())
            top.add_widget(close)
        self.card.add_widget(top)
        body = BoxLayout(spacing=dp(8))
        body.add_widget(AnchorVisual(tactical=tactical, size_hint_x=0.34))
        story = GlassPanel(orientation="vertical", padding=dp(9), spacing=dp(5), bg=GLASS_LIGHT, size_hint_x=0.43)
        flag = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(3))
        for c in ((0.08, 0.55, 0.28, 1), (0.96, 0.82, 0.12, 1), (0.10, 0.32, 0.72, 1)):
            block = Widget(size_hint_x=0.12)
            with block.canvas:
                Color(*c)
                block._rect = Rectangle(pos=block.pos, size=block.size)
            block.bind(pos=lambda inst, _v: setattr(inst._rect, "pos", inst.pos), size=lambda inst, _v: setattr(inst._rect, "size", inst.size))
            flag.add_widget(block)
        flag.add_widget(label("BRASIL / CENTRO DE CRISE", color=MUTED, font_size=dp(6.5)))
        story.add_widget(flag)
        story.add_widget(label(title.upper(), font_size=dp(15), bold=True))
        story.add_widget(label(text, color=MUTED, font_size=dp(8), valign="top"))
        impact = self.game.state.d.get("media_impact", {})
        impact_line = f"APROVACAO {impact.get('approval', 0):+.1f}   |   MERCADO {impact.get('market', 0):+.1f}   |   CRISE {impact.get('crisis', 0):+.1f}"
        story.add_widget(label(impact_line, color=AMBER, font_size=dp(7), bold=True, size_hint_y=None, height=dp(24)))
        body.add_widget(story)
        side = GlassPanel(orientation="vertical", padding=dp(7), spacing=dp(4), bg=GLASS_LIGHT, size_hint_x=0.23)
        side.add_widget(label("RELACIONADAS", color=CYAN, font_size=dp(7), bold=True, size_hint_y=None, height=dp(22)))
        for item in list(related)[:4]:
            side.add_widget(label(f"{item.get('category', 'Geral').upper()}\n{item.get('headline', '')}", font_size=dp(6.8), size_hint_y=None, height=dp(46)))
        body.add_widget(side)
        self.card.add_widget(body)
        if choices:
            row = GridLayout(cols=len(choices), size_hint_y=None, height=dp(58), spacing=dp(5))
            for choice_title, changes in choices:
                b = SmallButton(text=choice_title)
                b.bind(on_release=lambda _btn, t=choice_title, ch=changes: self.game.resolve_event(t, ch))
                row.add_widget(b)
            self.card.add_widget(row)
        else:
            b = SmallButton(text="CONTINUAR", size_hint_y=None, height=dp(36))
            b.bind(on_release=lambda *_: self.game.close_news_overlay())
            self.card.add_widget(b)


class MapFirstRoot(FloatLayout):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.globe = GlobeWidget(game, on_country=self._country_selected, size_hint=(1, 1))
        self.add_widget(self.globe)
        self.topbar = TopBar(game, size_hint=(0.90, None), height=dp(46), pos_hint={"x": 0.065, "top": 0.985})
        self.add_widget(self.topbar)
        toolbar = GlassPanel(orientation="vertical", padding=dp(4), spacing=dp(5), bg=(0.03, 0.055, 0.08, 0.84), size_hint=(None, None), width=dp(54), height=dp(310), pos_hint={"x": 0.008, "center_y": 0.50})
        for icon, hint, section in [("gov", "GOV", "gov"), ("eco", "ECO", "eco"), ("def", "DEF", "def"), ("dip", "DIP", "dip"), ("news", "NEWS", "news"), ("save", "SAVE", "save")]:
            b = IconButton(icon=icon, hint=hint, size_hint_y=None, height=dp(45))
            if section == "save":
                b.bind(on_release=lambda *_: self.game.save_game())
            else:
                b.bind(on_release=lambda _btn, s=section: self.game.drawer.open(s))
            toolbar.add_widget(b)
        self.add_widget(toolbar)
        self.drawer = Drawer(game, size_hint=(1, 1))
        self.game.drawer = self.drawer
        self.add_widget(self.drawer)
        self.news_overlay = NewsOverlay(game, size_hint=(1, 1))
        self.game.news_overlay = self.news_overlay
        self.add_widget(self.news_overlay)
        self.status = GlassPanel(orientation="horizontal", padding=(dp(8), dp(2)), bg=(0.02, 0.04, 0.06, 0.76), size_hint=(0.44, None), height=dp(30), pos_hint={"right": 0.985, "y": 0.018})
        self.status_label = label("", color=MUTED, font_size=dp(6.5))
        self.status.add_widget(self.status_label)
        self.add_widget(self.status)

    def _country_selected(self, name):
        self.game.drawer.open("dip")
        country = self.game.state.d["countries"].get(name)
        if country:
            self.status_label.text = f"{name.upper()}  |  RELACAO {country['relation']:+d}  |  PODER {country['power']}/100"

    def refresh(self):
        self.topbar.refresh()
        d = self.game.state.d
        self.status_label.text = f"MERCADO {d['market_sentiment']:.0f}%   |   CONGRESSO {d['congress']:.0f}%   |   RISCO DE CRISE {d['crisis_risk']:.0f}%"
        if self.drawer and not self.drawer.disabled:
            self.drawer.rebuild()


class GameApp(App):
    title = APP_NAME

    def build(self):
        Window.clearcolor = BG
        self.state = GameState()
        self.state.load()
        self.playing = False
        self.overlay_open = False
        self.drawer = None
        self.news_overlay = None
        self._play_accumulator = 0.0
        self.root_view = MapFirstRoot(self)
        Clock.schedule_interval(self._tick, 0.25)
        Clock.schedule_interval(lambda _dt: self.root_view.refresh(), 0.8)
        self.root_view.refresh()
        return self.root_view

    def toggle_play(self):
        if self.overlay_open:
            return
        self.playing = not self.playing
        self.root_view.refresh()

    def _tick(self, dt):
        if not self.playing or self.overlay_open:
            return
        self._play_accumulator += dt
        if self._play_accumulator >= 1.0:
            self._play_accumulator = 0.0
            self.advance(1, from_play=True)

    def advance(self, days, from_play=False):
        if self.overlay_open:
            return
        self.state.advance_day(days)
        self.root_view.refresh()
        event = self.state.d.get("event")
        if event:
            self.playing = False
            self.show_event_overlay(event)
        elif not from_play:
            self.root_view.refresh()

    def close_news_overlay(self):
        if self.news_overlay and self.news_overlay.event:
            return
        if self.news_overlay:
            self.news_overlay.hide()
        self.root_view.refresh()

    def show_event_overlay(self, event):
        self.playing = False
        self.news_overlay.show_event(event)

    def resolve_event(self, title, changes):
        self.state.apply_choice(title, changes)
        self.news_overlay.hide()
        self.overlay_open = False
        self.root_view.refresh()
        Clock.schedule_once(lambda *_: self.show_newsroom(), 0.15)

    def show_newsroom(self):
        self.playing = False
        self.news_overlay.show_news()

    def show_press_overlay(self):
        self.playing = False
        event = {"title": "Coletiva de imprensa", "text": "Jornalista: a inflacao e o custo de vida pressionam o governo. Qual sera a resposta presidencial?", "choices": [["Reconhecer o problema", {"approval": 1.0, "congress": 0.3}], ["Defender as medidas", {"approval": 0.2, "stability": 0.2}], ["Criticar a cobertura", {"approval": -1.2, "stability": -0.5}]]}
        self.state.d["event"] = event
        self.show_event_overlay(event)

    def economic_action(self, key, amount, title):
        d = self.state.d
        effect = {}
        if key == "tax_rate":
            d[key] += amount
            d["treasury"] -= amount * 1.2
            effect["approval"] = -amount * 0.5
        elif key == "interest_rate":
            d[key] += amount
            d["inflation"] += amount * 0.15
            d["gdp_growth"] -= amount * 0.2
            effect["approval"] = 0.1 if amount < 0 else -0.1
        elif key == "social_spending":
            d[key] += amount
            d["treasury"] -= amount
            d["debt_ratio"] += amount * 0.15
            effect["approval"] = amount * 0.6
        self.state.apply_choice(title, effect)
        self.drawer.rebuild()
        self.root_view.refresh()

    def military_action(self, title, amount):
        d = self.state.d
        d["military_budget"] = max(0.1, d["military_budget"] + amount)
        if "exercicio" in title.lower():
            effect = {"stability": 1.0, "approval": 0.3}
        else:
            d["treasury"] -= amount * 1.5
            effect = {"approval": 0.1 if amount > 0 else -0.1}
        self.state.apply_choice(title, effect)
        self.drawer.rebuild()
        self.root_view.refresh()

    def negotiate(self, name):
        d = self.state.d
        country = d["countries"][name]
        country["relation"] = int(clamp(country["relation"] + random.randint(2, 6), -100, 100))
        self.state.apply_choice(f"Negociacao avanca com {name}", {"approval": 0.2, "stability": 0.1})
        self.drawer.rebuild()
        self.root_view.refresh()

    def save_game(self):
        self.state.save()
        if self.drawer:
            self.drawer.close()
        self.root_view.status_label.text = "PARTIDA SALVA"
