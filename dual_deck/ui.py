import dearpygui.dearpygui as dpg
from pathlib import Path
from dual_deck.audio_engine import AudioEngine
from dual_deck.deck import DualDeck
from dual_deck.waveform import draw_local_waveform
from dual_deck.library import get_all_tracks, delete_track_from_library


dual = DualDeck(audio_engine_cls=AudioEngine)

current_load_target = None   # "A" or "B"
current_slider_value = 0.0
current_pitch_range = 0.08
loop_enabled = True



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
    dual.deck_a.play()
    update_local_waves()  # kick in case the loop died earlier
    
def play_b():
    dual.deck_b.play()
    update_local_waves()  # kick in case the loop died earlier
    
def pause_a():
    dual.deck_a.pause()

def pause_b():
    dual.deck_b.pause()

def crossfader_callback(sender, app_data):
    dual.set_crossfader(app_data)
    dpg.set_value("cross_value", f"{app_data:.2f}")
    
def refresh_library_ui():
    global library_tracks

    tracks = get_all_tracks()
    library_tracks = tracks

    names = [t[2] for t in tracks]  # show titles


    dpg.configure_item("library_list", items=names)

    if names:
        dpg.set_value("library_list", names[0])

    dpg.set_value("library_list", names)
    
def file_dialog_callback(sender, app_data):
    global loop_enabled, current_load_target
    loop_enabled = False
    try:
        path = app_data["file_path_name"]
        track_name = Path(path).stem

        if current_load_target == "A":
            dual.deck_a.safe_load(path)
            draw_global_static(dual.deck_a, "global_wave_A")
            refresh_hotcue_markers(dual.deck_a, "global_wave_A")
            dpg.set_value("deck_a_title", track_name)

        elif current_load_target == "B":
            dual.deck_b.safe_load(path)
            draw_global_static(dual.deck_b, "global_wave_B")
            refresh_hotcue_markers(dual.deck_b, "global_wave_B")
            dpg.set_value("deck_b_title", track_name)

        refresh_library_ui()
        dpg.hide_item("file_dialog_id")
        current_load_target = None

    finally:
        loop_enabled = True

def draw_waveform(waveform, tag, width=1120, height=60):
    # Delete what was before
    dpg.delete_item(tag, children_only=True)
    dpg.draw_rectangle(
    (0, 0),
    (width, height),
    fill=(0, 0, 0),
    color=(40, 40, 40),   # dark gray border
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

def draw_global_static(deck, tag, width=1120, height=60):
    dpg.delete_item(tag, children_only=True)

    wf = deck.waveform
    if wf is None or wf.size == 0:
        return

    dpg.draw_rectangle(
        (0, 0),
        (width, height),
        fill=(0, 0, 0),
        color=(40, 40, 40),
        thickness=1,
        parent=tag
    )

    mid = height // 2
    step = width / len(wf)

    for i in range(len(wf) - 1):
        x1 = i * step
        y1 = mid - wf[i] * mid
        x2 = (i + 1) * step
        y2 = mid - wf[i + 1] * mid

        dpg.draw_line(
            (x1, y1),
            (x2, y2),
            color=(0, 200, 255),
            thickness=1,
            parent=tag
        )

    # overlays placeholders
    dpg.draw_line((0, 0), (0, height),
                  color=(255, 0, 0),
                  thickness=2,
                  parent=tag,
                  tag=f"{tag}_playhead")

    dpg.draw_line((0, 0), (0, height),
                  color=(0, 200, 255),
                  thickness=2,
                  parent=tag,
                  tag=f"{tag}_cue")
    
    # contenedor para hotcues (solo se crea una vez)
    if not dpg.does_item_exist(f"{tag}_hotcues"):
        dpg.add_draw_node(tag=f"{tag}_hotcues", parent=tag)
        
    if not dpg.does_item_exist(f"{tag}_loop"):
        dpg.add_draw_node(tag=f"{tag}_loop", parent=tag)
    
def update_global_overlays(deck, tag, width=1120, height=60):
    wf = deck.waveform
    if wf is None or wf.size == 0:
        return

    play_tag = f"{tag}_playhead"
    cue_tag  = f"{tag}_cue"

    # si los overlays no existen aún, crea la global estática una vez
    if not dpg.does_item_exist(play_tag) or not dpg.does_item_exist(cue_tag):
        draw_global_static(deck, tag, width, height)

    # playhead
    x = (deck.position / len(wf)) * width
    dpg.configure_item(play_tag, p1=(x, 0), p2=(x, height))

    # cue
    if deck.cue_position is not None:
        cue_x = (deck.cue_position / len(wf)) * width
        dpg.configure_item(cue_tag, p1=(cue_x, 0), p2=(cue_x, height))
        dpg.show_item(cue_tag)
    else:
        dpg.hide_item(cue_tag)

def update_local_waves():
    try:
        # Si quieres pausar updates durante cargas, ok:
        if not loop_enabled:
            return

        # ---- LOCAL WAVES ----
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

        # ---- VU ----
        vuA = dual.deck_a._audio_engine._vu
        vuB = dual.deck_b._audio_engine._vu
        draw_vu("vu_A", vuA)
        draw_vu("vu_B", vuB)
        master = min(1.0, vuA + vuB)
        draw_vu_stereo("vu_master", master, master)

        # ---- GLOBAL overlays (playhead/cue/loop etc) ----
        if dual.deck_a.waveform is not None:
            update_global_overlays(dual.deck_a, "global_wave_A")

        if dual.deck_b.waveform is not None:
            update_global_overlays(dual.deck_b, "global_wave_B")

    except Exception as e:
        print("[UI] update_local_waves crashed:", repr(e))

    finally:
        # ✅ SIEMPRE reprograma, aunque haya return o excepción
        dpg.set_frame_callback(dpg.get_frame_count() + 2, update_local_waves)

def draw_vu(parent, level, segments=24):
    dpg.delete_item(parent, children_only=True)

    width = 22
    height = 120
    seg_height = height / segments

    for i in range(segments):
        y1 = height - (i + 1) * seg_height
        y2 = height - i * seg_height

        # current level in segments
        active_segments = int(level * segments)

        # color according to area
        if i < segments * 0.6:
            color = (0, 200, 0)      
        elif i < segments * 0.85:
            color = (255, 200, 0)    
        else:
            color = (255, 0, 0)      

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
 
def load_from_library(deck_prefix):
    global loop_enabled
    loop_enabled = False
    try:
        tracks = get_all_tracks()
        selected = dpg.get_value("library_list")

        if not selected:
            print("[UI] No track selected")
            return

        titles = [t[2] for t in tracks] 
        selected_index = titles.index(selected)

        track = tracks[selected_index]
        path = track[1]      
        title = track[2]     

        if deck_prefix == "A":
            dual.deck_a.safe_load(path)
            draw_global_static(dual.deck_a, "global_wave_A")
            dpg.set_value("deck_a_title", title)
            dpg.set_value("A_bpm_label", f"{dual.deck_a.bpm:.2f} BPM")
            update_local_waves()
            
        else:
            dual.deck_b.safe_load(path)
            draw_global_static(dual.deck_b, "global_wave_B")
            dpg.set_value("deck_b_title", title)
            dpg.set_value("B_bpm_label", f"{dual.deck_b.bpm:.2f} BPM")
            update_local_waves()
    finally:  
        loop_enabled = True
  
def reanalyze_track():
    tracks = get_all_tracks()
    selected_title = dpg.get_value("library_list")

    if not selected_title:
        print("[UI] No track selected for reanalyze")
        return

    names = [t[2] for t in tracks]  # títulos
    try:
        idx = names.index(selected_title)
    except ValueError:
        print("[UI] Selected title not found in tracks")
        return

    track = tracks[idx]
    path = track[1]  # path

    delete_track_from_library(path)
    dual.deck_a.load_track(path)
    refresh_library_ui()

def frames_to_x(deck, frame, width=1120):
    eng = deck._audio_engine
    if eng is None or eng._raw_data is None:
        return 0

    bytes_per_frame = eng._sample_width * eng._channels
    total_frames = len(eng._raw_data) // bytes_per_frame
    if total_frames <= 0:
        return 0

    return (frame / total_frames) * width

def refresh_hotcue_markers(deck, tag, width=1120, height=60):
    node_tag = f"{tag}_hotcues"

    if not dpg.does_item_exist(node_tag):
        dpg.add_draw_node(tag=node_tag, parent=tag)

    # borrar solo hijos del nodo
    dpg.delete_item(node_tag, children_only=True)

    eng = deck._audio_engine
    if eng is None or eng._raw_data is None:
        return

    bytes_per_frame = eng._sample_width * eng._channels
    total_frames = len(eng._raw_data) // bytes_per_frame
    if total_frames <= 0:
        return

    for n, frame in sorted(deck.hotcues.items()):
        x = (frame / total_frames) * width

        dpg.draw_line(
            (x, 0),
            (x, height),
            color=(255, 255, 0),
            thickness=2,
            parent=node_tag
        )

        dpg.draw_text(
            (x + 2, 2),
            str(n),
            color=(255, 255, 0),
            parent=node_tag
        )
        
def add_hotcue_ui(prefix, deck, global_tag):
    set_tag = f"hotcue_set_{prefix}"
    dpg.add_checkbox(label="SET", tag=set_tag)

    def hotcue_pressed(sender, app_data, user_data):
        n = user_data
        if n is None:
            return

        if dpg.get_value(set_tag):
            deck.set_hotcue(n)
            refresh_hotcue_markers(deck, global_tag)
        else:
            deck.goto_hotcue(n)

    with dpg.group(horizontal=True):
        for n in (1, 2, 3, 4):
            dpg.add_button(label=str(n), width=30, callback=hotcue_pressed, user_data=n)

def refresh_loop_markers(deck, tag, width=1120, height=60):
    node_tag = f"{tag}_loop"
    if not dpg.does_item_exist(node_tag):
        dpg.add_draw_node(tag=node_tag, parent=tag)

    dpg.delete_item(node_tag, children_only=True)

    eng = deck._audio_engine
    if eng is None or eng._raw_data is None:
        return

    bytes_per_frame = eng._sample_width * eng._channels
    total_frames = len(eng._raw_data) // bytes_per_frame
    if total_frames <= 0:
        return

    # IN
    if deck.loop_in is not None:
        x = (deck.loop_in / total_frames) * width
        dpg.draw_line((x, 0), (x, height), color=(0, 255, 0), thickness=2, parent=node_tag)
        dpg.draw_text((x + 2, 2), "IN", color=(0, 255, 0), parent=node_tag)

    # OUT
    if deck.loop_out is not None:
        x = (deck.loop_out / total_frames) * width
        dpg.draw_line((x, 0), (x, height), color=(255, 0, 255), thickness=2, parent=node_tag)
        dpg.draw_text((x + 2, 2), "OUT", color=(255, 0, 255), parent=node_tag)

    # Estado loop (opcional): un rectángulo tenue entre IN y OUT
    if deck.loop_enabled and deck.loop_in is not None and deck.loop_out is not None and deck.loop_out > deck.loop_in:
        x1 = (deck.loop_in / total_frames) * width
        x2 = (deck.loop_out / total_frames) * width
        dpg.draw_rectangle((x1, 0), (x2, height), fill=(80, 80, 80, 40), color=(0,0,0,0), parent=node_tag)

def add_loop_ui(prefix, deck, global_tag):
    def on_in():
        deck.set_loop_in()
        refresh_loop_markers(deck, global_tag)

    def on_out():
        deck.set_loop_out()
        refresh_loop_markers(deck, global_tag)

    def on_loop():
        before = deck.loop_enabled
        deck.toggle_loop()
        if before == False and deck.loop_enabled == False:
            # intentó activar pero no pudo
            print(f"[UI] Loop not enabled on Deck {prefix}: set valid IN/OUT first")
        refresh_loop_markers(deck, global_tag)

    def on_clear():
        deck.clear_loop()
        refresh_loop_markers(deck, global_tag)

    with dpg.group(horizontal=True):
        dpg.add_button(label="IN", width=45, callback=lambda: on_in())
        dpg.add_button(label="OUT", width=45, callback=lambda: on_out())
        dpg.add_button(label="LOOP", width=60, callback=lambda: on_loop())
        dpg.add_button(label="CLR", width=45, callback=lambda: on_clear())

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
    # GLOBAL WAVEFORM A
    # -----------------------------
    with dpg.window(label="Dual Deck", width=1150, height=850):
        dpg.add_spacer(height=20)

        # GLOBAL A
        with dpg.drawlist(width=1120, height=60, tag="global_wave_A"):
            dpg.draw_rectangle((0,0), (1120,60), fill=(0,0,0), color=(0,0,0))

        dpg.add_spacer(height=10)

        # GLOBAL B
        with dpg.drawlist(width=1120, height=60, tag="global_wave_B"):
            dpg.draw_rectangle((0,0), (1120,60), fill=(0,0,0), color=(0,0,0))

            
        dpg.add_spacer(height=20)
        # -----------------------------
        # LOCAL WAVES
        # -----------------------------
        with dpg.group(horizontal=True):
            
            with dpg.group():
                dpg.add_spacer(height=30)
                dpg.add_text("No track", tag="deck_a_title")

                with dpg.drawlist(width=300, height=60, tag="local_wave_A"):
                    dpg.draw_rectangle((0, 0), (300, 60), fill=(0, 0, 0), color=(0,0,0))

                # ✅ HOTCUES debajo de la onda local
                add_hotcue_ui("A", dual.deck_a, "global_wave_A")
                add_loop_ui("A", dual.deck_a, "global_wave_A")
                
                

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
                add_hotcue_ui("B", dual.deck_b, "global_wave_B")
                add_loop_ui("B", dual.deck_b, "global_wave_B")
            build_pitch_ui("B", dual.deck_b)
            
        # -----------------------------
        # DECK CONTROLS (A y B)
        # -----------------------------
        with dpg.group(horizontal=True):

            # -----------------------------
            # DECK A
            # -----------------------------
            with dpg.group(horizontal=True):
             
                load_a = dpg.add_button(label="Load A", callback=load_track_a)
                dpg.bind_item_theme(load_a,  "theme_controls_default")
                play_aa = dpg.add_button(label="play", callback=play_a)
                dpg.bind_item_theme(play_aa,  "theme_controls_default")
                pause_aa = dpg.add_button(label="pause", callback=pause_a)
                dpg.bind_item_theme(pause_aa,  "theme_controls_default")
                dpg.add_spacer(width=135)
                dpg.add_text("  0.00 BPM  ", tag="A_bpm_label")
                
            dpg.add_spacer(width=70)

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

            dpg.add_spacer(width=20)

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
                dpg.add_spacer(width=145)
                dpg.add_text("0.00 BPM", tag="B_bpm_label")

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=530)
            dpg.add_text("0.50", tag="cross_value")
            
        dpg.add_button(label="Reanalyze Selected", callback=reanalyze_track)


        with dpg.child_window(label="Library", tag="library_window", width=300, height=400):

            dpg.add_listbox([], tag="library_list", width=280, num_items=15)
            dpg.add_button(label="Load to Deck A", callback=lambda: load_from_library("A"))
            dpg.add_button(label="Load to Deck B", callback=lambda: load_from_library("B"))

        refresh_library_ui()


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
    # START DPG
    # -----------------------------
    dpg.create_viewport(title="Dual Deck", width=1150, height=850)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    update_local_waves()
    dpg.start_dearpygui()
    dpg.destroy_context()