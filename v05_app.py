import random

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from v04_app import (
    AMBER,
    BG,
    CYAN,
    GLASS,
    GLASS_DARK,
    GLASS_LIGHT,
    GREEN,
    MUTED,
    RED,
    TEXT,
    AnchorVisual,
    Drawer,
    GameApp as V04GameApp,
    GlassPanel,
    MapFirstRoot,
    NewsOverlay,
    SmallButton,
    clamp,
    label,
)

APP_NAME = "Presidente Simulator V0.5"

MEDIA_OUTLETS = [
    ("AGENCIA NACIONAL", "NEUTRO"),
    ("DIARIO PUBLICO", "CRITICO"),
    ("BRASIL EM FOCO", "GOVERNISTA"),
]


def ensure_media_state(data):
    data.setdefault("press_credibility", 58.0)
    data.setdefault("press_relation", 50.0)
    data.setdefault("media_attention", 25.0)
    data.setdefault("news_urgency", 0)
    data.setdefault("news_category", "Politica")
    data.setdefault("news_history", [])
    data.setdefault("feed", [])
    if not data["news_history"]:
        data["news_history"].append({
            "category": "Politica",
            "urgency": 1,
            "headline": data.get("headline", "Governo inicia novo ciclo"),
            "text": data.get("last_news", "O governo inicia uma nova etapa."),
            "day": data.get("day", ""),
        })


def compact_stat(title_text, value_text, accent=TEXT):
    row = GlassPanel(
        orientation="horizontal",
        padding=(dp(7), dp(2)),
        size_hint_y=None,
        height=dp(31),
        bg=GLASS_LIGHT,
    )
    row.add_widget(label(title_text, color=MUTED, font_size=dp(6.6)))
    row.add_widget(label(value_text, color=accent, font_size=dp(8.2), bold=True, halign="right"))
    return row


class LeaderSilhouette(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_once(self.redraw, 0)

    def redraw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        with self.canvas:
            Color(0.035, 0.08, 0.12, 1)
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[dp(9)])
            Color(CYAN[0], CYAN[1], CYAN[2], 0.20)
            Line(rounded_rectangle=(x, y, w, h, dp(9)), width=0.8)
            Color(0.36, 0.45, 0.54, 1)
            head = min(w, h) * 0.22
            Ellipse(pos=(x + w * 0.5 - head, y + h * 0.60 - head), size=(head * 2, head * 2))
            Color(0.15, 0.23, 0.31, 1)
            RoundedRectangle(
                pos=(x + w * 0.27, y + h * 0.12),
                size=(w * 0.46, h * 0.48),
                radius=[dp(14)],
            )


class ImpactBadge(GlassPanel):
    def __init__(self, title_text, value=0.0, inverse=False, **kwargs):
        super().__init__(orientation="vertical", padding=dp(5), spacing=dp(1), bg=GLASS_LIGHT, **kwargs)
        self.inverse = inverse
        self.title_label = label(title_text.upper(), color=MUTED, font_size=dp(5.8), bold=True)
        self.value_label = label("0.0", font_size=dp(10), bold=True)
        self.add_widget(self.title_label)
        self.add_widget(self.value_label)
        self.set_value(value)

    def set_value(self, value):
        value = float(value)
        if abs(value) < 0.05:
            color = MUTED
        else:
            good = value > 0
            if self.inverse:
                good = not good
            color = GREEN if good else RED
        prefix = "+" if value > 0 else ""
        self.value_label.text = f"{prefix}{value:.1f}"
        self.value_label.color = color


class MediaDrawer(Drawer):
    """V0.5 newsroom dashboard: imprensa, jornais, rede social e arquivo."""

    def rebuild(self):
        if self.section != "news":
            super().rebuild()
            return

        self.panel.clear_widgets()
        d = self.game.state.d
        ensure_media_state(d)
        self._header("MIDIA / CENTRAL DE NOTICIAS")

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        body = GridLayout(cols=1, spacing=dp(5), size_hint_y=None, padding=(0, 0, 0, dp(6)))
        body.bind(minimum_height=body.setter("height"))

        stats = GridLayout(cols=2, spacing=dp(4), size_hint_y=None, height=dp(66))
        stats.add_widget(compact_stat("Credibilidade", f"{d['press_credibility']:.0f}%", CYAN))
        stats.add_widget(compact_stat("Relacao com imprensa", f"{d['press_relation']:.0f}%"))
        stats.add_widget(compact_stat("Mercado", f"{d['market_sentiment']:.0f}%", GREEN if d["market_sentiment"] >= 50 else RED))
        stats.add_widget(compact_stat("Risco de crise", f"{d['crisis_risk']:.0f}%", AMBER))
        body.add_widget(stats)

        hero = GlassPanel(orientation="vertical", padding=dp(7), spacing=dp(2), size_hint_y=None, height=dp(92), bg=GLASS_LIGHT)
        urgency = int(d.get("news_urgency", 0))
        urgency_text = "PLANTAO" if urgency >= 3 else "DESTAQUE" if urgency == 2 else "ULTIMAS NOTICIAS"
        hero.add_widget(label(urgency_text, color=RED if urgency >= 3 else AMBER, font_size=dp(6.5), bold=True))
        hero.add_widget(label(d["headline"], font_size=dp(8.8), bold=True))
        hero.add_widget(label(d["last_news"], color=MUTED, font_size=dp(6.6)))
        body.add_widget(hero)

        body.add_widget(label("CAPAS / LINHAS EDITORIAIS", color=CYAN, font_size=dp(6.8), bold=True, size_hint_y=None, height=dp(20)))
        for outlet, stance in MEDIA_OUTLETS:
            card = GlassPanel(orientation="vertical", padding=dp(6), spacing=dp(1), size_hint_y=None, height=dp(58), bg=GLASS_DARK)
            card.add_widget(label(f"{outlet}  |  {stance}", color=AMBER if stance == "CRITICO" else CYAN, font_size=dp(5.8), bold=True))
            card.add_widget(label(self.game.editorial_headline(stance), font_size=dp(6.8), bold=True))
            body.add_widget(card)

        body.add_widget(label("REDE SOCIAL / REPERCUSSAO", color=CYAN, font_size=dp(6.8), bold=True, size_hint_y=None, height=dp(20)))
        for name, text, likes in list(d.get("feed", []))[:4]:
            social = GlassPanel(orientation="vertical", padding=dp(5), spacing=dp(1), size_hint_y=None, height=dp(50), bg=GLASS_LIGHT)
            social.add_widget(label(f"@{str(name).replace(' ', '').lower()}   {int(likes):,} curtidas".replace(",", "."), color=MUTED, font_size=dp(5.6)))
            social.add_widget(label(str(text), font_size=dp(6.5)))
            body.add_widget(social)

        body.add_widget(label("ARQUIVO RECENTE", color=CYAN, font_size=dp(6.8), bold=True, size_hint_y=None, height=dp(20)))
        for item in d.get("news_history", [])[:4]:
            body.add_widget(label(
                f"{item.get('day', '')}  |  {item.get('category', 'Geral').upper()}\n{item.get('headline', '')}",
                color=MUTED,
                font_size=dp(6.0),
                size_hint_y=None,
                height=dp(38),
            ))

        scroll.add_widget(body)
        self.panel.add_widget(scroll)

        actions = GridLayout(cols=2, spacing=dp(4), size_hint_y=None, height=dp(34))
        tv = SmallButton(text="ABRIR TELEJORNAL")
        tv.bind(on_release=lambda *_: self.game.show_newsroom())
        press = SmallButton(text="COLETIVA")
        press.bind(on_release=lambda *_: self.game.show_press_overlay())
        actions.add_widget(tv)
        actions.add_widget(press)
        self.panel.add_widget(actions)


class MediaNewsOverlay(NewsOverlay):
    """Plantao automatico com telejornal, lider, jornais, social e impacto imediato."""

    def _build(self, title, text, related, tactical, choices):
        self.card.clear_widgets()
        self.opacity = 1
        self.disabled = False
        self.game.overlay_open = True

        d = self.game.state.d
        ensure_media_state(d)
        urgency = int(d.get("news_urgency", 3 if choices else 2))
        category = d.get("news_category", "Politica")

        top = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(5))
        top.add_widget(label("PRESIDENTE NEWS", color=CYAN, font_size=dp(8), bold=True, size_hint_x=0.22))
        top.add_widget(label("AO VIVO" if urgency >= 2 else "NOTICIAS", color=RED if urgency >= 3 else AMBER, font_size=dp(7), bold=True, size_hint_x=0.13))
        top.add_widget(label(f"{category.upper()}  |  {d.get('day', '')}", color=MUTED, font_size=dp(6.4)))
        if not choices:
            close = SmallButton(text="X", size_hint_x=None, width=dp(32))
            close.bind(on_release=lambda *_: self.game.close_news_overlay())
            top.add_widget(close)
        self.card.add_widget(top)

        body = BoxLayout(spacing=dp(6))

        studio = GlassPanel(orientation="vertical", padding=dp(6), spacing=dp(4), bg=GLASS_DARK, size_hint_x=0.27)
        studio.add_widget(label("ESTUDIO / ANCORA", color=CYAN, font_size=dp(6.2), bold=True, size_hint_y=None, height=dp(20)))
        studio.add_widget(AnchorVisual(tactical=tactical))
        studio.add_widget(label("BOLETIM EM TEMPO REAL", color=MUTED, font_size=dp(5.8), halign="center", size_hint_y=None, height=dp(22)))
        body.add_widget(studio)

        story = GlassPanel(orientation="vertical", padding=dp(7), spacing=dp(4), bg=GLASS_LIGHT, size_hint_x=0.45)
        flag_row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(5))
        leader = LeaderSilhouette(size_hint_x=None, width=dp(54))
        flag_row.add_widget(leader)
        flag_info = BoxLayout(orientation="vertical")
        flag_info.add_widget(label("BRASIL", color=CYAN, font_size=dp(7), bold=True))
        flag_info.add_widget(label("GOVERNO / CENTRO DE CRISE", color=MUTED, font_size=dp(5.4)))
        flag_row.add_widget(flag_info)
        story.add_widget(flag_row)
        story.add_widget(label(title.upper(), font_size=dp(13), bold=True))
        story.add_widget(label(text, color=MUTED, font_size=dp(7.2), valign="top"))
        story.add_widget(label(
            f"CREDIBILIDADE {d['press_credibility']:.0f}%   |   IMPRENSA {d['press_relation']:.0f}%",
            color=AMBER,
            font_size=dp(6.0),
            bold=True,
            size_hint_y=None,
            height=dp(21),
        ))
        body.add_widget(story)

        side = GlassPanel(orientation="vertical", padding=dp(6), spacing=dp(3), bg=GLASS_LIGHT, size_hint_x=0.28)
        side.add_widget(label("REPERCUSSAO", color=CYAN, font_size=dp(6.4), bold=True, size_hint_y=None, height=dp(20)))
        for item in list(related)[:2]:
            side.add_widget(label(
                f"{item.get('category', 'Geral').upper()}\n{item.get('headline', '')}",
                font_size=dp(6.2),
                size_hint_y=None,
                height=dp(42),
            ))
        side.add_widget(label("REDES SOCIAIS", color=CYAN, font_size=dp(6.2), bold=True, size_hint_y=None, height=dp(19)))
        for name, post, likes in list(d.get("feed", []))[:2]:
            side.add_widget(label(
                f"@{str(name).replace(' ', '').lower()}  {int(likes):,}\n{post}".replace(",", "."),
                color=MUTED,
                font_size=dp(5.7),
                size_hint_y=None,
                height=dp(42),
            ))
        side.add_widget(label("JORNAIS", color=CYAN, font_size=dp(6.2), bold=True, size_hint_y=None, height=dp(19)))
        for outlet, stance in MEDIA_OUTLETS[:2]:
            side.add_widget(label(f"{outlet}: {self.game.editorial_headline(stance)}", font_size=dp(5.6), size_hint_y=None, height=dp(38)))
        side.add_widget(Widget())
        body.add_widget(side)
        self.card.add_widget(body)

        impact = d.get("media_impact", {})
        impact_row = GridLayout(cols=4, spacing=dp(4), size_hint_y=None, height=dp(52))
        impact_row.add_widget(ImpactBadge("Aprovacao", impact.get("approval", 0)))
        impact_row.add_widget(ImpactBadge("Mercado", impact.get("market", 0)))
        impact_row.add_widget(ImpactBadge("Risco crise", impact.get("crisis", 0), inverse=True))
        credibility_delta = d.get("last_credibility_impact", 0.0)
        impact_row.add_widget(ImpactBadge("Credibilidade", credibility_delta))
        self.card.add_widget(impact_row)

        if choices:
            row = GridLayout(cols=max(1, len(choices)), size_hint_y=None, height=dp(46), spacing=dp(4))
            for choice_title, changes in choices:
                b = SmallButton(text=choice_title)
                b.bind(on_release=lambda _btn, t=choice_title, ch=changes: self.game.resolve_event(t, ch))
                row.add_widget(b)
            self.card.add_widget(row)
        else:
            row = GridLayout(cols=2, size_hint_y=None, height=dp(34), spacing=dp(4))
            cont = SmallButton(text="CONTINUAR")
            cont.bind(on_release=lambda *_: self.game.close_news_overlay())
            press = SmallButton(text="CONVOCAR COLETIVA")
            press.bind(on_release=lambda *_: self.game.show_press_overlay())
            row.add_widget(cont)
            row.add_widget(press)
            self.card.add_widget(row)


class MediaMapRoot(MapFirstRoot):
    def __init__(self, game, **kwargs):
        super().__init__(game, **kwargs)

        old_drawer = self.drawer
        old_overlay = self.news_overlay
        self.remove_widget(old_drawer)
        self.remove_widget(old_overlay)

        self.drawer = MediaDrawer(game, size_hint=(1, 1))
        game.drawer = self.drawer
        self.add_widget(self.drawer)

        self.news_overlay = MediaNewsOverlay(game, size_hint=(1, 1))
        game.news_overlay = self.news_overlay
        self.add_widget(self.news_overlay)


class GameApp(V04GameApp):
    title = APP_NAME

    def build(self):
        Window.clearcolor = BG
        from v03_app import GameState

        self.state = GameState()
        self.state.load()
        ensure_media_state(self.state.d)
        self.playing = False
        self.overlay_open = False
        self.drawer = None
        self.news_overlay = None
        self._play_accumulator = 0.0
        self.root_view = MediaMapRoot(self)
        Clock.schedule_interval(self._tick, 0.25)
        Clock.schedule_interval(lambda _dt: self.root_view.refresh(), 0.8)
        self.root_view.refresh()
        return self.root_view

    def editorial_headline(self, stance):
        headline = self.state.d.get("headline", "Governo anuncia nova medida")
        if stance == "GOVERNISTA":
            return f"Governo destaca resposta: {headline.title()}"
        if stance == "CRITICO":
            return f"Pressao aumenta apos {headline.title()}"
        return headline.title()

    def classify_news(self, title):
        lower = title.lower()
        if any(k in lower for k in ("guerra", "ataque", "militar", "defesa", "fronteira")):
            return "Defesa"
        if any(k in lower for k in ("mercado", "imposto", "juros", "inflacao", "econom")):
            return "Economia"
        if any(k in lower for k in ("diplom", "negoci", "pais", "san", "tratado")):
            return "Diplomacia"
        if any(k in lower for k in ("protest", "greve", "sociedade")):
            return "Sociedade"
        return "Politica"

    def record_news(self, title, text, category=None, urgency=1):
        d = self.state.d
        ensure_media_state(d)
        category = category or self.classify_news(title)
        d["headline"] = str(title).upper()
        d["last_news"] = str(text)
        d["news_category"] = category
        d["news_urgency"] = int(urgency)
        d["media_attention"] = clamp(d["media_attention"] + urgency * 4 - 1)
        entry = {
            "category": category,
            "urgency": int(urgency),
            "headline": str(title),
            "text": str(text),
            "day": d.get("day", ""),
        }
        d["news_history"].insert(0, entry)
        d["news_history"] = d["news_history"][:40]
        d.setdefault("related_news", []).insert(0, {
            "category": category,
            "headline": str(title),
            "subtitle": str(text),
        })
        d["related_news"] = d["related_news"][:8]
        reactions = {
            "Economia": "Mercado e consumidores reagem aos novos dados.",
            "Diplomacia": "A decisao repercute entre governos estrangeiros.",
            "Defesa": "Analistas acompanham os efeitos para a seguranca nacional.",
            "Sociedade": "O tema domina as conversas nas redes sociais.",
            "Politica": "A decisao provoca reacao entre governo e oposicao.",
        }
        d["feed"].insert(0, ["AgoraBrasil", reactions.get(category, "A noticia gera forte repercussao."), random.randint(900, 14000)])
        d["feed"] = d["feed"][:10]
        self.state.save()

    def _credibility_from_choice(self, title):
        low = title.lower()
        if any(k in low for k in ("reconhecer", "investiga", "responsabilidade", "negociar")):
            return 1.2
        if any(k in low for k in ("criticar a cobertura", "ignorar", "negar")):
            return -1.5
        return 0.2

    def resolve_event(self, title, changes):
        d = self.state.d
        event = getattr(self.news_overlay, "event", None) or d.get("event") or {}
        event_title = event.get("title", title)
        event_text = event.get("text", "O governo tomou uma decisao diante de uma nova crise.")
        self.state.apply_choice(title, changes)
        credibility_delta = self._credibility_from_choice(title)
        d["press_credibility"] = clamp(d.get("press_credibility", 58) + credibility_delta)
        d["press_relation"] = clamp(d.get("press_relation", 50) + credibility_delta * 0.5)
        d["last_credibility_impact"] = credibility_delta
        category = self.classify_news(event_title)
        self.record_news(event_title, f"{event_text} Decisao do governo: {title}.", category, urgency=3)
        self.news_overlay.hide()
        self.overlay_open = False
        self.root_view.refresh()
        Clock.schedule_once(lambda *_: self.show_newsroom(), 0.12)

    def show_press_overlay(self):
        self.playing = False
        event = {
            "title": "Coletiva de imprensa",
            "text": "Jornalistas questionam o governo sobre economia, popularidade e estabilidade politica.",
            "choices": [
                ["Reconhecer o problema", {"approval": 1.0, "congress": 0.3}],
                ["Apresentar dados e medidas", {"approval": 0.7, "stability": 0.4}],
                ["Defender a estrategia", {"approval": 0.2, "stability": 0.2}],
                ["Criticar a cobertura", {"approval": -1.2, "stability": -0.5}],
            ],
        }
        self.state.d["event"] = event
        self.state.d["news_category"] = "Politica"
        self.state.d["news_urgency"] = 2
        self.show_event_overlay(event)

    def economic_action(self, key, amount, title):
        super().economic_action(key, amount, title)
        self.state.d["last_credibility_impact"] = 0.0
        self.record_news(title, "Nova decisao economica provoca reacao de mercado, consumidores e Congresso.", "Economia", urgency=1)
        self.root_view.refresh()

    def military_action(self, title, amount):
        super().military_action(title, amount)
        urgency = 2 if "exercicio" in title.lower() else 1
        self.state.d["last_credibility_impact"] = 0.0
        self.record_news(title, "A medida de defesa provoca repercussao politica e estrategica.", "Defesa", urgency=urgency)
        self.root_view.refresh()

    def negotiate(self, name):
        super().negotiate(name)
        self.state.d["last_credibility_impact"] = 0.2
        self.state.d["press_credibility"] = clamp(self.state.d.get("press_credibility", 58) + 0.2)
        self.record_news(
            f"Negociacao avanca com {name}",
            f"Representantes do Brasil e de {name} anunciam progresso nas conversas bilaterais.",
            "Diplomacia",
            urgency=1,
        )
        self.root_view.refresh()

    def advance(self, days, from_play=False):
        if self.overlay_open:
            return
        self.state.advance_day(days)
        self.root_view.refresh()
        event = self.state.d.get("event")
        if event:
            self.playing = False
            category = self.classify_news(event.get("title", ""))
            self.state.d["news_category"] = category
            self.state.d["news_urgency"] = 3
            self.record_news(event.get("title", "Plantao"), event.get("text", "Nova crise em desenvolvimento."), category, urgency=3)
            self.show_event_overlay(event)
        elif not from_play:
            self.root_view.refresh()
