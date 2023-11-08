from textual.app import App
from textual.widgets import Label

TEXT = """I must not fear.
Fear is the mind-killer.
Fear is the little-death that brings total obliteration.
I will face my fear.
I will permit it to pass over me and through me.
And when it has gone past, I will turn the inner eye to see its path.
Where the fear has gone there will be nothing. Only I will remain.
"""


class Scrollbar2App(App):
    CSS_PATH = "scrollbars2.tcss"

    def compose(self):
        yield Label(TEXT * 10)


if __name__ == "__main__":
    app = Scrollbar2App()
    app.run()
