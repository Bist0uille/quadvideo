import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
from PIL import Image, ImageTk
import numpy as np
import os
import random
import glob

class QuadVideoPlayer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Lecteur 4 Vidéos - Vue Carré")
        self.root.geometry("800x800")
        
        # Variables pour les vidéos
        self.caps = [None, None, None, None]
        self.labels = [None, None, None, None]
        self.current_folder = None
        self.video_files_in_folder = []
        self.selected_videos = [None, None, None, None]
        self.previously_used_videos = set()  # Historique des vidéos déjà utilisées
        
        # Variables de contrôle - gestion améliorée
        self.playing = False
        self.video_threads = []
        self.thread_lock = threading.Lock()
        self.stop_event = threading.Event()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame pour les boutons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Frame pour afficher le dossier courant
        folder_info_frame = tk.Frame(main_frame)
        folder_info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Label pour afficher le dossier courant
        self.folder_label = tk.Label(folder_info_frame, text="Aucun dossier sélectionné", 
                                    bg="#E0E0E0", fg="#333", font=("Arial", 9), 
                                    relief=tk.SUNKEN, anchor="w", padx=10)
        self.folder_label.pack(fill=tk.X)
        
        # Boutons de contrôle
        tk.Button(button_frame, text="Charger Vidéos", command=self.load_videos, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Charger Dossier", command=self.load_folder, 
                 bg="#9C27B0", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="4 Vidéos Random", command=self.load_random_videos, 
                 bg="#FF5722", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Réinitialiser Historique", command=self.reset_history, 
                 bg="#607D8B", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Play", command=self.play_videos, 
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Pause", command=self.pause_videos, 
                 bg="#FF9800", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Stop", command=self.stop_videos, 
                 bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Frame pour les vidéos (disposition 2x2)
        video_frame = tk.Frame(main_frame, bg="black")
        video_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configuration de la grille 2x2
        video_frame.grid_rowconfigure(0, weight=1)
        video_frame.grid_rowconfigure(1, weight=1)
        video_frame.grid_columnconfigure(0, weight=1)
        video_frame.grid_columnconfigure(1, weight=1)
        
        # Création des labels pour chaque vidéo
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for i, (row, col) in enumerate(positions):
            label = tk.Label(video_frame, text=f"Vidéo {i+1}\nUtilisez 'Charger Dossier' puis '4 Vidéos Random'", 
                           bg="black", fg="white", font=("Arial", 10), bd=0, highlightthickness=0)
            label.grid(row=row, column=col, sticky="nsew", padx=0, pady=0)
            self.labels[i] = label
    
    def load_folder(self):
        """Charge un dossier contenant des vidéos"""
        folder_path = filedialog.askdirectory(title="Sélectionner un dossier contenant des vidéos",
                                             initialdir=self.current_folder if self.current_folder else None)
        
        if not folder_path:
            return
        
        self.current_folder = folder_path
        
        # Réinitialiser l'historique quand on change de dossier
        self.previously_used_videos.clear()
        
        # Mettre à jour l'affichage du dossier
        folder_display = folder_path
        if len(folder_display) > 80:  # Tronquer si trop long
            folder_display = "..." + folder_display[-77:]
        self.folder_label.config(text=f"📁 Dossier: {folder_display}")
        
        # Extensions vidéo supportées
        video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.m4v', '*.webm']
        
        # Rechercher tous les fichiers vidéo dans le dossier et sous-dossiers
        self.video_files_in_folder = []
        for extension in video_extensions:
            # Recherche dans le dossier principal
            self.video_files_in_folder.extend(glob.glob(os.path.join(folder_path, extension)))
            # Recherche dans les sous-dossiers
            self.video_files_in_folder.extend(glob.glob(os.path.join(folder_path, '**', extension), recursive=True))
        
        # Supprimer les doublons et trier
        self.video_files_in_folder = list(set(self.video_files_in_folder))
        self.video_files_in_folder.sort()
        
        print(f"DEBUG: Trouvé {len(self.video_files_in_folder)} vidéos dans le dossier")
        for i, video in enumerate(self.video_files_in_folder[:10]):  # Afficher les 10 premières
            print(f"  {i+1}: {os.path.basename(video)}")
        
        if len(self.video_files_in_folder) < 4:
            messagebox.showwarning("Attention", 
                                 f"Le dossier contient seulement {len(self.video_files_in_folder)} vidéo(s).\n"
                                 f"Il faut au moins 4 vidéos pour utiliser cette fonctionnalité.")
            self.folder_label.config(text=f"📁 Dossier: {folder_display} ⚠️ ({len(self.video_files_in_folder)} vidéos - insuffisant)")
            return
        
        # Mettre à jour l'affichage avec le nombre de vidéos
        self.folder_label.config(text=f"📁 Dossier: {folder_display} ✅ ({len(self.video_files_in_folder)} vidéos)")
        
        # Pas de message popup - juste mettre à jour les labels
        for i in range(4):
            self.labels[i].config(text=f"Vidéo {i+1}\nDossier chargé - Cliquez '4 Vidéos Random'")
    
    def reset_history(self):
        """Réinitialise l'historique des vidéos déjà utilisées"""
        self.previously_used_videos.clear()
        print("DEBUG: Historique des vidéos réinitialisé")
        messagebox.showinfo("Historique", "L'historique des vidéos utilisées a été réinitialisé.\nToutes les vidéos peuvent maintenant être resélectionnées.")
        
        # Mettre à jour l'affichage si un dossier est chargé
        if self.current_folder and self.video_files_in_folder:
            folder_display = self.current_folder
            if len(folder_display) > 80:
                folder_display = "..." + folder_display[-77:]
            self.folder_label.config(text=f"📁 Dossier: {folder_display} ✅ ({len(self.video_files_in_folder)} vidéos) 🔄 Historique effacé")
    
    def force_cleanup(self):
        """Nettoyage forcé et immédiat de toutes les ressources"""
        print("DEBUG: Début du nettoyage forcé")
        
        # Arrêter immédiatement toute lecture
        self.playing = False
        self.stop_event.set()
        
        # Attendre que tous les threads se terminent (avec timeout)
        with self.thread_lock:
            for i, thread in enumerate(self.video_threads):
                if thread.is_alive():
                    print(f"DEBUG: Attente de la fin du thread {i}")
                    thread.join(timeout=0.5)  # Timeout plus court
                    if thread.is_alive():
                        print(f"DEBUG: Thread {i} toujours actif après timeout")
            
            self.video_threads.clear()
        
        # Fermer toutes les captures vidéo
        for i in range(4):
            if self.caps[i] is not None:
                print(f"DEBUG: Fermeture de la capture {i}")
                try:
                    self.caps[i].release()
                except:
                    pass
                self.caps[i] = None
            
            # Nettoyer les labels
            try:
                self.labels[i].config(image="")
                if hasattr(self.labels[i], 'image'):
                    self.labels[i].image = None
            except:
                pass
        
        # Réinitialiser l'événement d'arrêt
        self.stop_event.clear()
        
        # Petit délai pour s'assurer que tout est nettoyé
        time.sleep(0.1)
        print("DEBUG: Nettoyage forcé terminé")
    
    def select_unique_random_videos(self):
        """Sélectionne 4 vidéos vraiment aléatoires et uniques, en évitant celles déjà utilisées"""
        if len(self.video_files_in_folder) < 4:
            return []
        
        # Ajouter les vidéos actuellement chargées à l'historique
        for video in self.selected_videos:
            if video is not None:
                self.previously_used_videos.add(video)
        
        # Calculer les vidéos disponibles (non utilisées récemment)
        available_videos = [v for v in self.video_files_in_folder if v not in self.previously_used_videos]
        
        print(f"DEBUG: Total de vidéos: {len(self.video_files_in_folder)}")
        print(f"DEBUG: Vidéos déjà utilisées: {len(self.previously_used_videos)}")
        print(f"DEBUG: Vidéos disponibles: {len(available_videos)}")
        
        # Si on n'a pas assez de nouvelles vidéos, on réinitialise partiellement l'historique
        if len(available_videos) < 4:
            print("DEBUG: Pas assez de nouvelles vidéos - réinitialisation partielle de l'historique")
            
            # Garder seulement les 4 vidéos actuellement chargées dans l'historique
            current_videos = {v for v in self.selected_videos if v is not None}
            self.previously_used_videos = current_videos.copy()
            
            # Recalculer les vidéos disponibles
            available_videos = [v for v in self.video_files_in_folder if v not in self.previously_used_videos]
            
            print(f"DEBUG: Après réinitialisation partielle - Vidéos disponibles: {len(available_videos)}")
            
            # Si on n'a toujours pas assez, prendre toutes les vidéos sauf les actuelles
            if len(available_videos) < 4:
                available_videos = [v for v in self.video_files_in_folder if v not in current_videos]
                print(f"DEBUG: Utilisation de toutes les vidéos sauf les actuelles: {len(available_videos)}")
        
        # Mélanger plusieurs fois pour plus de randomisation
        for _ in range(3):
            random.shuffle(available_videos)
        
        # Prendre les 4 premières vidéos uniques
        selected = available_videos[:4]
        
        print("DEBUG: Nouvelles vidéos sélectionnées:")
        for i, video in enumerate(selected):
            print(f"  Position {i+1}: {os.path.basename(video)}")
        
        return selected
    
    def load_random_videos(self):
        """Charge 4 vidéos aléatoires depuis le dossier - version améliorée avec historique"""
        if not self.video_files_in_folder:
            messagebox.showwarning("Attention", "Veuillez d'abord charger un dossier avec 'Charger Dossier'")
            return
        
        if len(self.video_files_in_folder) < 4:
            messagebox.showwarning("Attention", "Il faut au moins 4 vidéos dans le dossier")
            return
        
        print("DEBUG: Début du chargement de vidéos aléatoires")
        
        # Nettoyage forcé et complet
        self.force_cleanup()
        
        # Mettre à jour l'affichage du dossier pour indiquer le chargement
        current_text = self.folder_label.cget("text")
        base_text = current_text.split(" 🔄")[0].split(" ✅")[0]
        self.folder_label.config(text=f"{base_text} 🔄 Chargement nouvelles vidéos...")
        self.root.update()
        
        # Sélectionner 4 vidéos uniques et nouvelles
        selected_video_paths = self.select_unique_random_videos()
        
        if len(selected_video_paths) < 4:
            messagebox.showerror("Erreur", "Impossible de sélectionner 4 vidéos différentes")
            return
        
        # Charger chaque vidéo
        success_count = 0
        new_selected_videos = [None, None, None, None]
        
        for i in range(4):
            video_path = selected_video_paths[i]
            print(f"DEBUG: Chargement de la vidéo {i+1}: {os.path.basename(video_path)}")
            
            # Créer une nouvelle capture pour cette vidéo
            cap = cv2.VideoCapture(video_path)
            
            if cap.isOpened():
                # Vérifier que la vidéo a bien des frames
                ret, test_frame = cap.read()
                if ret:
                    # Remettre au début
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    
                    self.caps[i] = cap
                    new_selected_videos[i] = video_path
                    filename = os.path.basename(video_path)
                    display_name = filename[:25] + ('...' if len(filename) > 25 else '')
                    self.labels[i].config(text=f"Vidéo {i+1}\n{display_name}")
                    success_count += 1
                    print(f"DEBUG: Vidéo {i+1} chargée avec succès")
                else:
                    print(f"DEBUG: Vidéo {i+1} ne contient pas de frames valides")
                    cap.release()
                    self.labels[i].config(text=f"Vidéo {i+1}\nErreur: pas de frames")
            else:
                print(f"DEBUG: Impossible d'ouvrir la vidéo {i+1}")
                cap.release()
                self.labels[i].config(text=f"Vidéo {i+1}\nErreur de chargement")
        
        # Mettre à jour la liste des vidéos sélectionnées seulement si le chargement a réussi
        if success_count == 4:
            self.selected_videos = new_selected_videos
        
        # Restaurer l'affichage du dossier
        folder_display = self.current_folder
        if len(folder_display) > 80:
            folder_display = "..." + folder_display[-77:]
        
        # Afficher le nombre de vidéos utilisées vs total
        used_count = len(self.previously_used_videos)
        total_count = len(self.video_files_in_folder)
        self.folder_label.config(text=f"📁 Dossier: {folder_display} ✅ ({total_count} vidéos) 🎬 {used_count} utilisées")
        
        print(f"DEBUG: {success_count} vidéos chargées sur 4")
        
        # Auto-play si toutes les vidéos sont chargées
        if success_count == 4:
            print("DEBUG: Démarrage automatique de la lecture")
            # Petit délai pour s'assurer que tout est prêt
            self.root.after(100, self.play_videos)
        else:
            if success_count == 0:
                messagebox.showwarning("Erreur", "Aucune vidéo n'a pu être chargée")
            else:
                messagebox.showwarning("Attention", f"Seulement {success_count} vidéo(s) ont pu être chargées sur 4")
    
    def load_videos(self):
        """Charge les 4 vidéos manuellement"""
        self.force_cleanup()
        
        video_files = []
        for i in range(4):
            file_path = filedialog.askopenfilename(
                title=f"Sélectionner la vidéo {i+1}",
                filetypes=[
                    ("Fichiers vidéo", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            if file_path:
                video_files.append(file_path)
            else:
                messagebox.showwarning("Attention", f"Vidéo {i+1} non sélectionnée")
                return
        
        # Initialiser les captures vidéo
        success_count = 0
        for i, file_path in enumerate(video_files):
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                ret, test_frame = cap.read()
                if ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.caps[i] = cap
                    self.selected_videos[i] = file_path
                    self.labels[i].config(text=f"Vidéo {i+1}\nChargée")
                    success_count += 1
                else:
                    cap.release()
                    messagebox.showerror("Erreur", f"La vidéo {i+1} ne contient pas de frames valides")
                    return
            else:
                cap.release()
                messagebox.showerror("Erreur", f"Impossible d'ouvrir la vidéo {i+1}")
                return
        
        if success_count == 4:
            messagebox.showinfo("Succès", "Toutes les vidéos ont été chargées!")
    
    def play_videos(self):
        """Lance la lecture des 4 vidéos"""
        # Vérifier que toutes les captures sont valides
        valid_caps_count = sum(1 for cap in self.caps if cap is not None and cap.isOpened())
        
        if valid_caps_count == 0:
            messagebox.showwarning("Attention", "Aucune vidéo valide n'est chargée")
            return
        
        print(f"DEBUG: Démarrage de la lecture avec {valid_caps_count} vidéos")
        
        if not self.playing:
            self.playing = True
            self.stop_event.clear()
            
            # Créer un nouveau thread pour chaque position vidéo
            with self.thread_lock:
                for i in range(4):
                    if self.caps[i] is not None and self.caps[i].isOpened():
                        thread = threading.Thread(target=self.play_video_safe, args=(i,), daemon=True)
                        thread.start()
                        self.video_threads.append(thread)
                        print(f"DEBUG: Thread {i} démarré")
    
    def play_video_safe(self, video_index):
        """Version thread-safe de la lecture vidéo"""
        cap = self.caps[video_index]
        label = self.labels[video_index]
        
        if cap is None or not cap.isOpened():
            print(f"DEBUG: Capture {video_index} invalide")
            return
        
        print(f"DEBUG: Début de lecture pour vidéo {video_index}")
        frame_count = 0
        
        try:
            while self.playing and not self.stop_event.is_set():
                ret, frame = cap.read()
                
                if ret:
                    frame_count += 1
                    
                    # Redimensionner et afficher le frame
                    try:
                        # Mettre à jour les dimensions du label
                        label.update_idletasks()
                        label_width = label.winfo_width()
                        label_height = label.winfo_height()
                        
                        if label_width > 10 and label_height > 10:
                            # Obtenir les dimensions originales
                            h, w = frame.shape[:2]
                            
                            # Mode crop : redimensionner pour remplir complètement l'espace
                            # en coupant ce qui dépasse pour garder les proportions
                            scale_w = label_width / w
                            scale_h = label_height / h
                            scale = max(scale_w, scale_h)  # Prendre le plus grand facteur
                            
                            # Nouvelles dimensions après mise à l'échelle
                            new_w = int(w * scale)
                            new_h = int(h * scale)
                            
                            if new_w > 0 and new_h > 0:
                                # Redimensionner la frame
                                frame_resized = cv2.resize(frame, (new_w, new_h))
                                
                                # Calculer les coordonnées de crop pour centrer
                                start_x = max(0, (new_w - label_width) // 2)
                                start_y = max(0, (new_h - label_height) // 2)
                                end_x = start_x + label_width
                                end_y = start_y + label_height
                                
                                # Cropper l'image pour qu'elle remplisse exactement le label
                                frame_cropped = frame_resized[start_y:end_y, start_x:end_x]
                                
                                # S'assurer que les dimensions correspondent exactement
                                if frame_cropped.shape[1] != label_width or frame_cropped.shape[0] != label_height:
                                    frame_cropped = cv2.resize(frame_cropped, (label_width, label_height))
                                
                                # Convertir et afficher
                                frame_rgb = cv2.cvtColor(frame_cropped, cv2.COLOR_BGR2RGB)
                                img = Image.fromarray(frame_rgb)
                                photo = ImageTk.PhotoImage(img)
                                
                                # Mise à jour thread-safe
                                if self.playing and not self.stop_event.is_set():
                                    label.config(image=photo, text="")
                                    label.image = photo
                    
                    except Exception as e:
                        print(f"DEBUG: Erreur affichage vidéo {video_index}: {e}")
                        break
                    
                    # Contrôle de la vitesse (30 FPS approximatif)
                    time.sleep(0.033)
                    
                else:
                    # Fin de vidéo - recommencer
                    if self.playing and not self.stop_event.is_set():
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        print(f"DEBUG: Redémarrage vidéo {video_index} (frame {frame_count})")
                        frame_count = 0
                    else:
                        break
                        
        except Exception as e:
            print(f"DEBUG: Erreur dans play_video_safe {video_index}: {e}")
        
        print(f"DEBUG: Fin de lecture pour vidéo {video_index}")
    
    def pause_videos(self):
        """Met en pause les vidéos"""
        print("DEBUG: Pause demandée")
        self.playing = False
    
    def stop_videos(self):
        """Arrête les vidéos et les remet au début"""
        print("DEBUG: Stop demandé")
        self.force_cleanup()
        
        # Restaurer les labels avec les noms de fichiers
        for i in range(4):
            if self.selected_videos[i] is not None:
                filename = os.path.basename(self.selected_videos[i])
                display_name = filename[:25] + ('...' if len(filename) > 25 else '')
                self.labels[i].config(image="", text=f"Vidéo {i+1}\n{display_name}\nArrêtée")
            else:
                self.labels[i].config(image="", text=f"Vidéo {i+1}\nArrêtée")
    
    def on_closing(self):
        """Nettoyage lors de la fermeture"""
        print("DEBUG: Fermeture de l'application")
        self.force_cleanup()
        self.root.destroy()
    
    def run(self):
        """Lance l'application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    # Vérifier si OpenCV est installé
    try:
        import cv2
    except ImportError:
        print("OpenCV n'est pas installé. Installez-le avec: pip install opencv-python")
        exit(1)
    
    # Vérifier si Pillow est installé
    try:
        from PIL import Image, ImageTk
    except ImportError:
        print("Pillow n'est pas installé. Installez-le avec: pip install Pillow")
        exit(1)
    
    # Lancer l'application
    app = QuadVideoPlayer()
    app.run()