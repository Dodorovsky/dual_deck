import dearpygui.dearpygui as dpg
from pathlib import Path
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
    #  = f"pitch_label_{prefix}"
    bpm_tag    = f"bpm_label_{prefix}"

    def update_display():
        if not dpg.does_item_exist(bpm_tag):
            return  # el label aún no existe, evitar error


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

    with dpg.group():
        sync=dpg.add_button(label="SYNC", width=40, callback=lambda: deck.sync_to(dual.deck_b if prefix=="A" else dual.deck_a))
        dpg.bind_item_theme(sync,  "theme_sync_default")
        with dpg.group(horizontal=True):
            # Pitch
            dpg.add_slider_float(
                tag=slider_tag,
                #label="Pitch",
                default_value=0.0,
                min_value=-1.0,
                max_value=1.0,
                width=40,
                height=120,
                vertical=True,
                callback=on_slider
            )

            with dpg.group():
                

                dpg.add_button(label="±8%",  tag=f"btn_8_{prefix}",  width=60, callback=on_range, user_data=0.08)
                dpg.add_button(label="±16%", tag=f"btn_16_{prefix}", width=60, callback=on_range, user_data=0.16)
                dpg.add_button(label="±50%", tag=f"btn_50_{prefix}", width=60, callback=on_range, user_data=0.50)

            
                
                #dpg.add_spacer(height=10)
                #dpg.add_text("Pitch:")
                #dpg.add_text("+0.0%", tag=pitch_tag) 

                #dpg.add_text("BPM:")
                #dpg.add_text("0.00 BPM", tag=bpm_tag)
                dpg.add_spacer(height=1)
                dpg.add_button(label="CUE", width=60, callback=lambda: deck.set_cue())
                dpg.add_button(label="Play CUE", width=60, callback=lambda: deck.cue_play())
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
    print("[UI] play_a() called")
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
    dpg.set_value("cross_value", f"{app_data:.2f}")
    
def file_dialog_callback(sender, app_data):
    global current_load_target

    path = app_data["file_path_name"]
    track_name = Path(path).stem   # ← WITHOUT EXTENSION

    if current_load_target == "A":
        dual.deck_a.load(path)
        dpg.set_value("deck_a_title", track_name)
        draw_waveform(dual.deck_a.waveform, "global_wave_A")
        draw_local_waveform(dual.deck_a.waveform, 0, 300, "local_wave_A")

    elif current_load_target == "B":
        dual.deck_b.load(path)
        dpg.set_value("deck_b_title", track_name)
        draw_waveform(dual.deck_b.waveform, "global_wave_B")
        draw_local_waveform(dual.deck_b.waveform, 0, 300, "local_wave_B")

    dpg.set_frame_callback(dpg.get_frame_count() + 1, update_local_waves)
    dpg.hide_item("file_dialog_id")
    current_load_target = None

def draw_waveform(waveform, tag, width=1120, height=60):
    # Delete what was before
    dpg.delete_item(tag, children_only=True)
    dpg.draw_rectangle(
    (0, 0),
    (width, height),
    fill=(0, 0, 0),
    color=(40, 40, 40),   # borde gris oscuro
    thickness=1,
    parent=tag
)


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
        
def get_master_level(deck_a, deck_b):
    return min(1.0, deck_a._vu + deck_b._vu)
def update_local_waves():
    # -------------------------
    # ONDAS LOCALES
    # -------------------------
    if dual.deck_a.waveform is not None:
        draw_local_waveform(
            dual.deck_a.waveform,
            dual.deck_a.position,
            window_size=300,
            tag="local_wave_A"
        )

    if dual.deck_b.waveform is not None:
        draw_local_waveform(
            dual.deck_b.waveform,
            dual.deck_b.position,
            window_size=300,
            tag="local_wave_B"
        )

    # -------------------------
    # VÚMETROS A y B
    # -------------------------
    vuA = dual.deck_a._audio_engine._vu
    vuB = dual.deck_b._audio_engine._vu

    draw_vu("vu_A", vuA)
    draw_vu("vu_B", vuB)

    # -------------------------
    # VÚMETRO MASTER ESTÉREO
    # (simulación: A = canal L, B = canal R)
    # -------------------------
    


    vuA = dual.deck_a._audio_engine._vu
    vuB = dual.deck_b._audio_engine._vu

    master = min(1.0, vuA + vuB)

    draw_vu_stereo("vu_master", master, master)






    # -------------------------
    # REPROGRAMAR TIMER
    # -------------------------
    dpg.set_frame_callback(dpg.get_frame_count() + 2, update_local_waves)

def draw_vu(parent, level, segments=24):
    dpg.delete_item(parent, children_only=True)

    width = 22
    height = 120
    seg_height = height / segments

    for i in range(segments):
        y1 = height - (i + 1) * seg_height
        y2 = height - i * seg_height

        # nivel actual en segmentos
        active_segments = int(level * segments)

        # color según zona
        if i < segments * 0.6:
            color = (0, 200, 0)      # verde
        elif i < segments * 0.85:
            color = (255, 200, 0)    # amarillo
        else:
            color = (255, 0, 0)      # rojo

        fill = color if i < active_segments else (40, 40, 40)

        dpg.draw_rectangle(
            (0, y1),
            (width, y2),
            fill=fill,
            color=(0, 0, 0),
            parent=parent
        )
   
def draw_vu_stereo(tag, left_level, right_level, width=40, height=120, segments=24):
    dpg.delete_item(tag, children_only=True)

    bar_width = width // 2
    seg_height = height / segments

    # LEFT BAR (Deck A)
    active_left = int(left_level * segments)

    for i in range(segments):
        y1 = height - (i + 1) * seg_height
        y2 = height - i * seg_height

        if i < active_left:
            color = (0,255,0) if i < segments * 0.6 else (255,255,0) if i < segments * 0.85 else (255,0,0)
        else:
            color = (40,40,40)

        dpg.draw_rectangle(
            (0, y1),
            (bar_width, y2),
            fill=color,
            color=(0,0,0),
            parent=tag
        )

    # RIGHT BAR (Deck B)
    active_right = int(right_level * segments)

    for i in range(segments):
        y1 = height - (i + 1) * seg_height
        y2 = height - i * seg_height

        if i < active_right:
            color = (0,255,0) if i < segments * 0.6 else (255,255,0) if i < segments * 0.85 else (255,0,0)
        else:
            color = (40,40,40)

        dpg.draw_rectangle(
            (bar_width, y1),
            (width, y2),
            fill=color,
            color=(0,0,0),
            parent=tag
        )
 
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
            
    with dpg.theme(tag="theme_sync_default"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (69, 55, 32))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 80))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 100))
            
    with dpg.theme(tag="theme_controls_default"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (69, 55, 32))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 80))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 100))
            
    with dpg.theme() as fader_theme:
        with dpg.theme_component(dpg.mvSliderFloat):
            
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 240, 8))
            
            # Fondo del track
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (20, 20, 20))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (20, 20, 20))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (20, 20, 20))

            # Color del fader (grab)
            
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (200, 200, 200))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (255, 255, 255))

            # Borde fino
            dpg.add_theme_color(dpg.mvThemeCol_Border, (80, 80, 80))
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)

            # Padding para hacerlo más fino
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 2, 2)
            
    with dpg.theme() as pioneer_fader:
        with dpg.theme_component(dpg.mvSliderFloat):
            # Track background
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (20, 20, 20))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (30, 30, 30))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (40, 40, 40))

            # Fader cap (the “button”)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (200, 200, 200))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (255, 255, 255))

            # Pioneer style fine border
            dpg.add_theme_color(dpg.mvThemeCol_Border, (80, 80, 80))
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)

            # Padding to make it finer
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 2, 2)

    # -----------------------------
    # FONT
    # -----------------------------
    with dpg.font_registry():
        main_font = dpg.add_font("fonts/DejaVuSans.ttf", 14)

    dpg.bind_font(main_font)
     
    # -----------------------------
    # MAIN WINDOW
    # -----------------------------
    with dpg.window(label="Dual Deck", width=1150, height=500):
        dpg.add_spacer(height=20)
        
        # -----------------------------
        # GLOBAL WAVEFORMS
        # -----------------------------
        #dpg.add_text("Deck A Waveform")
        with dpg.drawlist( width=1120, height=60, tag="global_wave_A"):
            dpg.draw_rectangle((0, 0), (1120, 60), fill=(0, 0, 0), color=(0,0,0))
            pass

        #dpg.add_text("Deck B Waveform")
        with dpg.drawlist(width=1120, height=60, tag="global_wave_B"):
            dpg.draw_rectangle((0, 0), (1120, 60), fill=(0, 0, 0), color=(0,0,0))
            pass
        
        
        dpg.add_spacer(height=20)
        # -----------------------------
        # LOCAL WAVES
        # -----------------------------
        with dpg.group(horizontal=True):
            
            with dpg.group():
                dpg.add_spacer(height=30)
                dpg.add_text("No track", tag="deck_a_title") 
            # --- Onda local A ---
                with dpg.drawlist(width=300, height=60, tag="local_wave_A"):
                    dpg.draw_rectangle((0, 0), (300, 60), fill=(0, 0, 0), color=(0,0,0))
                    pass

            #dpg.add_spacer(width=10)

            # --- Pitch A ---
            build_pitch_ui("A", dual.deck_a)

            dpg.add_spacer(width=20)

            # ============================================
            # MIXER BLOCK PASTED BELOW
            # ============================================

            # Volume A (glued below)
            with dpg.group():
                
                dpg.add_spacer(height=20)  
                dpg.add_slider_float(
                    tag="vol_A",
                    label="",
                    default_value=1.0,
                    min_value=0.0,
                    max_value=1.0,
                    height=120,
                    vertical=True,
                    format="",
                    callback=lambda s, a: dual.deck_a.set_volume(a)
                )
            dpg.bind_item_theme("vol_A", pioneer_fader)

            dpg.add_spacer(width=15)

            # VU A / MASTER / VU B (glued below)
            with dpg.group():
                dpg.add_spacer(height=20)
                with dpg.group(horizontal=True):
                    dpg.add_drawlist(tag="vu_A", width=20, height=120)
                    dpg.add_drawlist(tag="vu_master", width=40, height=120)
                    dpg.add_drawlist(tag="vu_B", width=20, height=120)

            dpg.add_spacer(width=15)

            # Volume B (glued below)
            with dpg.group():
                dpg.add_spacer(height=20)
                dpg.add_slider_float(
                    tag="vol_B",
                    label="",
                    default_value=1.0,
                    min_value=0.0,
                    max_value=1.0,
                    height=120,
                    vertical=True,
                    format="",
                    callback=lambda s, a: dual.deck_b.set_volume(a)
                )
                dpg.bind_item_theme("vol_B", pioneer_fader)

            dpg.add_spacer(width=20)
            with dpg.group():
                dpg.add_spacer(height=30)
                dpg.add_text("No track", tag="deck_b_title")
                with dpg.drawlist(width=300, height=60, tag="local_wave_B"):
                    dpg.draw_rectangle((0, 0), (300, 60), fill=(0, 0, 0), color=(0,0,0))
                    pass
            build_pitch_ui("B", dual.deck_b)

        # -----------------------------
        # DECK CONTROLS (A y B)
        # -----------------------------
        with dpg.group(horizontal=True):

            # -----------------------------
            # DECK A
            # -----------------------------
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=50)
                load_a = dpg.add_button(label="Load A", callback=load_track_a)
                dpg.bind_item_theme(load_a,  "theme_controls_default")
                play_aa = dpg.add_button(label="play", callback=play_a)
                dpg.bind_item_theme(play_aa,  "theme_controls_default")
                pause_aa = dpg.add_button(label="pause", callback=pause_a)
                dpg.bind_item_theme(pause_aa,  "theme_controls_default")
                stop_aa = dpg.add_button(label="stop", callback=stop_a)
                dpg.bind_item_theme(stop_aa,  "theme_controls_default")
                dpg.add_spacer(width=40)
                dpg.add_text("  0.00 BPM  ", tag="A_bpm_label")
                
            dpg.add_spacer(width=73)

            # -----------------------------
            # CROSSFADER
            # -----------------------------
            dpg.add_slider_float(
                tag="crossfader",
                label="",
                default_value=0.5,
                min_value=0.0,
                max_value=1.0,
                width=198,
                format="",
                callback=crossfader_callback,
                
            )
            dpg.bind_item_theme("crossfader", fader_theme)

            dpg.add_spacer(width=70)

            # -----------------------------
            # DECK B
            # -----------------------------
            with dpg.group(horizontal=True):
                load_bb = dpg.add_button(label="Load B", callback=load_track_b)
                dpg.bind_item_theme(load_bb,  "theme_controls_default")
                play_bb = dpg.add_button(label="play", callback=play_b)
                dpg.bind_item_theme(play_bb,  "theme_controls_default")
                pause_bb = dpg.add_button(label="pause", callback=pause_b)
                dpg.bind_item_theme(pause_bb,  "theme_controls_default")
                stop_bb = dpg.add_button(label="stop", callback=stop_b)
                dpg.bind_item_theme(stop_bb,  "theme_controls_default")
                dpg.add_spacer(width=50)
                dpg.add_text("0.00 BPM", tag="B_bpm_label")

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=530)
            dpg.add_text("0.50", tag="cross_value")

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
    dpg.create_viewport(title="Dual Deck", width=1150, height=500)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
