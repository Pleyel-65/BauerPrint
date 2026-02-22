import pygame
import RPi.GPIO as gpio
from pathlib import Path
import os
import time
from datetime import datetime
import re
import asyncio
import logging

SOUNDS = Path('.').absolute().joinpath('sounds')
NO_MESSAGE_SOUND = SOUNDS.joinpath('other/no_message.mp3')
PRE_MESSAGE_SOUND = SOUNDS.joinpath('other/pre_message_beep.mp3')
RING_SOUND = SOUNDS.joinpath('other/ring.mp3')
NEW_MESSAGES_FOLDER = SOUNDS.joinpath('voicemail/new/')
OLD_MESSAGES_FOLDER = SOUNDS.joinpath('voicemail/old/')
logger = logging.getLogger('__main__')
class Phone:
    def __init__(self, phonePin:int = 4):
        gpio.setmode(gpio.BCM)
        gpio.setup(phonePin, gpio.IN)
        self.in_pin = phonePin

        pygame.mixer.pre_init(frequency=44100, buffer=2048)
        pygame.mixer.init()
        pygame.init()
        self.sound = None

        self.is_hung = True
        self.__hang_wait_change_state = 0.5
        self.__time_since_last_hang_change_state = time.time()
        self.__last_gpio_state = True

        self.was_playing_messages = False
        self.current_message = None
        self.new_messages = os.listdir(NEW_MESSAGES_FOLDER)
        self.old_messages = os.listdir(OLD_MESSAGES_FOLDER)
        self.old_messages.sort(reverse=False)


    async def run(self):
        try:
            while True:
                self.changeHangState()
                self.checkNewMessages()
                if not self.is_hung:
                    self.was_playing_messages = True
                    self.readThroughMessages()
                elif self.was_playing_messages:
                    self.was_playing_messages = False
                    self.stopSound()
                    self.current_message = None
                
                await asyncio.sleep(0.1)
        except (Exception, KeyboardInterrupt):
            pass
        finally:
            logger.info("Bye Bye")
            gpio.cleanup()
    
    def readThroughMessages(self):
        # if gpio.input(self.in_pin) and not self.is_hung:
        #     self.stopSound()
        if not self.isPlayingSound():
            self.playSound(PRE_MESSAGE_SOUND, loop=False)
            time.sleep(1.5)
            if self.current_message == None and self.old_messages:
                self.current_message = self.old_messages[-1]
            elif self.current_message == None or (self.old_messages and self.current_message == self.old_messages[0]):
                self.playSound(NO_MESSAGE_SOUND)
                return
            elif self.old_messages:
                self.current_message = self.old_messages[self.old_messages.index(self.current_message) - 1] 

            self.playSound(OLD_MESSAGES_FOLDER.joinpath(self.current_message), loop=False)

    def stopSound(self):
        if self.isPlayingSound():
            self.channel.stop()
            self.sound = None

    def playSound(self, sound:Path=RING_SOUND, force=False, loop=True):
        if self.isPlayingSound() and force:
            self.stopSound()
        
        if not self.isPlayingSound():
            self.sound = pygame.mixer.Sound(sound)
            self.sound.set_volume(1.0)
            loop = -1 if loop else 0
            self.channel = self.sound.play(loops=loop)
            
    def changeHangState(self):
        c_but_state = gpio.input(self.in_pin)
        if c_but_state != self.__last_gpio_state:
            self.__last_gpio_state = c_but_state
            self.__time_since_last_hang_change_state = time.time()
        if self.__time_since_last_hang_change_state > self.__hang_wait_change_state and self.is_hung != c_but_state:
            self.is_hung = c_but_state
            logger.info(f"Hang state changed : {self.is_hung}")


    def removeMessage(self, before: datetime = datetime.min, after: datetime = datetime.max):
        if self.old_messages:
            for msg_name in self.old_messages:
                msg_abs_path = OLD_MESSAGES_FOLDER.joinpath(msg_name)
                # logger.info(msg_name)
                # logger.info(re.search(r'\d{4}([_|-]\d{2}){5}', msg_name))
                receive_date = datetime.strptime(re.search(r'\d{4}([_|-]\d{2}){5}', msg_name).group(0), "%Y-%m-%d_%H-%M-%S")
                if receive_date <= before:
                    os.remove(msg_abs_path)
                    continue
                if receive_date >= after:
                    os.remove(msg_abs_path)

        if os.listdir(OLD_MESSAGES_FOLDER):
            self.old_messages = os.listdir(OLD_MESSAGES_FOLDER)
            self.old_messages.sort(reverse=False)
        else: 
            self.old_messages = []

    async def getNewMessages(self):
        while True:
            self.old_messages = os.listdir(OLD_MESSAGES_FOLDER)
            self.old_messages.sort(reverse=False)
            self.new_messages = os.listdir(NEW_MESSAGES_FOLDER)
            await asyncio.sleep(1)
            # logger.info(f"New Messages : {self.new_messages}")

    def unreadMessage(self, message:Path):
        new_file_name = NEW_MESSAGES_FOLDER.joinpath(f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{re.search(r'(?<=_)\d+$', message.stem).group(0)}{message.suffix}')
        if message.is_file():
            os.rename(message, new_file_name)
            self.old_messages = os.listdir(OLD_MESSAGES_FOLDER)
            self.old_messages.sort(reverse=False)
            self.new_messages = os.listdir(NEW_MESSAGES_FOLDER)
        else:
            logger.info("Cannot find file...")
            

    def checkNewMessages(self):
        if gpio.input(self.in_pin) and self.new_messages:
            self.playSound(RING_SOUND)
        elif self.new_messages:
            self.stopSound()
            for f in self.new_messages:
                new_msg_file = NEW_MESSAGES_FOLDER.joinpath(f)
                os.rename(new_msg_file, OLD_MESSAGES_FOLDER.joinpath(f))


            self.old_messages = os.listdir(OLD_MESSAGES_FOLDER)
            self.old_messages.sort(reverse=False)
            self.new_messages = os.listdir(NEW_MESSAGES_FOLDER)
        # elif self.is_hung:
        #     self.stopSound()


    def isPlayingSound(self):
        return hasattr(self, 'channel') and self.channel.get_busy()
    # def playNewMessage(self):
    #     if not gpio.input(self.in_pin) and not self.isPlayingSound():
    #         if not os.listdir(NEW_MESSAGES_FOLDER):

if __name__ == "__main__":
    phone = Phone()
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(phone.getNewMessages())
    loop.create_task(phone.run())
    loop.run_forever()
    # while True:
    #     phone.hangUp()
    #     phone.playNewMessage()
    #     time.sleep(0.1)