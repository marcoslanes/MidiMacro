import threading
import customtkinter as ctk
import mido
import mido.backends.rtmidi
import time
import json
import os
import sys
import subprocess
import ctypes
from tkinter import filedialog
from pynput import keyboard
from PIL import Image
import pystray

# --- FIX: APP ID ---
try:
    myappid = 'lanes.it.midimacro.v4' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except: pass

mido.set_backend('mido.backends.rtmidi')
kb_controller = keyboard.Controller()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MidiMacroPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MIDI Macro Pro")
        self.geometry("1100x700")
        self.configure(fg_color="#0f172a")

        self.icon_path = resource_path("icon.ico")
        if os.path.exists(self.icon_path):
            self.iconbitmap(self.icon_path)
            self.icon_image = Image.open(self.icon_path)
        else: self.icon_image = None

        self.listening = False
        self.config_file = "macros_v4.json"
        self.macros = self.load_config()
        self.recorded_keys = []
        self.is_recording = False
        self.last_midi_id = None
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_list())

        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color="#1e293b")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="CONTROLE", font=("Segoe UI", 16, "bold")).pack(pady=(30, 20))
        
        self.btn_toggle = ctk.CTkButton(self.sidebar, text="LIGAR MONITOR", command=self.toggle_monitor, 
                                        fg_color="#10b981", hover_color="#059669", height=35)
        self.btn_toggle.pack(pady=10, padx=20)
        
        self.status_led = ctk.CTkLabel(self.sidebar, text="● OFFLINE", text_color="#ef4444", font=("Segoe UI", 11, "bold"))
        self.status_led.pack(pady=5)

        # --- ÁREA PRINCIPAL ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=25, pady=20)

        self.top_row = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.top_row.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(self.top_row, text="Minhas Macros", font=("Segoe UI", 22, "bold")).pack(side="left")
        
        self.search_entry = ctk.CTkEntry(self.top_row, placeholder_text="🔍 Buscar...", 
                                         width=250, textvariable=self.search_var, fg_color="#1e293b", border_color="#334155")
        self.search_entry.pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

        # --- FOOTER ---
        self.footer = ctk.CTkFrame(self.main_area, fg_color="#1e293b", corner_radius=12)
        self.footer.pack(fill="x", pady=(15, 0))

        self.input_row = ctk.CTkFrame(self.footer, fg_color="transparent")
        self.input_row.pack(pady=10, padx=15, fill="x")

        self.alias_entry = ctk.CTkEntry(self.input_row, placeholder_text="Apelido da Macro", 
                                        width=200, fg_color="#0f172a", border_color="#334155")
        self.alias_entry.grid(row=0, column=0, padx=5)

        self.btn_record_kb = ctk.CTkButton(self.input_row, text="Atalho", command=self.start_kb_record, 
                                           fg_color="#334155", width=90)
        self.btn_record_kb.grid(row=0, column=1, padx=5)

        ctk.CTkButton(self.input_row, text="+ Pasta", command=self.add_folder_macro, 
                      fg_color="#334155", width=80).grid(row=0, column=2, padx=5)
        
        ctk.CTkButton(self.input_row, text="+ App", command=self.add_app_macro, 
                      fg_color="#334155", width=80).grid(row=0, column=3, padx=5)

        self.label_preview = ctk.CTkLabel(self.footer, text="Toque em uma tecla MIDI...", 
                                          font=("Consolas", 12), text_color="#94a3b8")
        self.label_preview.pack(pady=(0, 10))

        self.refresh_list()

    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        search_query = self.search_var.get().lower()

        for midi_id, data in self.macros.items():
            alias = data.get('alias', 'Sem Nome')
            note_name = self.get_note_name(midi_id.split('_')[-1])
            
            if search_query and search_query not in alias.lower() and search_query not in note_name.lower():
                continue

            # CARD COMPACTO (height=50)
            card = ctk.CTkFrame(self.scroll_frame, fg_color="#1e293b", height=50, corner_radius=8)
            card.pack(fill="x", pady=3, padx=5)
            card.pack_propagate(False) # Mantém a altura fixa
            
            accent_colors = {"Trigger Shortcut": "#3b82f6", "Open Folder": "#eab308", "Launch App": "#10b981"}
            accent = ctk.CTkFrame(card, width=4, fg_color=accent_colors.get(data['type'], "#64748b"), corner_radius=0)
            accent.pack(side="left", fill="y")

            ctk.CTkLabel(card, text=note_name, font=("Consolas", 13, "bold"), width=80, text_color="#60a5fa").pack(side="left", padx=10)

            # Texto em linha única para economizar espaço
            detail = " + ".join(data['keys']).upper() if 'keys' in data else os.path.basename(data['path'])
            info_text = f"{alias.upper()}  •  {detail}"
            
            ctk.CTkLabel(card, text=info_text, font=("Segoe UI", 12), anchor="w", text_color="#f8fafc").pack(side="left", fill="x", expand=True, padx=5)

            ctk.CTkButton(card, text="✕", width=28, height=28, fg_color="transparent", hover_color="#ef4444", 
                          command=lambda m=midi_id: self.delete_macro(m)).pack(side="right", padx=10)

    def save_macro_data(self, macro_type, keys=None, path=None):
        if not self.last_midi_id: return
        alias = self.alias_entry.get() or "Nova Macro"
        self.macros[self.last_midi_id] = {
            "type": macro_type, "alias": alias, "keys": keys if keys else [], "path": path if path else ""
        }
        self.save_config()
        self.refresh_list()
        self.alias_entry.delete(0, 'end')

    def hide_window(self):
        self.withdraw()
        if not hasattr(self, 'tray_icon'):
            menu = pystray.Menu(pystray.MenuItem("Abrir", self.show_window), pystray.MenuItem("Sair", self.quit_app))
            self.tray_icon = pystray.Icon("MidiMacro", self.icon_image, "MIDI Macro Pro", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        if hasattr(self, 'tray_icon'): self.tray_icon.stop(); del self.tray_icon
        self.deiconify()

    def quit_app(self, icon=None, item=None):
        if hasattr(self, 'tray_icon'): self.tray_icon.stop()
        self.destroy(); os._exit(0)

    def normalize_key(self, key):
        try:
            if hasattr(key, 'vk') and key.vk is not None:
                vk = key.vk
                if 65 <= vk <= 90: return chr(vk).lower()
                if 48 <= vk <= 57: return chr(vk)
            k = str(key).replace("Key.", "")
            special = {"ctrl_l": "ctrl", "alt_l": "alt", "shift_l": "shift", "enter": "enter", "space": "space"}
            return special.get(k, k.lower())
        except: return str(key).lower()

    def execute_macro_async(self, data):
        threading.Thread(target=self.execute_macro, args=(data,), daemon=True).start()

    def execute_macro(self, data):
        try:
            if data['type'] == "Trigger Shortcut":
                objs = [getattr(keyboard.Key, k) if k in ['ctrl', 'alt', 'shift', 'cmd', 'enter', 'space', 'tab', 'esc'] else k for k in data['keys']]
                for o in objs: kb_controller.press(o)
                time.sleep(0.08)
                for o in reversed(objs): kb_controller.release(o)
            elif data['type'] == "Open Folder": os.startfile(data['path'])
            elif data['type'] == "Launch App": subprocess.Popen(data['path'])
        except: pass

    def get_note_name(self, n):
        try:
            val = int(n)
            notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            return f"{notes[val % 12]}{(val // 12) - 1}"
        except: return n

    def midi_loop(self):
        while self.listening:
            try:
                names = mido.get_input_names()
                if not names: time.sleep(1); continue
                with mido.open_input(names[0]) as inport:
                    self.status_led.configure(text="● ONLINE", text_color="#10b981")
                    for msg in inport:
                        if not self.listening: break
                        if (msg.type == 'note_on' and msg.velocity > 0) or (msg.type == 'control_change' and msg.value > 0):
                            val = msg.note if hasattr(msg, 'note') else msg.control
                            midi_key = f"{msg.type}_{val}"
                            self.last_midi_id = midi_key
                            self.label_preview.configure(text=f"TECLA: {self.get_note_name(val)}", text_color="#60a5fa")
                            if midi_key in self.macros:
                                self.execute_macro_async(self.macros[midi_key])
            except: 
                self.status_led.configure(text="● ERRO", text_color="#ef4444")
                time.sleep(1)

    def start_kb_record(self):
        if not self.last_midi_id: return
        self.recorded_keys = []
        self.is_recording = True
        self.btn_record_kb.configure(text="GRAVANDO", fg_color="#eab308")
        self.kb_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.kb_listener.start()

    def on_press(self, key):
        if not self.is_recording: return
        k = self.normalize_key(key)
        if k and k not in self.recorded_keys: self.recorded_keys.append(k)
        self.label_preview.configure(text=f"HOTKEY: {' + '.join(self.recorded_keys).upper()}")

    def on_release(self, key):
        self.is_recording = False
        self.btn_record_kb.configure(text="Atalho", fg_color="#334155")
        if hasattr(self, 'kb_listener'): self.kb_listener.stop()
        if self.recorded_keys: self.save_macro_data("Trigger Shortcut", keys=self.recorded_keys)

    def add_folder_macro(self):
        path = filedialog.askdirectory()
        if path: self.save_macro_data("Open Folder", path=path)

    def add_app_macro(self):
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if path: self.save_macro_data("Launch App", path=path)

    def delete_macro(self, m_id):
        if m_id in self.macros: del self.macros[m_id]; self.save_config(); self.refresh_list()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def save_config(self):
        with open(self.config_file, 'w') as f: json.dump(self.macros, f)

    def toggle_monitor(self):
        self.listening = not self.listening
        self.btn_toggle.configure(text="PARAR MONITOR" if self.listening else "LIGAR MONITOR", 
                                  fg_color="#ef4444" if self.listening else "#10b981")
        if self.listening: threading.Thread(target=self.midi_loop, daemon=True).start()
        else: self.status_led.configure(text="● OFFLINE", text_color="#ef4444")

if __name__ == "__main__":
    app = MidiMacroPro()
    app.mainloop()