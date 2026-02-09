import dearpygui.dearpygui as dpg
from dual_deck.deck import DualDeck

# Global instance of the logic engine
dual = DualDeck()
current_load_target = None   # "A" or "B"


# -----------------------------
# Control callbacks
# -----------------------------

def load_track_a():
    global current_load_target
    
    dual.deck_a.load("track_a.mp3")
    print("Loaded A:", dual.deck_a.current_track)
    
    current_load_target = "A"
    dpg.show_item("file_dialog_id")

def load_track_b():
    global current_load_target
    
    dual.deck_b.load("track_b.mp3")
    print("Loaded B:", dual.deck_b.current_track)
    
    current_load_target = "B"
    dpg.show_item("file_dialog_id")

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
    
def file_dialog_callback(sender, app_data):
    global current_load_target

    # app_data["file_path_name"] contains the complete path
    path = app_data["file_path_name"]

    if current_load_target == "A":
        dual.deck_a.load(path)
        print("Loaded A:", path)

    elif current_load_target == "B":
        dual.deck_b.load(path)
        print("Loaded B:", path)
        
    dpg.hide_item("file_dialog_id")

    current_load_target = None


# -----------------------------
# Building UI
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
        
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        callback=file_dialog_callback,
        tag="file_dialog_id",
        width=600,
        height=400
    ):
        dpg.add_file_extension(".*", color=(255, 255, 255, 255))
        dpg.add_file_extension(".mp3", color=(0, 255, 0, 255))
        dpg.add_file_extension(".wav", color=(0, 200, 255, 255))
        
        dpg.add_button(label="Cancel", callback=lambda: dpg.hide_item("file_dialog_id"))

    dpg.create_viewport(title="Dual Deck", width=600, height=400)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
