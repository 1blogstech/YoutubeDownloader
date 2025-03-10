import os
import platform
import threading
import yt_dlp
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from tkinter.filedialog import askdirectory


class YouTubeDownloader(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.selected_folder = ""  # Store chosen download folder

        self.url_input = TextInput(hint_text="Enter YouTube URL", size_hint=(1, 0.1))
        self.add_widget(self.url_input)

        self.choose_folder_button = Button(text="Choose Folder", size_hint=(1, 0.2))
        self.choose_folder_button.bind(on_press=self.open_filechooser)
        self.add_widget(self.choose_folder_button)

        self.download_button = Button(text="Download", size_hint=(1, 0.2))
        self.download_button.bind(on_press=self.start_download)
        self.add_widget(self.download_button)

        self.progress_label = Label(text="Progress: 0%", size_hint=(1, 0.1))
        self.add_widget(self.progress_label)

        self.progress_bar = ProgressBar(max=100, size_hint=(1, 0.1))
        self.add_widget(self.progress_bar)

    def get_root_path(self):
        """Return the appropriate root path based on the platform."""
        if platform.system() == "Windows":
            return None  # Start from C: to access "This PC"
        elif platform.system() == "Android":
            return "/storage/emulated/0/"  # Default user-accessible storage
        else:
            return None # Root for Linux/macOS

    def open_filechooser(self, instance):
        """Open file chooser dialog with platform-specific root directory."""
        content = BoxLayout(orientation="vertical")

        path = self.get_root_path()
        if path != None:
            filechooser = FileChooserListView(path=self.get_root_path(), dirselect=True)
            content.add_widget(filechooser)

            def select_folder(instance):
                if filechooser.selection:
                    self.selected_folder = filechooser.selection[0]
                    popup.dismiss()

            select_button = Button(text="Select", size_hint=(1, 0.2))
            select_button.bind(on_press=select_folder)
            content.add_widget(select_button)

            popup = Popup(title="Choose Download Folder", content=content, size_hint=(0.9, 0.9))
            popup.open()
        else:
            self.selected_folder = askdirectory(title="Choose Download Folder")

    def start_download(self, instance):
        """Start the video download."""
        video_url = self.url_input.text.strip()
        if not video_url:
            self.progress_label.text = "Please enter a valid URL!"
            return

        if not self.selected_folder:
            self.progress_label.text = "Please choose a folder first!"
            return

        self.download_button.disabled = True  # Disable button while downloading
        self.progress_label.text = "Starting download..."

        # Start download in a separate thread
        threading.Thread(target=self.download_video, args=(video_url,), daemon=True).start()

    def download_video(self, url):
        """Download video and update progress bar."""
        def progress_hook(d):
            if d['status'] == 'downloading':
                total_size = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
                downloaded = d.get('downloaded_bytes', 0)
                progress = int((downloaded / total_size) * 100)

                # Update UI on the main thread
                self.progress_label.text = f"Progress: {progress}%"
                self.progress_bar.value = progress

            elif d['status'] == 'finished':
                self.progress_label.text = "Download complete!"
                self.progress_bar.value = 100
                self.download_button.disabled = False  # Re-enable button

        # Set download path dynamically
        output_template = os.path.join(self.selected_folder, "%(title)s.%(ext)s")

        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'progress_hooks': [progress_hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])


class YouTubeApp(App):
    def build(self):
        self.title = "Youtube Downloader"
        self.icon = "setting.ico"
        return YouTubeDownloader()


if __name__ == "__main__":
    YouTubeApp().run()
