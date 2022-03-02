from pathlib import Path
import tanjun, logging

class Client(tanjun.Client):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    
    def load_modules(self):
        path = Path("./lib/modules")
        for ext in path.glob(("**/") + "[!_]*.py"): # Loads all but private python files
            super().load_modules(".".join([*ext.parts[:-1], ext.stem]))
            logging.info(f"Loaded {ext} module.")
        return self
