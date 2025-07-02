
from utilts import ScheduleManager, get_serial, time_to_cron
import requests, json, time, subprocess, os
from threading import Thread, Event
from queue import Queue
from functools import partial

from config import *


class Setting:
    def __init__(self, name: str, value, func=None):
        """
        Initialize the setting object.

        :param name: The name of the setting.
        :param value: The initial value of the setting.
        :param apply_callback: A callback function to run when the setting is updated.
        """
        self._name = name
        self._value = value
        self._apply_callback = None if func is None else partial(func)  # New test partial function for callback

    @property
    def name(self):
        """Get the name of the setting."""
        return self._name

    @property
    def value(self):
        """Get the value of the setting."""
        return self._value

    @value.setter
    def value(self, new_value):
        """Set the value of the setting and apply the changes if the value is different."""
        if self._value != new_value:
            self._value = new_value
            if self._apply_callback:
                self._apply_callback(self)

    def set_apply_callback(self, callback):
        """
        Set the apply callback function.

        :param callback: A callback function to run when the setting is updated.
        """
        self._apply_callback = callback


class PlayerSettings:
    def __init__(self):
        """
        Initialize the PlayerSettings object with an empty dictionary of settings.
        """
        self._settings = {}

    def get_settings(self) -> dict:
        """Get all player settings"""
        return self._settings

    def add_setting(self, name, value, func=None):
        """
        Add a new setting to the player settings.

        :param name: The name of the setting.
        :param value: The initial value of the setting.
        :param apply_callback: A callback function to run when the setting is updated.
        """
        self._settings[name] = Setting(name, value, func)

    def get_setting(self, name):
        """
        Get the value of a setting by name.

        :param name: The name of the setting.
        :return: The value of the setting.
        """
        setting = self._settings.get(name)
        if setting:
            return setting.value
        else:
            raise KeyError(f"Setting '{name}' not found.")

    def update_setting(self, name, new_value):
        """
        Update the value of an existing setting.

        :param name: The name of the setting.
        :param new_value: The new value of the setting.
        """
        if name in self._settings:
            self._settings[name].value = new_value
        else:
            raise KeyError(f"Setting '{name}' not found.")


class Display:
    COMMAND = "chromium-browser --kiosk --incognito --noerrdialogs --disable-infobars --fast --disable-translate --disable-pinch --fast-start "

    def __init__(self):
        self.browser_process = None
        self.switch_tabs_interval = [Setting(name="switch_tab_interval", value=10)]     # use list so that switch tabs thread can "see" changes
        self.setup_display()
        self.switch_tabs_event = Event()
        self.switch_tabs_thread = Thread(target=self.switch_tabs, args=(self.switch_tabs_event, self.switch_tabs_interval,))

    def update_switch_tab_interval(self, new_interval: Setting):
        print(f"new switch_tab_interval applied: {new_interval.value}")
        self.switch_tabs_interval[0] = new_interval


    def setup_display(self, rotation=None):
        subprocess.run(["xset", "-dpms"])
        subprocess.run(["xset", "s", "off"])
        subprocess.run(["xset", "s", "noblank"])
        #subprocess.Popen(["unclutter", "-idle", "1"])

        width = os.getenv('WIDTH', '1920')
        height = os.getenv('HEIGHT', '1080')

        self.COMMAND = f"chromium-browser --kiosk --window-size={width},{height} --start-fullscreen --incognito --noerrdialogs --disable-infobars --fast --disable-translate --disable-pinch --fast-start "

        if rotation:
            subprocess.run(["xrandr", "--output", "HDMI-1", "--rotate", rotation])

    def exit_chromium(self):
        command = "pkill chromium-browser"
        subprocess.Popen(command, shell=True)
        subprocess.run(["sed", "-i", 's/"exited_cleanly":false/"exited_cleanly":true/', '~/.config/chromium/Default/Preferences'])
        subprocess.run(["sed", "-i", 's/"exit_type":"Crashed"/"exit_type":"Normal"/', '~/.config/chromium/Default/Preferences'])

    def open_url(self, urls: list[str]):
        if len(urls) == 1:
            command = self.COMMAND + urls[0]
            self.browser_process = subprocess.Popen(command, shell=True)
            self.switch_tabs_event.set()
        else:
            urls_string = " ".join(urls)
            command = self.COMMAND + urls_string
            self.browser_process = subprocess.Popen(command, shell=True)
            self.switch_tabs_event.clear()

    def switch_tabs(self, stop_event: Event, setting: list[Setting]):
        command = ["xdotool", "key", "ctrl+Tab"]
        while not stop_event.is_set():
            subprocess.run(command)
            print(f"inside switch_tab: {setting[0].value}")
            time.sleep(setting[0].value)

    def display_content(self, url_queue: Queue):
        urls = []
        while not url_queue.empty():
            urls.append(url_queue.get())
        if urls:
            if self.browser_process:
                try:
                    self.exit_chromium()
                except Exception as e:
                    print(f"Error closing browser: {e}")
            self.open_url(urls)

    def manage_display(self, url_queue):
        self.switch_tabs_thread.start()
        while True:
            self.display_content(url_queue)
            time.sleep(1)




class Player:
    ON_COMMAND = "/bin/bash -c 'echo \"on 0\" | cec-client -s -d 1 && DISPLAY=:0 xset -dpms'"
    OFF_COMMAND = "/bin/bash -c 'echo \"standby 0\" | cec-client -s -d 1 && DISPLAY=:0 xset dpms force off'"
    
    def __init__(self, serlver_url: str, port: int):
        """
        Initialize the Player object.
        """
        self._serial = get_serial()
        self._server_url = f"{serlver_url}:{port}"
        self._settings = PlayerSettings()
        self._display = Display()
        self._schedule_manager = ScheduleManager()
        self._url_queue = Queue()

        # Initial settings configuration
        self.configure_initial_settings()

        # Threads to complete player tasks
        self._display_thread = Thread(target=self.display.manage_display, args=(self.url_queue,), daemon=True)
        self._polling_thread = Thread(target=self.poll_server, daemon=True)

    def schedule_updator(self, setting: Setting):
        match setting.name:
            case "on_time":
                self.schedule_manager.update_schedule_job(self.ON_COMMAND, time_to_cron(setting.value))
            case "off_time":
                self.schedule_manager.update_schedule_job(self.OFF_COMMAND, time_to_cron(setting.value))
        
    def configure_initial_settings(self):
        time = "08:00"
        self.settings.add_setting(name="on_time",value=time, func=self.schedule_updator)
        time = "16:00"
        self.settings.add_setting(name="off_time",value=time, func=self.schedule_updator)
        self.settings.add_setting(name="player_name", value=PLAYER_NAME)
        self.settings.add_setting(name="description", value=DESCRIPTION)
        self.settings.add_setting(name="switch_tab_interval", value=10, func=self.display.update_switch_tab_interval)
        self.settings.add_setting(name="poll_interval", value=POLL_INTERVAL)

    @property
    def settings(self):
        """Get the player's settings."""
        return self._settings
    
    @property
    def schedule_manager(self):
        """Get the player's schedule manager"""
        return self._schedule_manager
    
    @property
    def display(self):
        """Get the players Display"""
        return self._display
    
    @property
    def url_queue(self):
        """Get player url queue"""
        return self._url_queue
    
    @property
    def serial(self):
        """Get Player serial"""
        return self._serial
    
    @property
    def server_url(self):
        """Get Server url"""
        return self._server_url
    
    
    def register_player_attempt(self):
        try:
            name = self.settings.get_setting("player_name")
            description = self.settings.get_setting("description")

            data = {"name": name,
                    "description": description,
                    "serial": f"{self.serial}"
                    }
            headers = {"Content-Type": "application/json"}
            response = requests.post(f"{self.server_url}/register", data=json.dumps(data), headers=headers)
            if response.status_code == 201:
                print("Client registered")
                return True
            else:
                print("Client registeration failed")
                return False
        except Exception as e:
            print("Error registering client:", e)
            return False
        
    def register_player(self):
        while not self.register_player_attempt():
            time.sleep(REGISTRATION_RETRY_INTERVAL)

    def poll_urls(self) -> set[any] | None:
        data = {"serial": self.serial}
        headers = {"Content-Type": "application/json"}

        response = requests.get(f"{self.server_url}/playlist", data=json.dumps(data), headers=headers)

        if response.status_code == 200:
            urls = set(response.json())
            return urls
        return None
    
    def poll_settings(self) -> set[any] | None:
        data = {"serial": self.serial}
        headers = {"Content-Type": "application/json"}

        response = requests.get(f"{self.server_url}/settings", data=json.dumps(data), headers=headers)

        if response.status_code == 200:
            settings = set(response.json().items())
            return settings
        return None

    def ping_server(self):
        data = {"serial": f"{self.serial}"}
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{self.server_url}/ping", data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            print("Ping success")
        else:
            print("Ping failed")

    def poll_server(self):
        previous_urls = set()

        while True:
            try:
                polled_urls = self.poll_urls()
                if polled_urls != previous_urls:
                    for url in polled_urls:
                        self.url_queue.put(url)
                    previous_urls = polled_urls
            except Exception as e:
                print(f"Error getting url: {e}")

            try:
                polled_settings = self.poll_settings()
                if polled_settings:
                    for name, value in polled_settings:
                        self.settings.update_setting(name=name, new_value=value)
            except Exception as e:
                print(f"Error polling settings: {e}")

            try:
                self.ping_server()
            except Exception as e:
                print(f"Error pinging server: {e}")

            poll_interval = self.settings.get_setting(name="poll_interval")
            time.sleep(poll_interval)

    
    def run(self):
        """Run the player application"""
        self.register_player()

        # start player job threads
        self._display_thread.start()
        self._polling_thread.start()

        # Keep main thread alive
        while True:
            time.sleep(1)
    