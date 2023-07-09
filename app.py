import logging
import datetime as dt
from PIL import Image, ImageFont, ImageDraw
import json
import requests
import sys
import os
import epaper

logging.basicConfig(level=logging.DEBUG)

class JsonHandler:
    """Handles the JSON body from the todo api"""
    @staticmethod
    def parse_json(json_data):
        try:
            return json.loads(json_data)
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON: {e}")
            return {}

class ImageDrawer:
    """Class for drawing stuff using the pillow draw object."""
    LINE_WIDTH = 15
    STARTING_CURSOR_LOC = (15, 5)

    def __init__(self, draw):
        self.current_cursor_loc = self.STARTING_CURSOR_LOC
        self.linewidth = self.LINE_WIDTH
        self.draw = draw

    def write_title(self, title_text, font):
        self.write(title_text, font)
        self.increment_cursor_loc(increment_y=15)

    def write_todo(self, todo_dict, font):
        """
        Writes a single todo onto the screen and crosses it out if it's been done.
        Moves the current cursor location to the next line.
        """
        text = self.generate_todo_text(todo_dict)
        text_width, text_height = self.draw.textsize(text, font=font)
        self.write(text, font)
        if todo_dict.get("doneDate") == "None": 
            self.cross_out_todo_text(text_height, text_width)
        self.increment_cursor_loc(increment_y=self.linewidth)

    @staticmethod
    def generate_todo_text(todo_dict):
        """
        Formats each todo item ready for the display.
        """
        return f"- {todo_dict.get('name')}"

    def cross_out_todo_text(self, text_height, text_width):
        """
        Crosses out a todo item given the height and width of the printed text.
        """
        line_y = (text_height // 2) + 2
        self.draw.line((self.current_cursor_loc[0], line_y + self.current_cursor_loc[1], self.current_cursor_loc[0] + text_width, line_y + self.current_cursor_loc[1]), fill=0)

    def write(self, text, font):
        """
        Writes something on the screen at the current cursor location.
        """
        self.draw.text(self.current_cursor_loc, text, fill=0, font=font)

    def increment_cursor_loc(self, increment_y):
        """
        Increments the y value of the current cursor location by `increment_y`.
        """
        self.current_cursor_loc = (self.current_cursor_loc[0], self.current_cursor_loc[1] + increment_y)

    def draw_quote(self, font):
        """
        Draws a quote on the right hand side of the display.
        """
        # self.draw.rectangle([(250, 10), (470, 270)])
        response = requests.get("https://zenquotes.io/api/today").json()[0]
        quote_words= response.get("q").split(" ")
        
        lines = []
        cur_line = ""
        while quote_words:
            while len(cur_line) < 15 and quote_words:
                if quote_words:
                    cur_line += quote_words.pop(0) + " "
            lines.append(cur_line)
            cur_line = ""

        quote_y = 100
        for line in lines:
            self.draw.text((255, quote_y), line, font=font) 
            quote_y += 10

class ToDoListDisplay:
    TODAY = dt.date.today()
    TOMORROW = TODAY + dt.timedelta(days=1)
    RESOURCES_PATH = "resources"
    TITLE_FONT_PATH = os.path.join(RESOURCES_PATH, "MozartNbp.ttf")
    FONT_PATH = os.path.join(RESOURCES_PATH, "MozartNbp.ttf")
    QUOTE_FONT_PATH = os.path.join(RESOURCES_PATH, "WayfarersToyBoxRegular.ttf")
    LINE_WIDTH = 15
    EPD_DISPLAY_DIMS = (480, 280)

    def __init__(self, todos_json):
        self.today = self.TODAY
        self.tomorrow = self.TOMORROW
        self.todos_json = todos_json
        self.todos = JsonHandler.parse_json(self.todos_json)
        
        self.epd_display_dims = self.EPD_DISPLAY_DIMS
        self.title_font = ImageFont.truetype(self.TITLE_FONT_PATH, 22)
        self.font = ImageFont.truetype(self.FONT_PATH, 20)
        self.quote_font = ImageFont.truetype(self.QUOTE_FONT_PATH, 8)
        self.display = Image.new("L", self.EPD_DISPLAY_DIMS, 0xFF)
        self.draw = ImageDraw.Draw(self.display)
        self.image_drawer = ImageDrawer(self.draw)
        self.linewidth = self.image_drawer.linewidth

    def build_todo_list(self):
        """
        Uses the ImageDrawer class to draw the todo list for all items in `self.todos`.
        """
        [   
            [self.image_drawer.write_title(f"To do {'today' if str(self.today) == date else date}", self.title_font), 
            [self.image_drawer.write_todo(todo, self.font) for todo in todos]]
            for date, todos in self.todos.items()
        ]
        self.image_drawer.draw_quote(self.quote_font)

    def get_display(self):
        return self.display

    def send_to_epd(self):
        """
        Sends the current display to the epaper display.
        """
        rotated_display = self.display.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
        self.epd = epaper.epaper('epd3in7').EPD()
        self.epd.init(0)
        self.epd.Clear(0xFF, 0)
        self.epd.display_1Gray(self.epd.getbuffer(rotated_display))

if __name__ == "__main__":

    try:
        response = requests.get("http://192.168.0.4:5000/api/v1/users/1/todos?horizon=2")
        # logging.info(response.content)
        display = ToDoListDisplay(response.content)
        display.build_todo_list()
        display.send_to_epd()
    except Exception as e:
        logging.info(e)