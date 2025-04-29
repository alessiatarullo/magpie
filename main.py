import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
from mutagen import File
from mutagen.easyid3 import EasyID3

if os.name == 'nt':
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)

window = tk.Tk()
window.geometry("600x700")
window.title("magpie")
window.iconbitmap('magpie.ico')
window.configure(background="white")

audio_extensions = ('.mp3', '.wav', '.flac', '.m4a', '.aac', '.wma', '.ogg')
image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
checkbox_vars = {}  # Dizionario globale per le checkbox

def show_files():
    global checkbox_vars
    directory = filedialog.askdirectory()
    if directory:
        path_label.config(text=f"Percorso: {directory}")
        files = os.listdir(directory)
        
        # Pulisci la lista precedente
        for widget in files_container.winfo_children():
            widget.destroy()
        checkbox_vars.clear()
            
        # Crea checkbox per ogni file audio
        row = 0
        for file in files:
            if is_audio_file(file):
                var = tk.BooleanVar(value=True)  # Default: Title Case attivo
                checkbox_vars[file] = var
                
                frame = ttk.Frame(files_container)
                frame.grid(row=row, column=0, sticky='w', pady=2)
                
                ttk.Checkbutton(frame, variable=var, text="Title Case").pack(side='left', padx=(0,10))
                ttk.Label(frame, text=file).pack(side='left')
                
                row += 1

def is_audio_file(filename):
    return filename.lower().endswith(audio_extensions)

def is_image_file(filename):
    return filename.lower().endswith(image_extensions)

def format_featuring(artists):
    if not artists:  # Se la lista è vuota
        return ""
    elif len(artists) == 1:
        return f" [feat {artists[0]}]"
    elif len(artists) == 2:
        return f" [feat {artists[0]} & {artists[1]}]"
    else:
        return f" [feat {', '.join(artists[:-1])} & {artists[-1]}]"

def format_title(title):
    exceptions = {
        "a", "an", "the",
        "and", "but", "or", "nor", "for", "so", "yet",
        "at", "by", "in", "of", "on", "to", "up", "with"
    }
    words = title.split()
    if not words:
        return title
    formatted = []
    for i, word in enumerate(words):
        if word.isupper():
            formatted.append(word)
        else:
            if i == 0:
                formatted.append(word.capitalize())
            elif word.lower() in exceptions:
                formatted.append(word.lower())
            else:
                formatted.append(word.capitalize())
    return " ".join(formatted)

def rename_from_metadata():
    directory = path_label.cget("text").replace("Percorso: ", "")
    if directory == "Nessuna cartella selezionata":
        messagebox.showerror("Errore", "Seleziona prima una cartella!")
        return
    
    files = os.listdir(directory)
    audio_files = [f for f in files if is_audio_file(f)]
    image_files = [f for f in files if is_image_file(f)]
    
    # Rinomina le immagini
    folder_name = os.path.basename(directory)
    for idx, image_file in enumerate(image_files, 1):
        try:
            old_path = os.path.join(directory, image_file)
            extension = os.path.splitext(image_file)[1]
            if len(image_files) > 1:
                new_name = f"{folder_name} ({idx}){extension}"
            else:
                new_name = f"{folder_name}{extension}"
            new_path = os.path.join(directory, new_name)
            os.rename(old_path, new_path)
        except Exception as e:
            tk.messagebox.showerror("Errore", f"Errore nel rinominare l'immagine {image_file}: {str(e)}")
    
    # Rinomina i file audio
    for file in audio_files:
        try:
            file_path = os.path.join(directory, file)
            audio = File(file_path)
            
            if audio is None:
                tk.messagebox.showerror("Errore", f"Impossibile leggere i metadati di {file}")
                continue
            
            artist = None
            featuring_artists = []
            title = None
            track = None
            album = None

            if hasattr(audio, 'tags'):
                tags = audio.tags
                for artist_tag in ['artist', 'TPE1', '©ART', 'Author']:
                    if artist_tag in tags:
                        artist_value = tags[artist_tag]
                        if isinstance(artist_value, (list, tuple)):
                            artist = str(artist_value[0])
                            if len(artist_value) > 1:
                                featuring_artists = [str(a) for a in artist_value[1:]]
                        else:
                            full_artist = str(artist_value)
                            if 'feat.' in full_artist.lower() or 'feat' in full_artist.lower():
                                parts = full_artist.split('feat')
                                artist = parts[0].strip()
                                if len(parts) > 1:
                                    feat_part = parts[1].replace('.', '').strip()
                                    for feat in feat_part.replace(' & ', ', ').split(','):
                                        feat = feat.strip()
                                        if feat:
                                            featuring_artists.append(feat)
                            else:
                                artist = full_artist
                        break
                
                for title_tag in ['title', 'TIT2', '©nam', 'Title']:
                    if title_tag in tags:
                        title = str(tags[title_tag][0])
                        break

                for album_tag in ['album', 'TALB', '©alb']:
                    if album_tag in tags:
                        album = str(tags[album_tag][0])
                        break
                
                for track_tag in ['tracknumber', 'TRCK', 'trkn']:
                    if track_tag in tags:
                        val = tags[track_tag][0]
                        if isinstance(val, tuple):
                            track = str(val[0]).zfill(2)
                        else:
                            track = str(val).split('/')[0].zfill(2)
                        break

            artist = artist if artist else "Unknown Artist"
            title = title if title else "Unknown Title"
            track = track if track else "00"
            album = album if album else "Unknown Album"

            invalid_chars = r'\/:*?"<>|'
            artist = ''.join(c for c in artist if c not in invalid_chars)
            title = ''.join(c for c in title if c not in invalid_chars)
            album = ''.join(c for c in album if c not in invalid_chars)
            featuring_artists = [''.join(c for c in f if c not in invalid_chars) for f in featuring_artists]

            # Controlla se questo file deve essere formattato in Title Case
            if file in checkbox_vars and checkbox_vars[file].get():
                formatted_title = format_title(title)
            else:
                formatted_title = title  # Lascia il titolo invariato
                
            featuring_string = format_featuring(featuring_artists) if featuring_artists else ""
            
            extension = os.path.splitext(file)[1]
            new_name = f"{artist} - {album} - {track} - {formatted_title}{featuring_string}{extension}"
            new_path = os.path.join(directory, new_name)
            os.rename(file_path, new_path)
            
        except Exception as e:
            tk.messagebox.showerror("Errore", f"Errore nel rinominare {file}: {str(e)}")
            continue
    
    # Aggiorna la lista dei file
    files = os.listdir(directory)
    
    # Pulisci la lista precedente
    for widget in files_container.winfo_children():
        widget.destroy()
    checkbox_vars.clear()
            
    # Ricrea le checkbox per i file audio
    row = 0
    for file in files:
        if is_audio_file(file):
            var = tk.BooleanVar(value=True)
            checkbox_vars[file] = var
            
            frame = ttk.Frame(files_container)
            frame.grid(row=row, column=0, sticky='w', pady=2)
            
            ttk.Checkbutton(frame, variable=var, text="Title Case").pack(side='left', padx=(0,10))
            ttk.Label(frame, text=file).pack(side='left')
            
            row += 1

    tk.messagebox.showinfo("Successo", "File rinominati con successo!")

# Creazione dell'interfaccia
select_button = ttk.Button(
    window,
    text="Seleziona Cartella",
    command=show_files
)
select_button.pack(pady=20)

path_label = ttk.Label(window, text="Nessuna cartella selezionata")
path_label.pack(pady=10)

# Frame per la lista dei file con scrollbar
file_frame = ttk.Frame(window)
file_frame.pack(pady=10, fill='both', expand=True)

# Scrollbar verticale
scrollbar_y = ttk.Scrollbar(file_frame)
scrollbar_y.pack(side='right', fill='y')

# Scrollbar orizzontale
scrollbar_x = ttk.Scrollbar(file_frame, orient='horizontal')
scrollbar_x.pack(side='bottom', fill='x')

# Canvas
canvas = tk.Canvas(file_frame)
canvas.pack(side='left', fill='both', expand=True)

# Configura lo scrolling
scrollbar_y.configure(command=canvas.yview)
scrollbar_x.configure(command=canvas.xview)
canvas.configure(yscrollcommand=scrollbar_y.set,
                xscrollcommand=scrollbar_x.set)

# Frame interno per i file e le checkbox
files_container = ttk.Frame(canvas)
canvas_window = canvas.create_window((0, 0), window=files_container, anchor='nw')

# Funzione per aggiornare lo scrolling
def configure_scroll(event):
    canvas.configure(scrollregion=canvas.bbox('all'))
    canvas.itemconfig(canvas_window, width=canvas.winfo_width())

files_container.bind('<Configure>', configure_scroll)

rename_metadata_button = ttk.Button(
    window,
    text="Rinomina usando Metadati",
    command=rename_from_metadata
)
rename_metadata_button.pack(pady=10)

if __name__ == '__main__':
    window.mainloop()