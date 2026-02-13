import dearpygui.dearpygui as dpg

from dual_deck.audio_engine import AudioEngine
from dual_deck.deck import DualDeck
from dual_deck.waveform import draw_local_waveform

dual = DualDeck(audio_engine_cls=AudioEngine)

current_load_target = None   # "A" or "B"
current_slider_value = 0.0
current_pitch_range = 0.08



def update_pitch_range_buttons(prefix, selected):
    dpg.bind_item_theme(f"btn_8_{prefix}",  "theme_button_default")
    dpg.bind_item_theme(f"btn_16_{prefix}", "theme_button_default")
    dpg.bind_item_theme(f"btn_50_{prefix}", "theme_button_default")

    if selected == 0.08:
        dpg.bind_item_theme(f"btn_8_{prefix}", "theme_button_active")
    elif selected == 0.16:
        dpg.bind_item_theme(f"btn_16_{prefix}", "theme_button_active")
    elif selected == 0.50:
        dpg.bind_item_theme(f"btn_50_{prefix}", "theme_button_active")

def update_pitch_display():
    pitch_percent = (dual.get_pitch() - 1.0) * 100

    dpg.set_value("pitch_label", f"{pitch_percent:+.1f}%")

    if hasattr(dual, "original_bpm"):
        bpm_actual = dual.original_bpm * dual._pitch
        dpg.set_value("bpm_label", f"{bpm_actual:.2f} BPM")

def on_pitch_slider(sender, app_data):
    global current_slider_value
    current_slider_value = float(app_data)

    dual.set_pitch_slider(current_slider_value)
    update_pitch_display()

def on_pitch_range(sender, app_data, user_data):
    global current_pitch_range
    current_pitch_range = user_data

    dual.set_pitch_range(user_data)
    dual.set_pitch_slider(current_slider_value)

    update_pitch_range_buttons(user_data)
    update_pitch_display()

def build_pitch_ui(prefix, deck):

    slider_tag = f"pitch_slider_{prefix}"
    pitch_tag  = f"pitch_label_{prefix}"
    bpm_tag    = f"bpm_label_{prefix}"

    def update_display():
        pitch_percent = (deck._pitch - 1.0) * 100
        dpg.set_value(pitch_tag, f"{pitch_percent:+.1f}%")

        if getattr(deck, "original_bpm", None) is not None:
            bpm = deck.original_bpm * deck._pitch
            dpg.set_value(bpm_tag, f"{bpm:.2f} BPM")
        else:
            dpg.set_value(bpm_tag, "— BPM")


    def on_slider(sender, app_data):
        deck.set_pitch_slider(float(app_data))
        update_display()

    def on_range(sender, app_data, user_data):
        deck.set_pitch_range(user_data)

        # Reapply the current slider value
        slider_value = dpg.get_value(f"pitch_slider_{prefix}")
        deck.set_pitch_slider(slider_value)

        update_pitch_range_buttons(prefix, user_data)
        update_display()


    with dpg.group(horizontal=True):
    
        # Pitch
        dpg.add_slider_float(
            tag=slider_tag,
            #label="Pitch",
            default_value=0.0,
            min_value=-1.0,
            max_value=1.0,
            width=40,
            height=200,
            vertical=True,
            callback=on_slider
        )

        with dpg.group():
            dpg.add_spacer(height=10)

            dpg.add_button(label="±8%",  tag=f"btn_8_{prefix}",  width=60, callback=on_range, user_data=0.08)
            dpg.add_button(label="±16%", tag=f"btn_16_{prefix}", width=60, callback=on_range, user_data=0.16)
            dpg.add_button(label="±50%", tag=f"btn_50_{prefix}", width=60, callback=on_range, user_data=0.50)

            #dpg.add_spacer(height=10)
            dpg.add_text("Pitch:")
            dpg.add_text("+0.0%", tag=pitch_tag) 

            dpg.add_text("BPM:")
            dpg.add_text("0.00 BPM", tag=bpm_tag)
            
            dpg.add_button(label="CUE", width=60, callback=lambda: deck.set_cue())
            dpg.add_button(label="Play CUE", width=60, callback=lambda: deck.cue_play())
            dpg.add_button(label="SYNC", width=60, callback=lambda: deck.sync_to(dual.deck_b if prefix=="A" else dual.deck_a))
            dpg.add_spacer(width=20)
                        

    update_pitch_range_buttons(prefix, 0.08)

def load_track_a():
    global current_load_target
    current_load_target = "A"
    dpg.show_item("file_dialog_id")


def load_track_b():
    global current_load_target
    current_load_target = "B"
    dpg.show_item("file_dialog_id")

def play_a():
    dual.deck_a.play()
    
def play_b():
    dual.deck_b.play()
    
def pause_a():
    dual.deck_a.pause()

def pause_b():
    dual.deck_b.pause()

def stop_a():
    dual.deck_a.stop()

def stop_b():
    dual.deck_b.stop()

def crossfader_callback(sender, app_data):
    dual.set_crossfader(app_data)
    
def file_dialog_callback(sender, app_data):
    global current_load_target

    path = app_data["file_path_name"]

    if current_load_target == "A":
        dual.deck_a.load(path)
        draw_waveform(dual.deck_a.waveform, "global_wave_A")
        draw_local_waveform(dual.deck_a.waveform, 0, 300, "local_wave_A")

    elif current_load_target == "B":
        dual.deck_b.load(path)
        draw_waveform(dual.deck_b.waveform, "global_wave_B")
        draw_local_waveform(dual.deck_b.waveform, 0, 300, "local_wave_B")

    # RESET TIMER TO PICK UP THE NEW WAVEFORM
    dpg.set_frame_callback(dpg.get_frame_count() + 1, update_local_waves)

    dpg.hide_item("file_dialog_id")
    current_load_target = None


def draw_waveform(waveform, tag, width=1200, height=120):
    # Delete what was before
    dpg.delete_item(tag, children_only=True)

    mid = height // 2
    step = width / len(waveform)

    for i in range(len(waveform) - 1):
        x1 = i * step
        y1 = mid - waveform[i] * mid
        x2 = (i + 1) * step
        y2 = mid - waveform[i + 1] * mid

        dpg.draw_line((x1, y1), (x2, y2),
                      color=(0, 200, 255),
                      thickness=1,
                      parent=tag)
def update_local_waves():
    # Deck A
    if dual.deck_a.waveform is not None:
        draw_local_waveform(
            dual.deck_a.waveform,
            dual.deck_a.position,
            window_size=300,
            tag="local_wave_A"
        )

    # Deck B
    if dual.deck_b.waveform is not None:
        draw_local_waveform(
            dual.deck_b.waveform,
            dual.deck_b.position,
            window_size=300,
            tag="local_wave_B"
        )

    #  Repete
    dpg.set_frame_callback(dpg.get_frame_count() + 2, update_local_waves)
    
    draw_vu("vu_A", dual.deck_a._audio_engine._vu)
    draw_vu("vu_B", dual.deck_b._audio_engine._vu)

def draw_vu(tag, level, width=20, height=120):
    dpg.delete_item(tag, children_only=True)

    # altura de la barra
    bar_h = int(level * height)

    # color estilo DJ (verde → amarillo → rojo)
    if level < 0.6:
        color = (0, 255, 0)
    elif level < 0.85:
        color = (255, 255, 0)
    else:
        color = (255, 0, 0)

    dpg.draw_rectangle((0, height - bar_h), (width, height),
                       fill=color, parent=tag)


    
# -----------------------------
# Building UI
# -----------------------------

def start_ui():
    dpg.create_context()
    
    # -----------------------------
    # THEMES
    # -----------------------------
    with dpg.theme(tag="theme_button_default"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 60))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 80))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 100))

    with dpg.theme(tag="theme_button_active"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 120, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (30, 150, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 90, 200))
    
    # -----------------------------
    # FONT
    # -----------------------------
    with dpg.font_registry():
        main_font = dpg.add_font("fonts/DejaVuSans.ttf", 14)

    dpg.bind_font(main_font)
     
    # -----------------------------
    # MAIN WINDOW
    # -----------------------------
    with dpg.window(label="Dual Deck", width=1300, height=800):
        dpg.add_spacer(height=20)
        
        # -----------------------------
        # GLOBAL WAVEFORMS
        # -----------------------------
        dpg.add_text("Deck A Waveform")
        with dpg.drawlist(width=1200, height=120, tag="global_wave_A"):
            pass

        dpg.add_text("Deck B Waveform")
        with dpg.drawlist(width=1200, height=120, tag="global_wave_B"):
            pass
        
        dpg.add_spacer(height=10)

        # -----------------------------
        # LOCAL WAVES
        # -----------------------------
        dpg.add_text("Deck A (Local Wave)")
        with dpg.drawlist(width=600, height=120, tag="local_wave_A"):
            pass

        dpg.add_text("Deck B (Local Wave)")
        with dpg.drawlist(width=600, height=120, tag="local_wave_B"):
            pass

        dpg.add_spacer(height=20)

        # -----------------------------
        # DECK CONTROLS (A y B)
        # -----------------------------
        with dpg.group(horizontal=True):

            # -----------------------------
            # DECK A
            # -----------------------------
            with dpg.group():
                dpg.add_button(label="Load A", callback=load_track_a)
                dpg.add_button(label="play", callback=play_a)
                dpg.add_button(label="pause", callback=pause_a)
                dpg.add_button(label="stop", callback=stop_a)
                dpg.add_text("0.00 BPM", tag="A_bpm_label")

                build_pitch_ui("A", dual.deck_a)

                dpg.add_slider_float(
                    label="",
                    default_value=1.0,
                    min_value=0.0,
                    max_value=1.0,
                    height=200,
                    vertical=True,
                    callback=lambda s, a: dual.deck_a.set_volume(a)
                )

            dpg.add_spacer(width=20)

            # -----------------------------
            # CROSSFADER
            # -----------------------------
            dpg.add_slider_float(
                label="",
                default_value=0.5,
                min_value=0.0,
                max_value=1.0,
                width=200,
                callback=crossfader_callback
            )

            dpg.add_spacer(width=20)
            
            dpg.add_drawlist(tag="vu_A", width=20, height=120)
            dpg.add_drawlist(tag="vu_B", width=20, height=120)



            # -----------------------------
            # DECK B
            # -----------------------------
            with dpg.group():
                dpg.add_button(label="Load B", callback=load_track_b)
                dpg.add_button(label="play", callback=play_b)
                dpg.add_button(label="pause", callback=pause_b)
                dpg.add_button(label="stop", callback=stop_b)
                dpg.add_text("0.00 BPM", tag="B_bpm_label")

                build_pitch_ui("B", dual.deck_b)

                dpg.add_slider_float(
                    label="",
                    default_value=1.0,
                    min_value=0.0,
                    max_value=1.0,
                    height=200,
                    vertical=True,
                    callback=lambda s, a: dual.deck_b.set_volume(a)
                )

        dpg.add_spacer(height=20)

    # -----------------------------
    # FILE DIALOG
    # -----------------------------
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        callback=file_dialog_callback,
        tag="file_dialog_id",
        width=600,
        height=400
    ):
        dpg.add_file_extension(".mp3", color=(0, 255, 0, 255))
        dpg.add_file_extension(".wav", color=(0, 200, 255, 255))
        dpg.add_button(label="Cancel", callback=lambda: dpg.hide_item("file_dialog_id"))

    # -----------------------------
    # START LOCAL WAVE UPDATES
    # -----------------------------
    update_local_waves()

    # -----------------------------
    # START DPG
    # -----------------------------
    dpg.create_viewport(title="Dual Deck", width=1300, height=800)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
