import reflex as rx
from typing import List, Optional
from dataclasses import dataclass
import time
import asyncio
from textwrap import dedent

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.yfinance import YFinanceTools

from agent.styles import SIDEBAR_STYLE, STOCK_BUTTON_STYLE, REMOVE_ICON_STYLE

# Data Models
@dataclass
class QA:
    """A question and answer pair."""
    question: str
    answer: str

# Custom Loading Icon
class LoadingIcon(rx.Component):
    """A custom loading icon component."""
    library = "react-loading-icons"
    tag = "SpinningCircles"
    stroke: rx.Var[str]
    stroke_opacity: rx.Var[str]
    fill: rx.Var[str]
    fill_opacity: rx.Var[str]
    stroke_width: rx.Var[str]
    speed: rx.Var[str]
    height: rx.Var[str]

    def get_event_triggers(self) -> dict:
        return {"on_change": lambda status: [status]}

loading_icon = LoadingIcon.create

# Styles
message_style = dict(
    display="inline-block", 
    padding="1em", 
    border_radius="8px",
    max_width=["30em", "30em", "50em", "50em", "50em", "50em"]
)

# Application State
class State(rx.State):
    """The app state."""
    chats: List[List[QA]] = [[]]
    current_chat: int = 0
    processing: bool = False
    watchlist: List[str] = ["AAPL", "MSFT", "GOOGL", "BTC-USD", "ETH-USD"]

    def _create_agent(self) -> Agent:
        """Create a fresh agent instance for each interaction"""
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp"),
            tools=[
                YFinanceTools(
                    stock_price=True,
                    analyst_recommendations=True,
                    stock_fundamentals=True,
                    historical_prices=True,
                    company_info=True,
                    company_news=True,
                )
            ],
            instructions=dedent("""\
                You are a seasoned Wall Street analyst with deep expertise in market analysis! 📊

                Follow these steps for comprehensive financial analysis:
                1. Market Overview
                   - Latest stock price
                   - 52-week high and low
                2. Financial Deep Dive
                   - Key metrics (P/E, Market Cap, EPS)
                3. Professional Insights
                   - Analyst recommendations breakdown
                   - Recent rating changes
                4. Market Context
                   - Industry trends and positioning
                   - Competitive analysis
                   - Market sentiment indicators

                Your reporting style:
                - Begin with an executive summary
                - Strictly use tables for numerical data presentation
                - Include clear section headers
                - Add emoji indicators for trends (📈 📉)
                - Highlight key insights with bullet points
                - Compare metrics to industry averages
                - Include technical term explanations
                - End with a forward-looking analysis

                Risk Disclosure:
                - Always highlight potential risk factors
                - Note market uncertainties
                - Mention relevant regulatory concerns
            """),
            add_datetime_to_instructions=True,
            show_tool_calls=False, # TO REMOVE  
            markdown=True,
        )

    @rx.event(background=True)
    async def process_question(self, form_data: dict):
        """Process a financial analysis question"""
        if self.processing or not form_data.get("question"):
            return

        question = form_data["question"]
        
        async with self:
            self.processing = True
            self.chats[self.current_chat].append(QA(question=question, answer=""))
            yield

        try:
            agent = self._create_agent()
            response = agent.run(question, stream=True) 

            async with self:
                answer_content = ""
                for chunk in response:  # Process each chunk of the response
                    if hasattr(chunk, "content"):  # Check if the chunk has a `content` attribute
                        answer_content += chunk.content
                    else:
                        answer_content += str(chunk)

                    # Update the UI with the latest chunk
                    self.chats[self.current_chat][-1].answer = answer_content
                    self.chats = self.chats
                    yield
                    await asyncio.sleep(0.05)

        except Exception as e:
            answer_content = f"Error processing question: {str(e)}"

        async with self:
            self.chats[self.current_chat][-1].answer = answer_content
            self.chats = self.chats
            self.processing = False
            yield

    def add_to_watchlist(self, form_data: dict[str, str]):
        """Add a stock to the watchlist"""
        symbol = form_data.get("symbol", "").upper()
        if symbol and symbol not in self.watchlist:
            self.watchlist.append(symbol.upper())

    def remove_from_watchlist(self, symbol: str):
        """Remove a stock from the watchlist"""
        if symbol in self.watchlist:
            self.watchlist.remove(symbol)
    
    def create_new_chat(self):
        """Create a new chat"""
        self.chats.append([])
        self.current_chat = len(self.chats) - 1

#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
# UI Components
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------

def message(qa: QA) -> rx.Component:
    return rx.box(
        rx.box(
            rx.markdown(
                qa.question,
                background_color=rx.color("blue", 4),
                color=rx.color("blue", 12),
                **message_style,
            ),
            text_align="right",
            margin_top="1em",
        ),
        rx.box(
            rx.markdown(
                qa.answer,
                background_color=rx.color("green", 4),
                color=rx.color("green", 12),
                **message_style,
            ),
            text_align="left",
            padding_top="1em",
        ),
        width="100%",
    )

def chat() -> rx.Component:
    """Chat siempre visible con la barra de entrada integrada."""
    return rx.vstack(
        rx.box(
            rx.foreach(State.chats[State.current_chat], message),
            width="100%",
            overflow_y="auto",
            padding_bottom="2em",
            flex="1",
        ),
        rx.form(
            rx.hstack(
                rx.input(
                    placeholder="Ask about any stock...",
                    id="question",
                    width="100%",
                    disabled=State.processing,
                    border_color=rx.color("blue", 6),
                    _focus={"border_color": rx.color("blue", 8)},
                    background_color="transparent",
                    padding="0.5em",
                    border_radius="4px",
                ),
                rx.button(
                    rx.cond(
                        State.processing,
                        loading_icon(height="1em"),
                        rx.text("Send"),
                    ),
                    type_="submit",
                    disabled=State.processing,
                    bg=rx.color("green", 9),
                    color="white",
                    _hover={"bg": rx.color("green", 10)},
                    border_radius="4px",
                    padding="0.5em 1em",
                ),
                align_items="center",
                spacing="1",
            ),
            on_submit=State.process_question,
            width="100%",
            reset_on_submit=True,
        ),
        spacing="3",
        align_items="center",
        width="100%",
        max_width="50em",
        max_height="60vh",
        overflow_y="auto",
        padding_x="4px",
        py="8",
        flex="1",
    )

def action_bar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Ask about any stock...",
                        id="question",
                        width=["15em", "20em", "45em", "50em", "50em", "50em"],
                        disabled=State.processing,
                        border_color=rx.color("blue", 6),
                        _focus={"border_color": rx.color("blue", 8)},
                        background_color="transparent",
                        padding="0.5em",
                        border_radius="4px"
                    ),
                    rx.button(
                        rx.cond(
                            State.processing,
                            loading_icon(height="1em"),
                            rx.text("Analyze"),
                        ),
                        type_="submit",
                        disabled=State.processing,
                        bg=rx.color("green", 9),
                        color="white",
                        _hover={"bg": rx.color("green", 10)},
                        border_radius="4px",
                        padding="0.5em 1em",
                    ),
                    align_items="center",
                    spacing="1",
                ),
                on_submit=State.process_question,
                width="100%",
                reset_on_submit=True,
            ),
            align_items="center",
            width="100%",
        ),
        position="fixed",
        bottom="0",
        left="0",
        padding_x="350px",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        background_color=rx.color("mauve", 2),
        border_top=f"1px solid {rx.color('blue', 3)}",
        width="100%",
    )

def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                "Your Personal Market Analyst",
                color=rx.color("blue", 11),
                font_size="sm",
                margin_bottom="2em",
            ),
            rx.heading("Watchlist", size="4", margin_bottom="1em"),
            rx.foreach(
                State.watchlist,
                lambda symbol: rx.hstack(
                     rx.text(
                        "×",  # Using × symbol as remove icon
                        on_click=lambda: State.remove_from_watchlist(symbol),
                        **REMOVE_ICON_STYLE,
                    ),
                    rx.text(symbol, font_size="sm"),
                    rx.button(
                        "Analyze",
                        on_click=lambda: State.process_question({"question": f"Analyze {symbol}'s performance"}),
                        size="2",
                        **STOCK_BUTTON_STYLE,
                    ),
                    width="100%",
                    justify_content="space-between",
                ),
            ),
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Add new stock...",
                        id="symbol",
                        size="2",
                    ),
                    rx.button(
                        "Add",
                        type_="submit",
                        size="2",
                        **STOCK_BUTTON_STYLE,
                    ),
                ),
                on_submit=State.add_to_watchlist(),
                width="100%",
                margin_top="2em",
            ),
            align_items="stretch",
            height="100%",
        ),
        **SIDEBAR_STYLE,
    )

def index() -> rx.Component:
    """Página principal con el chat siempre abierto."""
    return rx.box(
        sidebar(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("AI Finance Agent", size="6"),
                    rx.button(
                        "New Chat",
                        on_click=State.create_new_chat,
                        margin_left="auto",
                    ),
                    rx.hstack(
                        rx.color_mode.icon(),
                        rx.color_mode.switch(),
                        spacing="4",
                        padding_top="4"
                    ),
                    width="75%",
                    align='center'
                ),
                rx.spacer(),
                chat(),
                spacing="4",
                align_items="center",
            ),
            margin_left="300px",
            width="calc(100% - 300px)",
            height="100vh",
            padding="4em",
        ),
        width="100%",
        height="100vh",
        background_color=rx.color("mauve", 1),
    )

app = rx.App()
app.add_page(index)