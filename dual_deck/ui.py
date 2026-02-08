import dearpygui.dearpygui as dpg
from dual_deck.deck import DualDeck

# Instancia global del motor lógico
dual = DualDeck()

# -----------------------------
# Callbacks de los controles
# -----------------------------

def load_track_a():
    # Más adelante abriremos un file dialog
    dual.deck_a.load("track_a.mp3")
    print("Loaded A:", dual.deck_a.current_track)

def load_track_b():
    dual.deck_b.load("track_b.mp3")
    print("Loaded B:", dual.deck_b.current_track)

def play_a():
    dual.deck_a.play()
    print("Play A")

def play_b():
    dual.deck_b.play()
    print("Play B")

def stop_a():
    dual.deck_a.stop()
    print("Stop A")

def stop_b():
    dual.deck_b.stop()
    print("Stop B")

def crossfader_callback(sender, app_data):
    dual.set_crossfader(app_data)
    print("Crossfader:", app_data)

# -----------------------------
# Construcción de la UI
# -----------------------------

def start_ui():
    dpg.create_context()

    with dpg.window(label="Dual Deck", width=600, height=400):

        dpg.add_text("Deck A")
        dpg.add_button(label="Load A", callback=load_track_a)
        dpg.add_button(label="Play A", callback=play_a)
        dpg.add_button(label="Stop A", callback=stop_a)

        dpg.add_spacer(height=20)

        dpg.add_text("Deck B")
        dpg.add_button(label="Load B", callback=load_track_b)
        dpg.add_button(label="Play B", callback=play_b)
        dpg.add_button(label="Stop B", callback=stop_b)

        dpg.add_spacer(height=20)

        dpg.add_text("Crossfader")
        dpg.add_slider_float(
            label="",
            default_value=0.5,
            min_value=0.0,
            max_value=1.0,
            callback=crossfader_callback,
            width=300
        )

    dpg.create_viewport(title="Dual Deck", width=600, height=400)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
