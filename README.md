# 🎹 MIDI Macro Pro

Transforme qualquer tecla MIDI em atalhos globais, abertura de pastas ou lançamento de aplicativos.

## ✨ Funcionalidades
- **Atalhos Globais:** Execute comandos mesmo com o app minimizado.
- **Hardware Level:** Identificação física de teclas (contorna bugs de layout).
- **System Tray:** Minimiza para a bandeja do sistema.
- **Interface Moderna:** Dark mode com sistema de busca e apelidos.

## 🚀 Como usar o Executável
1. Vá até a seção [Releases](https://github.com/marcoslanes/MidiMacro/tree/main/release) e baixe o `MidiMacroPro.exe`.
2. Execute como **Administrador** (necessário para injetar teclas em outros apps).
3. Selecione uma tecla MIDI e configure sua ação.

## 🛠️ Instalação (Para Desenvolvedores)
1. Instale o Python 3.11.
2. Instale as dependências: `pip install customtkinter mido python-rtmidi pynput Pillow pystray`
3. Execute: `python main.py`