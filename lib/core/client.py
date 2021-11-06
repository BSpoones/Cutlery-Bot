from pathlib import Path
import hikari, tanjun


class Client(tanjun.Client):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    
    def load_modules(self):
        path = Path("./lib/modules")
        for ext in path.glob(("**/") + "[!_]*.py"):
            super().load_modules(".".join([*ext.parts[:-1], ext.stem]))
            print("loaded",ext)
        return self
