import logging
import datetime as dt
from PIL import Image, ImageFont, ImageDraw
import json
import requests
import sys
import os

logging.basicConfig(level=logging.DEBUG)

class JsonHandler:
    @staticmethod
    def parse_json(json_data):
        try:
            return json.loads(json_data)
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON: {e}")
            return {}

class ImageDrawer:
    LINE_WIDTH = 15

    def __init__(self, draw):
        self.current_cursor_loc = (15, 5)
        self.linewidth = ImageDrawer.LINE_WIDTH
        self.draw = draw

    def write_title(self, title_text, font):
        self.write(title_text, font)
        self.increment_cursor_loc(increment_y=15)

    def write_todo(self, todo_dict, font):
        text = self.generate_todo_text(todo_dict)
        text_width, text_height = self.draw.textsize(text, font=font)
        self.write(text, font)
        if not todo_dict.get("doneDate"):
            self.cross_out_todo_text(text_height, text_width)
        self.increment_cursor_loc(increment_y=self.linewidth)

    @staticmethod
    def generate_todo_text(todo_dict):
        return f"- {todo_dict.get('name')}"

    def cross_out_todo_text(self, text_height, text_width):
        line_y = (text_height // 2) + 2
        self.draw.line((self.current_cursor_loc[0], line_y + self.current_cursor_loc[1], self.current_cursor_loc[0] + text_width, line_y + self.current_cursor_loc[1]), fill=0)

    def write(self, text, font):
        self.draw.text(self.current_cursor_loc, text, fill=0, font=font)

    def increment_cursor_loc(self, increment_y):
        self.current_cursor_loc = (self.current_cursor_loc[0], self.current_cursor_loc[1] + increment_y)


class ToDoListDisplay:
    TODAY = dt.date.today()
    TOMORROW = TODAY + dt.timedelta(days=1)
    RESOURCES_PATH = "resources"
    TITLE_FONT_PATH = os.path.join(RESOURCES_PATH, "MozartNbp.ttf")
    FONT_PATH = os.path.join(RESOURCES_PATH, "MozartNbp.ttf")
    QUOTE_FONT_PATH = os.path.join(RESOURCES_PATH, "WayfarersToyBoxRegular.ttf")
    LINE_WIDTH = 15
    EPD_DISPLAY_DIMS = (480, 280)


    def __init__(self, todos_json, test=False):
        self.today = self.TODAY
        self.tomorrow = self.TOMORROW
        if test:
            self.todos_json = json.dumps({
                str(self.today): [{"name": "wani kani", "doneDate": None}]
            })
        else:
            self.todos_json = todos_json

        if self.todos_json:
            self.todos = JsonHandler.parse_json(self.todos_json)
            
            self.epd_display_dims = self.EPD_DISPLAY_DIMS
            self.title_font = ImageFont.truetype(self.TITLE_FONT_PATH, 20)
            self.font = ImageFont.truetype(self.FONT_PATH, 18)
            self.quote_font = ImageFont.truetype(self.QUOTE_FONT_PATH, 6)
            self.display = Image.new("L", self.EPD_DISPLAY_DIMS, 0xFF)
            self.draw = ImageDraw.Draw(self.display)
            self.image_drawer = ImageDrawer(self.draw)
            self.linewidth = self.image_drawer.linewidth
                
        else:
            logging.info("No response received, not refreshing display")
    
    def draw_quote(self):
        self.draw.rectangle([(250, 10), (470, 270)])
        response = requests.get("https://zenquotes.io/api/today").json()[0]
        quote_words= response.get("q").split(" ")
        
        lines = []
        cur_line = ""
        while quote_words:
            while len(cur_line) < 25 and quote_words:
                if quote_words:
                    cur_line += quote_words.pop(0) + " "
            lines.append(cur_line)
            cur_line = ""

        quote_y = 15
        for line in lines:
            self.draw.text((255, quote_y), line, font=self.quote_font) 
            quote_y += 10

    def build_todo_list_display(self):
        [   
            [self.image_drawer.write_title(f"To do {'today' if str(self.today) == date else date}", self.title_font), 
            [self.image_drawer.write_todo(todo, self.font) for todo in todos]]
            for date, todos in self.todos.items()
        ]

    def get_display(self):
        return self.display

    def show_display(self):
        rotated_display = self.display.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
        self.epd = None # TODO set epd
        self.epd.init(0)
        self.epd.Clear(0xFF, 0)
        self.epd.display_1Gray(self.epd.getbuffer(rotated_display))

if __name__ == "__main__":

    try:
        display = ToDoListDisplay("", test=True)
        display.build_todo_list_display()
        # display.draw_quote()
        display.get_display().show()
        # display = ToDoListDisplay(sys.argv[1])
        # display.show()
    except Exception as e:
        logging.info(e)