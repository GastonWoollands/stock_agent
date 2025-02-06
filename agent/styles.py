import reflex as rx

SIDEBAR_STYLE = dict(
    width="300px",
    height="100vh",
    position="fixed",
    left=0,
    top=0,
    padding="2em",
    background_color=rx.color("blue", 2),
    border_right=f"1px solid {rx.color('blue', 3)}",
)

STOCK_BUTTON_STYLE = dict(
    color=rx.color("blue", 12),
    bg="transparent",
    border=f"1px solid {rx.color('blue', 6)}",
    _hover={"bg": rx.color("blue", 3)},
)

REMOVE_ICON_STYLE = {
    "color": "gray.400",
    "cursor": "pointer",
    "_hover": {"bg": rx.color("red", 3)},
    "font_size": "lg",
    "font_weight": "bold",
    "margin_right": "2",
}