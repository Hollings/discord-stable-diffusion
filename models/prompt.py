import json
from random import sample, randint, random

from peewee import *

db = SqliteDatabase('bot.db')


class Prompt(Model):
    prompts = TextField(null=True)  # json list of prompts
    quantity = IntegerField(default=1)
    channel_id = IntegerField()
    message_id = IntegerField()
    seed = IntegerField(default=-1)
    image_paths = TextField(default="[]")
    output_message_id = IntegerField(null=True)
    model = TextField(default="stable-diffusion-v1")
    sampler = TextField(default="Euler a")
    negative_prompt = TextField(default="")
    apply_caption = BooleanField(default=True)
    status = TextField(default="pending")
    steps = IntegerField(default=30)
    height = IntegerField(default=768)
    width = IntegerField(default=768)

    def __repr__(self):
        return self.prompts

    def __str__(self):
        return self.prompts

    class Meta:
        database = db

    def apply_modifiers(self):
        current_char = 1
        added_tags = []
        add_artist = False
        prompt = self.prompts
        add_random_tags = 0
        add_quality_tags = 0

        if "|" in prompt:
            # if "|" is not in between [], it's a modifier
            if not ("[" in prompt and "]" in prompt and prompt.index("[") < prompt.index("|") < prompt.index("]")):
                prompt, self.negative_prompt = str(self.prompts).split("|", 1)

        # load tags.json
        with open('config/tags.json') as tags_file:
            tags = json.load(tags_file)

        while current_char < len(str(prompt)) and prompt[current_char] in "!?+#^$.%{^<":
            if prompt[current_char] == "!":
                self.quantity += 1
            if prompt[current_char] == "?":
                add_random_tags += 1
            if prompt[current_char] == "+":
                self.steps = 75
            if prompt[current_char] == "#":
                self.quantity += 5
            if prompt[current_char] == ".":
                self.apply_caption = False
            if prompt[current_char] == "%":
                self.seed = 69420
            if prompt[current_char] == "^":
                self.height += 128
                self.width -= 128
            if prompt[current_char] == "<":
                self.height -= 128
                self.width += 128
            if prompt[current_char] == "{" and "}" in prompt[current_char + 1:]:
                num_string = ""
                current_char += 1
                while prompt[current_char] != "}":
                    if not prompt[current_char].isdigit():
                        num_string = "69420"
                        break
                    num_string += prompt[current_char]
                    current_char += 1
                self.seed = int(num_string)
            current_char += 1

        self.quantity = min(self.quantity, 5)
        prompt = prompt[current_char:]

        # append the tags to the prompt
        added_tags = []
        if add_quality_tags:
            added_tags.append(sample(tags['quality'], randint(2, 5)))
        if add_random_tags:
            added_tags.append(sample(tags['random'], randint(1, 3)))
        if add_artist:
            added_tags.append(sample(tags['artist'], 1))
        if added_tags:
            prompt += " - " + " ".join([", ".join(tag) for tag in added_tags])
        self.prompts = prompt

    def generate_img_to_txt(self):
        if not self.image_paths:
            return "Prompt has no image"
