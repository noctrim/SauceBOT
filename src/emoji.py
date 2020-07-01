import re


class Emoji:
    def __init__(self, text, emojis):
        r = re.match(r'(?:\<:([^:]+):([0-9]+)\>)', text)
        if not r:
            self.value = text
            return
        emojis = list(filter(lambda e: str(e.id) == r.group(2), emojis))
        self.value = emojis[0].name

    @classmethod
    def get_mapping(cls, text, emojis):
        mapping = {}
        r = re.search(r'\[([\s\S]*)\]', text)
        if not r:
            return mapping
        input_map = r.group(1).strip()
        lines = input_map.splitlines()
        for line in lines:
            try:
                emoji, role = line.split("-")
                role = role.strip()
                if not any([emoji, role]):
                    break
                emoji = cls(emoji.strip(), emojis)
                mapping[emoji.value] = role
            except Exception as e:
                print("Error: {0} parsing line: {1}".format(e, line))
                continue
        return mapping
