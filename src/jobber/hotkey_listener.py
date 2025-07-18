import keyboard
import pyperclip
import asyncio
import time
import threading
from resume_tailor import ResumeTailor
from file_handler import FileHandler

"TODO: Add a delay inbetween hotkey presses to prevent accidental double-triggering"

class HotkeyListener:
    def __init__(self):
        self.hotkeys = {}  # Filled in after loading config
        self.rt = None
        self.running = True
        self.loop = asyncio.get_event_loop()
        self.f_handler = FileHandler()

    @classmethod
    async def create(cls):
        instance = cls()
        jackie_resume = await instance.f_handler.load_resume_data_async("jackie_ling_data.json")
        resume_template = await instance.f_handler.load_resume_template_async("default_resume_template.html")
        instance.rt = await ResumeTailor.set_scraper(jackie_resume, resume_template)

        hotkey_map = await instance.f_handler.load_hotkey_config_async()
        instance.hotkeys = {
            combo: getattr(instance, method_name, instance.unsupported_hotkey_handler)
            for combo, method_name in hotkey_map.items()
        }
        return instance

    async def listen(self):
        print("🎧 Hotkeys active:")
        for combo in self.hotkeys:
            print(f"  - {combo}")
            keyboard.add_hotkey(combo, self.hotkeys[combo])
        keyboard.add_hotkey('esc', self.stop)

        while self.running:
            await asyncio.sleep(0.1)


    def stop(self):
        print("Stopping listener.")
        self.running = False
        keyboard.unhook_all_hotkeys()

    def on_tailor_resume_hotkey(self):
        keyboard.send('ctrl+c')
        time.sleep(0.1)  # Slight delay to let clipboard catch up
        clipboard_content = pyperclip.paste()
        print("Tailoring resume for: ", clipboard_content)
        if self.rt:
            asyncio.run_coroutine_threadsafe(
                self.rt.generate_tailored_resume_async(clipboard_content),
                self.loop
            )
        else:
            print("ResumeTailor not initialized.")

    def on_save_pdf_hotkey(self):
        print("Saving PDF...")
        if self.rt:
            asyncio.run_coroutine_threadsafe(
                self.f_handler.generate_pdf_async(dir_name=self.rt.most_recent_output_dir,
                                                    output_name=self.rt.resume_pdf_file_name),
                self.loop
            )
        else:
            print("Unable to save pdf: ResumeTailor not initialized.")

        

    def unsupported_hotkey_handler(self):
        print("⚠️ This hotkey is mapped to an undefined handler.")
