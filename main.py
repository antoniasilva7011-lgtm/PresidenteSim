
import json
import os
import random
from datetime import date, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


# ------------------------------------------------------------
# PRESIDENTE SIMULATOR V0.1
# Prototype: mobile geopolitical simulation.
# ------------------------------------------------------------

APP_NAME = "Presidente Simulator"
SAVE_FILE = "presidente_simulator_save.json"


COUNTRIES = {
    "Brasil": {"flag": "🇧🇷", "relation": 72, "gdp": 2.1, "power": 72},
    "Estados Unidos": {"flag": "🇺🇸", "relation": 55, "gdp": 28.8, "power": 100},
    "China": {"flag": "🇨🇳", "relation": -34, "gdp": 18.7, "power": 98},
    "Rússia": {"flag": "🇷🇺", "relation": 45, "gdp": 2.0, "power": 83},
    "Argentina": {"flag": "🇦🇷", "relation": 20, "gdp": 0.63, "power": 32},
    "França": {"flag": "🇫🇷", "relation": 38, "gdp": 3.2, "power": 70},
    "Alemanha": {"flag": "🇩🇪", "relation": 44, "gdp": 4.6, "power": 69},
    "Índia": {"flag": "🇮🇳", "relation": 30, "gdp": 3.9, "power": 73},
    "Japão": {"flag": "🇯🇵", "relation": 36, "gdp": 4.2, "power": 67},
    "México": {"flag": "🇲🇽", "relation": 28, "gdp": 1.8, "power": 43},
}

INITIAL_STATE = {
    "day": "2026-09-15",
    "approval": 57.0,
    "congress": 51.0,
    "inflation": 4.8,
    "unemployment": 7.2,
    "debt_ratio": 78.4,
    "gdp": 12.4,
    "gdp_growth": 2.3,
    "stability": 68.0,
    "coup_risk": 8.0,
    "impeachment_risk": 12.0,
    "treasury": 100.0,
    "tax_rate": 27.0,
    "interest_rate": 10.5,
    "military_budget": 2.0,
    "social_spending": 18.0,
    "last_news": "Governo inicia novo ciclo político.",
    "headline": "GOVERNO PREPARA NOVAS MEDIDAS",
    "news_tone": "neutral",
    "feed": [
        ("Carlos Silva", "O governo precisa mostrar resultados.", 1840),
        ("Mariana Costa", "Debate econômico movimenta o Congresso.", 920),
        ("João Santos", "Espero que o custo de vida caia.", 710),
    ],
    "countries": COUNTRIES,
    "event": None,
}


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def fmt_money(v):
    return f"R$ {v:,.1f} tri".replace(",", "X").replace(".", ",").replace("X", ".")


class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(4), **kwargs)
        with self.canvas.before:
            Color(0.035, 0.055, 0.09, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class StatCard(Card):
    def __init__(self, title, value, subtitle="", **kwargs):
        super().__init__(size_hint_y=None, height=dp(82), **kwargs)
        self.add_widget(Label(text=title, color=(0.65, 0.73, 0.84, 1),
                              font_size=dp(11), halign="left", valign="middle",
                              text_size=(None, dp(22))))
        self.value_label = Label(text=str(value), color=(0.95, 0.97, 1, 1),
                                 bold=True, font_size=dp(19), halign="left",
                                 valign="middle")
        self.add_widget(self.value_label)
        self.add_widget(Label(text=subtitle, color=(0.35, 0.8, 0.95, 1),
                              font_size=dp(10), halign="left"))


class StyledButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.055, 0.12, 0.20, 1))
        kwargs.setdefault("color", (0.92, 0.96, 1, 1))
        kwargs.setdefault("font_size", dp(12))
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)
        with self.canvas.after:
            Color(0.08, 0.45, 0.65, 0.75)
            self.outline = Line(rounded_rectangle=(0, 0, 100, 100, 10), width=0.8)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.outline.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(9))


class ScrollText(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(do_scroll_x=False, **kwargs)
        self.label = Label(text="", size_hint_y=None, padding=(dp(12), dp(12)),
                           color=(0.85, 0.9, 0.96, 1), font_size=dp(13),
                           halign="left", valign="top")
        self.label.bind(texture_size=self._resize)
        self.add_widget(self.label)

    def _resize(self, *_):
        self.label.height = max(self.height, self.label.texture_size[1])


class GameState:
    def __init__(self):
        self.data = json.loads(json.dumps(INITIAL_STATE, ensure_ascii=False))

    def save(self):
        path = os.path.join(App.get_running_app().user_data_dir, SAVE_FILE)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def load(self):
        path = os.path.join(App.get_running_app().user_data_dir, SAVE_FILE)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            return True
        return False

    @property
    def d(self):
        return self.data

    def advance_day(self, days=1):
        for _ in range(days):
            self._daily_tick()
        self.save()

    def _daily_tick(self):
        d = self.d
        current = date.fromisoformat(d["day"])
        d["day"] = (current + timedelta(days=1)).isoformat()

        # Economic drift
        demand = (d["gdp_growth"] - 2.0) * 0.025
        fiscal_pressure = (d["debt_ratio"] - 70) * 0.002
        d["inflation"] += random.uniform(-0.05, 0.07) + demand + fiscal_pressure
        d["inflation"] = max(0.5, min(30, d["inflation"]))

        d["unemployment"] += random.uniform(-0.08, 0.08)
        d["unemployment"] = max(2, min(30, d["unemployment"]))

        # Approval naturally reacts to economic indicators.
        target = 62 - (d["inflation"] - 4.0) * 1.2 - (d["unemployment"] - 6.0) * 0.8
        d["approval"] += (target - d["approval"]) * 0.035 + random.uniform(-0.18, 0.18)
        d["approval"] = clamp(d["approval"])

        # Congress follows approval/stability slowly.
        d["congress"] += ((d["approval"] - 50) * 0.025) + random.uniform(-0.12, 0.12)
        d["congress"] = clamp(d["congress"])

        d["stability"] += (d["approval"] - 50) * 0.006 - (d["inflation"] - 5) * 0.01
        d["stability"] = clamp(d["stability"])

        d["impeachment_risk"] = clamp(
            8 + max(0, 50 - d["approval"]) * 0.65 +
            max(0, 45 - d["congress"]) * 0.55 +
            max(0, d["inflation"] - 10) * 1.4
        )
        d["coup_risk"] = clamp(
            2 + max(0, 45 - d["stability"]) * 0.8 +
            max(0, 40 - d["approval"]) * 0.25
        )

        # Small GDP movement.
        d["gdp_growth"] += random.uniform(-0.08, 0.08)
        d["gdp_growth"] = max(-10, min(12, d["gdp_growth"]))
        d["gdp"] *= 1 + d["gdp_growth"] / 100 / 365

        # Chance of a daily event.
        if random.random() < 0.10:
            self.create_random_event()

    def create_random_event(self):
        events = [
            {
                "title": "Greve nacional",
                "text": "Sindicatos convocam paralisação contra o custo de vida.",
                "choices": [
                    ("Negociar", {"approval": 1.5, "stability": 1}),
                    ("Reprimir", {"approval": -2.5, "stability": -2}),
                    ("Ignorar", {"approval": -1, "stability": -1}),
                ],
            },
            {
                "title": "Pressão no mercado",
                "text": "Investidores demonstram preocupação com a trajetória fiscal.",
                "choices": [
                    ("Anunciar corte de gastos", {"debt_ratio": -0.7, "approval": -0.8}),
                    ("Aumentar impostos", {"debt_ratio": -1.0, "approval": -1.5}),
                    ("Manter política", {"approval": 0.3, "stability": -0.5}),
                ],
            },
            {
                "title": "Crise diplomática",
                "text": "Um país estrangeiro fez uma declaração hostil.",
                "choices": [
                    ("Responder diplomaticamente", {"stability": 0.5, "approval": 0.5}),
                    ("Adotar tom duro", {"approval": 1.0, "stability": -0.5}),
                    ("Não responder", {"approval": -0.4}),
                ],
            },
            {
                "title": "Escândalo no governo",
                "text": "Documentos levantam suspeitas envolvendo uma autoridade.",
                "choices": [
                    ("Abrir investigação", {"approval": 1.2, "congress": 0.8}),
                    ("Defender o ministro", {"approval": -2.0, "congress": -1}),
                    ("Exonerar imediatamente", {"approval": 0.5, "stability": -0.2}),
                ],
            },
        ]
        self.d["event"] = random.choice(events)

    def apply_choice(self, changes):
        for key, value in changes.items():
            if key in ("approval", "congress", "stability", "coup_risk", "impeachment_risk",
                       "inflation", "unemployment", "debt_ratio", "treasury", "tax_rate"):
                self.d[key] += value
                if key in ("approval", "congress", "stability", "coup_risk", "impeachment_risk"):
                    self.d[key] = clamp(self.d[key])
        self.d["event"] = None
        self.d["last_news"] = "O governo tomou uma decisão diante de uma nova crise."
        self.d["headline"] = "GOVERNO TOMA DECISÃO EM MEIO À CRISE"
        self.d["feed"].insert(0, ("SocialNet", "A decisão do governo divide opiniões.", random.randint(1200, 8000)))
        self.d["feed"] = self.d["feed"][:8]
        self.save()


class CabinetView(BoxLayout):
    def __init__(self, game, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.game = game
        self.padding = dp(12)
        self.spacing = dp(10)
        self.build()

    def build(self):
        # stylized 3D-like office background
        with self.canvas.before:
            Color(0.018, 0.027, 0.045, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            Color(0.06, 0.12, 0.18, 1)
            self.wall = Rectangle(pos=(0, self.height * 0.42), size=(self.width, self.height * 0.58))
        self.bind(pos=self._sync, size=self._sync)

        header = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(8))
        header.add_widget(Label(text="🇧🇷  PRESIDENTE SIMULATOR", font_size=dp(18), bold=True,
                                color=(0.95, 0.98, 1, 1), halign="left"))
        self.date_label = Label(text="", size_hint_x=0.42, font_size=dp(12),
                                color=(0.55, 0.82, 1, 1))
        header.add_widget(self.date_label)
        self.add_widget(header)

        room = BoxLayout(spacing=dp(12))

        # left: desk
        left = BoxLayout(orientation="vertical", size_hint_x=0.63, spacing=dp(10))
        tv = Card(size_hint_y=0.45)
        tv.add_widget(Label(text="📺  TELEJORNAL — AO VIVO", color=(0.4, 0.8, 1, 1),
                           bold=True, font_size=dp(13)))
        self.tv_headline = Label(text="", font_size=dp(17), bold=True,
                                 color=(1, 1, 1, 1), halign="center", valign="middle")
        tv.add_widget(self.tv_headline)
        self.tv_news = Label(text="", font_size=dp(11), color=(0.7, 0.78, 0.86, 1),
                             halign="center")
        tv.add_widget(self.tv_news)
        left.add_widget(tv)

        desk = Card(size_hint_y=0.55)
        desk.add_widget(Label(text="MESA PRESIDENCIAL", color=(0.75, 0.82, 0.9, 1),
                              bold=True, font_size=dp(11)))
        grid = GridLayout(cols=2, spacing=dp(8))
        for text, cb in [
            ("☎ TELEFONE DE CRISE", lambda *_: self.game.show_message(
                "Telefone de crise", "Nenhuma chamada urgente no momento.")),
            ("📁 PASTAS DE LEIS", lambda *_: self.game.show_screen("politics")),
            ("🌎 GLOBO 3D", lambda *_: self.game.show_screen("map")),
            ("💾 SALVAR PARTIDA", lambda *_: self.game.save_game()),
        ]:
            b = StyledButton(text=text)
            b.bind(on_release=cb)
            grid.add_widget(b)
        desk.add_widget(grid)
        left.add_widget(desk)
        room.add_widget(left)

        # right: status
        right = BoxLayout(orientation="vertical", size_hint_x=0.37, spacing=dp(8))
        self.stats = GridLayout(cols=1, spacing=dp(7))
        right.add_widget(self.stats)
        room.add_widget(right)
        self.add_widget(room)

        nav = GridLayout(cols=6, size_hint_y=None, height=dp(54), spacing=dp(5))
        for text, screen in [
            ("🏛 Governo", "cabinet"), ("💰 Economia", "economy"), ("🏛 Política", "politics"),
            ("⚔ Militar", "military"), ("🌎 Diplomacia", "diplomacy"), ("📰 Mídia", "media"),
        ]:
            b = StyledButton(text=text, font_size=dp(9))
            b.bind(on_release=lambda _, s=screen: self.game.show_screen(s))
            nav.add_widget(b)
        self.add_widget(nav)
        self.refresh()

    def _sync(self, *_):
        self.bg.pos, self.bg.size = self.pos, self.size
        self.wall.pos = (self.x, self.y + self.height * 0.42)
        self.wall.size = (self.width, self.height * 0.58)

    def refresh(self):
        d = self.game.state.d
        self.date_label.text = d["day"]
        self.tv_headline.text = "🔴 " + d["headline"]
        self.tv_news.text = d["last_news"]

        self.stats.clear_widgets()
        values = [
            ("APROVAÇÃO", f'{d["approval"]:.0f}%', "popular"),
            ("PIB", fmt_money(d["gdp"]), f'{d["gdp_growth"]:+.1f}% crescimento'),
            ("INFLAÇÃO", f'{d["inflation"]:.1f}%', "IPCA"),
            ("DESEMPREGO", f'{d["unemployment"]:.1f}%', "mercado de trabalho"),
            ("CONGRESSO", f'{d["congress"]:.0f}%', "apoio parlamentar"),
            ("IMPEACHMENT", f'{d["impeachment_risk"]:.0f}%', "risco estimado"),
        ]
        for title, value, sub in values:
            self.stats.add_widget(StatCard(title, value, sub))


class EconomyView(BoxLayout):
    def __init__(self, game, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(10), **kwargs)
        self.game = game
        self.add_widget(Label(text="💰 ECONOMIA", size_hint_y=None, height=dp(45),
                              font_size=dp(21), bold=True, color=(0.9, 0.97, 1, 1)))
        self.grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.add_widget(self.grid)
        actions = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(120))
        for text, cb in [
            ("Imposto -1 p.p.", lambda *_: self.change("tax_rate", -1, "Impostos reduzidos.")),
            ("Imposto +1 p.p.", lambda *_: self.change("tax_rate", 1, "Impostos aumentados.")),
            ("Juros -0,5 p.p.", lambda *_: self.change("interest_rate", -0.5, "Banco Central recebe pressão por juros menores.")),
            ("Gasto social +1", lambda *_: self.change("social_spending", 1, "Gasto social ampliado.")),
        ]:
            b = StyledButton(text=text)
            b.bind(on_release=cb)
            actions.add_widget(b)
        self.add_widget(actions)
        back = StyledButton(text="← Voltar ao gabinete", size_hint_y=None, height=dp(45))
        back.bind(on_release=lambda *_: self.game.show_screen("cabinet"))
        self.add_widget(back)
        self.refresh()

    def change(self, key, amount, news):
        d = self.game.state.d
        d[key] += amount
        if key == "tax_rate":
            d["treasury"] -= amount * 1.2
            d["approval"] += -amount * 0.5
        elif key == "interest_rate":
            d["inflation"] += amount * 0.15
            d["gdp_growth"] -= amount * 0.2
        elif key == "social_spending":
            d["treasury"] -= amount
            d["approval"] += amount * 0.6
            d["debt_ratio"] += amount * 0.15
        d["approval"] = clamp(d["approval"])
        d["last_news"] = news
        d["headline"] = news.upper()
        self.game.refresh_all()

    def refresh(self):
        self.grid.clear_widgets()
        d = self.game.state.d
        stats = [
            ("PIB", fmt_money(d["gdp"]), f"Crescimento {d['gdp_growth']:+.1f}%"),
            ("Inflação", f"{d['inflation']:.1f}%", "meta de estabilidade"),
            ("Desemprego", f"{d['unemployment']:.1f}%", "força de trabalho"),
            ("Dívida/PIB", f"{d['debt_ratio']:.1f}%", "sustentabilidade fiscal"),
            ("Juros", f"{d['interest_rate']:.1f}%", "taxa básica"),
            ("Impostos", f"{d['tax_rate']:.1f}%", "carga tributária"),
            ("Tesouro", f"{d['treasury']:.1f}", "reserva relativa"),
            ("Gasto social", f"{d['social_spending']:.1f}", "índice orçamentário"),
        ]
        for a, b, c in stats:
            self.grid.add_widget(StatCard(a, b, c))


class PoliticsView(BoxLayout):
    def __init__(self, game, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(10), **kwargs)
        self.game = game
        self.add_widget(Label(text="🏛 POLÍTICA E GOVERNO", size_hint_y=None, height=dp(45),
                              font_size=dp(21), bold=True, color=(0.9, 0.97, 1, 1)))
        self.info = Label(text="", halign="left", valign="top", font_size=dp(14))
        self.add_widget(self.info)
        laws = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, height=dp(210))
        for title, effect in [
            ("📜 Reforma Tributária", {"congress": -2, "approval": -1}),
            ("🏥 Expansão da Saúde Pública", {"congress": 1, "approval": 2, "debt_ratio": 0.8}),
            ("🎓 Plano Nacional de Educação", {"congress": 0.5, "approval": 1.5, "debt_ratio": 0.5}),
            ("🛡 Lei de Segurança Nacional", {"congress": -1, "approval": -1, "stability": 1}),
        ]:
            b = StyledButton(text=title)
            b.bind(on_release=lambda _, e=effect, t=title: self.pass_law(t, e))
            laws.add_widget(b)
        self.add_widget(laws)
        back = StyledButton(text="← Voltar", size_hint_y=None, height=dp(45))
        back.bind(on_release=lambda *_: self.game.show_screen("cabinet"))
        self.add_widget(back)
        self.refresh()

    def pass_law(self, title, effect):
        d = self.game.state.d
        if d["congress"] < 40:
            self.game.show_message("Lei rejeitada", "O apoio parlamentar é insuficiente para aprovar esta proposta.")
            return
        for k, v in effect.items():
            d[k] += v
            if k in ("approval", "congress", "stability"):
                d[k] = clamp(d[k])
        d["last_news"] = f"{title} foi aprovado pelo Congresso."
        d["headline"] = "CONGRESSO APROVA NOVA LEI"
        self.game.refresh_all()

    def refresh(self):
        d = self.game.state.d
        self.info.text = (
            f"[b]Apoio no Congresso:[/b] {d['congress']:.0f}%\n"
            f"[b]Aprovação:[/b] {d['approval']:.0f}%\n"
            f"[b]Estabilidade:[/b] {d['stability']:.0f}%\n"
            f"[b]Risco de impeachment:[/b] {d['impeachment_risk']:.0f}%\n\n"
            "Projetos de lei exigem apoio parlamentar. "
            "Cada decisão altera grupos sociais e pode gerar novas crises."
        )
        self.info.markup = True


class DiplomacyView(BoxLayout):
    def __init__(self, game, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(8), **kwargs)
        self.game = game
        self.add_widget(Label(text="🌎 DIPLOMACIA", size_hint_y=None, height=dp(45),
                              font_size=dp(21), bold=True, color=(0.9, 0.97, 1, 1)))
        scroll = ScrollView(do_scroll_x=False)
        self.list = GridLayout(cols=1, spacing=dp(7), size_hint_y=None, padding=(0, 0, 0, dp(8)))
        self.list.bind(minimum_height=self.list.setter("height"))
        scroll.add_widget(self.list)
        self.add_widget(scroll)
        back = StyledButton(text="← Voltar", size_hint_y=None, height=dp(45))
        back.bind(on_release=lambda *_: self.game.show_screen("cabinet"))
        self.add_widget(back)
        self.refresh()

    def refresh(self):
        self.list.clear_widgets()
        for name, c in self.game.state.d["countries"].items():
            if name == "Brasil":
                continue
            row = Card(orientation="horizontal", size_hint_y=None, height=dp(75), spacing=dp(7))
            label = Label(text=f"{c['flag']}  {name}\nRelação: {c['relation']:+d}   Poder: {c['power']}/100",
                          halign="left", color=(0.9, 0.95, 1, 1))
            row.add_widget(label)
            b = StyledButton(text="NEGOCIAR", size_hint_x=0.35)
            b.bind(on_release=lambda _, n=name: self.negotiate(n))
            row.add_widget(b)
            self.list.add_widget(row)

    def negotiate(self, name):
        c = self.game.state.d["countries"][name]
        c["relation"] = int(clamp(c["relation"] + random.randint(2, 6), -100, 100))
        self.game.state.d["approval"] = clamp(self.game.state.d["approval"] + 0.2)
        self.game.state.d["last_news"] = f"Negociação diplomática avançou com {name}."
        self.game.state.d["headline"] = f"BRASIL AVANÇA EM NEGOCIAÇÕES COM {name.upper()}"
        self.game.refresh_all()


class MapView(Widget):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.selected = "Brasil"
        self.bind(pos=self.draw, size=self.draw)
        self.draw()

    def draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(0.012, 0.025, 0.055, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Stylized "3D globe" / world map panel.
            Color(0.03, 0.16, 0.25, 1)
            Ellipse(pos=(self.x + self.width * .08, self.y + self.height * .18),
                    size=(self.width * .84, self.height * .68))
            Color(0.06, 0.30, 0.20, 0.75)
            # continents as abstract polygons
            for pts in [
                [(0.17,.60),(0.28,.70),(0.33,.58),(0.28,.43),(0.20,.35),(0.14,.46)],
                [(0.42,.67),(0.55,.73),(0.66,.64),(0.71,.51),(0.61,.43),(0.50,.49)],
                [(0.70,.40),(0.82,.48),(0.88,.35),(0.78,.25),(0.68,.30)],
                [(0.37,.30),(0.45,.22),(0.50,.12),(0.43,.08),(0.35,.17)],
            ]:
                Color(0.08, 0.38, 0.25, 1)
                pts2 = [(self.x + self.width*x, self.y + self.height*y) for x,y in pts]
                from kivy.graphics import Mesh
                Mesh(vertices=[v for p in pts2 for v in (*p, 0, 0)],
                     indices=list(range(len(pts2))), mode="triangle_fan")

            # diplomatic routes
            Color(0.1, 0.65, 0.95, 0.65)
            Line(points=[
                self.x+self.width*.26, self.y+self.height*.51,
                self.x+self.width*.48, self.y+self.height*.63,
                self.x+self.width*.73, self.y+self.height*.55
            ], width=1.2)

        # interactive country buttons
        self.buttons = []
        positions = [
            ("🇧🇷 Brasil", .22, .45),
            ("🇺🇸 EUA", .34, .67),
            ("🇨🇳 China", .72, .58),
            ("🇦🇷 Argentina", .22, .32),
            ("🇷🇺 Rússia", .65, .72),
            ("🇮🇳 Índia", .68, .45),
        ]
        for text, x, y in positions:
            b = StyledButton(text=text, size_hint=(None, None),
                             size=(dp(115), dp(38)),
                             pos=(self.x + self.width*x, self.y + self.height*y))
            b.bind(on_release=lambda _, t=text: self.select_country(t))
            self.add_widget(b)
            self.buttons.append(b)

    def select_country(self, text):
        self.selected = text
        name = text.split(" ", 1)[1]
        if name == "EUA":
            name = "Estados Unidos"
        c = self.game.state.d["countries"].get(name)
        if c:
            self.game.show_message(name, f"Relação diplomática: {c['relation']:+d}\nPoder: {c['power']}/100\nPIB: US$ {c['gdp']:.2f} tri")

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        return True


class MediaView(BoxLayout):
    def __init__(self, game, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(8), **kwargs)
        self.game = game
        self.add_widget(Label(text="📰 MÍDIA E IMPRENSA", size_hint_y=None, height=dp(45),
                              font_size=dp(21), bold=True, color=(0.9, 0.97, 1, 1)))
        self.content = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(self.content)
        self.add_widget(scroll)

        press = StyledButton(text="🎙 CONVOCAR COLETIVA DE IMPRENSA", size_hint_y=None, height=dp(52))
        press.bind(on_release=lambda *_: self.game.press_conference())
        self.add_widget(press)
        back = StyledButton(text="← Voltar", size_hint_y=None, height=dp(45))
        back.bind(on_release=lambda *_: self.game.show_screen("cabinet"))
        self.add_widget(back)
        self.refresh()

    def refresh(self):
        self.content.clear_widgets()
        d = self.game.state.d

        headline = Card(size_hint_y=None, height=dp(125))
        headline.add_widget(Label(text="CAPA DO DIA", color=(0.5, 0.8, 1, 1), bold=True))
        headline.add_widget(Label(text=d["headline"], font_size=dp(17), bold=True,
                                  color=(1, 1, 1, 1), halign="center"))
        headline.add_widget(Label(text=d["last_news"], color=(0.65, 0.75, 0.85, 1),
                                  halign="center"))
        self.content.add_widget(headline)

        for name, text, likes in d["feed"]:
            row = Card(orientation="vertical", size_hint_y=None, height=dp(86))
            row.add_widget(Label(text=f"@{name.replace(' ', '').lower()}",
                                 color=(0.4, 0.8, 1, 1), halign="left"))
            row.add_widget(Label(text=text, color=(0.9, 0.94, 1, 1), halign="left"))
            row.add_widget(Label(text=f"♥ {likes:,}".replace(",", "."), color=(0.55, 0.65, 0.75, 1),
                                 halign="left", font_size=dp(10)))
            self.content.add_widget(row)


class MilitaryView(BoxLayout):
    def __init__(self, game, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(10), **kwargs)
        self.game = game
        self.add_widget(Label(text="⚔ FORÇAS ARMADAS", size_hint_y=None, height=dp(45),
                              font_size=dp(21), bold=True, color=(0.9, 0.97, 1, 1)))
        self.info = Label(text="", halign="left", valign="top", font_size=dp(14))
        self.add_widget(self.info)
        for text, change in [
            ("Aumentar orçamento militar", 0.2),
            ("Reduzir orçamento militar", -0.2),
            ("Realizar exercício militar", 1.0),
        ]:
            b = StyledButton(text=text, size_hint_y=None, height=dp(50))
            b.bind(on_release=lambda _, c=change, t=text: self.action(t, c))
            self.add_widget(b)
        back = StyledButton(text="← Voltar", size_hint_y=None, height=dp(45))
        back.bind(on_release=lambda *_: self.game.show_screen("cabinet"))
        self.add_widget(back)
        self.refresh()

    def action(self, title, change):
        d = self.game.state.d
        d["military_budget"] = max(0.1, d["military_budget"] + change)
        if "exercício" in title:
            d["stability"] = clamp(d["stability"] + 1)
            d["approval"] = clamp(d["approval"] + 0.3)
        else:
            d["treasury"] -= change * 1.5
        d["last_news"] = title + "."
        d["headline"] = "GOVERNO ANUNCIA NOVA MEDIDA MILITAR"
        self.game.refresh_all()

    def refresh(self):
        d = self.game.state.d
        self.info.text = (
            f"[b]Orçamento militar:[/b] {d['military_budget']:.1f}% do PIB\n"
            f"[b]Estabilidade nacional:[/b] {d['stability']:.0f}%\n"
            f"[b]Risco de golpe:[/b] {d['coup_risk']:.0f}%\n\n"
            "A V0.1 usa um modelo abstrato de defesa. "
            "A futura versão adicionará forças terrestres, aéreas, navais, bases e frentes de batalha."
        )
        self.info.markup = True


class GameApp(App):
    title = APP_NAME

    def build(self):
        Window.clearcolor = (0.01, 0.02, 0.035, 1)
        self.state = GameState()
        self.state.load()

        self.root_box = BoxLayout(orientation="vertical")
        self.content = BoxLayout()
        self.root_box.add_widget(self.content)

        bottom = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(5), padding=dp(5))
        self.day_button = StyledButton(text="▶ AVANÇAR 1 DIA")
        self.day_button.bind(on_release=lambda *_: self.advance(1))
        bottom.add_widget(self.day_button)

        b2 = StyledButton(text="▶ 7 DIAS")
        b2.bind(on_release=lambda *_: self.advance(7))
        bottom.add_widget(b2)

        save = StyledButton(text="💾 SALVAR")
        save.bind(on_release=lambda *_: self.save_game())
        bottom.add_widget(save)

        self.root_box.add_widget(bottom)
        self.root = self.root_box
        self.views = {}
        self.show_screen("cabinet")
        Clock.schedule_interval(self.auto_refresh, 0.5)
        return self.root

    def get_view(self, name):
        if name not in self.views:
            if name == "cabinet":
                self.views[name] = CabinetView(self)
            elif name == "economy":
                self.views[name] = EconomyView(self)
            elif name == "politics":
                self.views[name] = PoliticsView(self)
            elif name == "diplomacy":
                self.views[name] = DiplomacyView(self)
            elif name == "map":
                self.views[name] = MapView(self)
            elif name == "media":
                self.views[name] = MediaView(self)
            elif name == "military":
                self.views[name] = MilitaryView(self)
        return self.views[name]

    def show_screen(self, name):
        self.content.clear_widgets()
        self.content.add_widget(self.get_view(name))
        self.refresh_all()

    def refresh_all(self):
        for v in self.views.values():
            if hasattr(v, "refresh"):
                v.refresh()

    def auto_refresh(self, _dt):
        self.refresh_all()
        if self.state.d.get("event"):
            self.show_event_if_needed()

    def advance(self, days):
        if self.state.d.get("event"):
            self.show_event_if_needed()
            return
        self.state.advance_day(days)
        self.refresh_all()
        self.show_event_if_needed()

    def show_event_if_needed(self):
        event = self.state.d.get("event")
        if not event:
            return
        self.state.d["event"] = None  # reserve it while popup is visible
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        box.add_widget(Label(text=event["title"], font_size=dp(19), bold=True,
                             color=(1, 0.85, 0.45, 1)))
        box.add_widget(Label(text=event["text"], color=(0.9, 0.93, 1, 1)))
        choices = GridLayout(cols=1, spacing=dp(7))
        popup = Popup(title="🔴 EVENTO NACIONAL", content=box,
                      size_hint=(0.9, 0.72), auto_dismiss=False)
        for title, changes in event["choices"]:
            b = StyledButton(text=title)
            b.bind(on_release=lambda _, ch=changes: self.finish_event(popup, ch))
            choices.add_widget(b)
        box.add_widget(choices)
        popup.open()

    def finish_event(self, popup, changes):
        self.state.apply_choice(changes)
        popup.dismiss()
        self.refresh_all()

    def press_conference(self):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        box.add_widget(Label(text="Jornalista: “A inflação está subindo. O governo perdeu o controle?”",
                             color=(0.9, 0.94, 1, 1), halign="left"))
        popup = Popup(title="🎙 COLETIVA DE IMPRENSA", content=box,
                      size_hint=(0.92, 0.8), auto_dismiss=False)
        options = [
            ("“Não há motivo para preocupação.”", {"approval": -1.2, "inflation": 0.1}),
            ("“Estamos trabalhando para resolver.”", {"approval": 0.5}),
            ("“A situação é séria e assumimos nossa responsabilidade.”", {"approval": 1.5, "congress": 0.5}),
            ("“A imprensa está exagerando.”", {"approval": -1.5, "stability": -0.5}),
        ]
        for text, changes in options:
            b = StyledButton(text=text, size_hint_y=None, height=dp(52))
            b.bind(on_release=lambda _, ch=changes: self.finish_press(popup, ch))
            box.add_widget(b)
        popup.open()

    def finish_press(self, popup, changes):
        for k, v in changes.items():
            self.state.d[k] += v
            if k in ("approval", "congress", "stability"):
                self.state.d[k] = clamp(self.state.d[k])
        self.state.d["headline"] = "PRESIDENTE FALA EM COLETIVA"
        self.state.d["last_news"] = "Mercado e população repercutem a declaração presidencial."
        self.state.d["feed"].insert(0, ("Repórter", "A coletiva presidencial gera forte repercussão.", random.randint(2000, 15000)))
        self.state.d["feed"] = self.state.d["feed"][:8]
        self.state.save()
        popup.dismiss()
        self.refresh_all()

    def save_game(self):
        self.state.save()
        self.show_message("Partida salva", "O estado atual foi salvo no armazenamento do aplicativo.")

    def show_message(self, title, message):
        Popup(title=title, content=Label(text=message, color=(0.9, 0.94, 1, 1),
                                         halign="center", valign="middle"),
              size_hint=(0.82, 0.35)).open()


if __name__ == "__main__":
    GameApp().run()
