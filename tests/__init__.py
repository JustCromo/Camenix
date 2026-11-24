# i test non toccano mai la vera /var/lib/camenix: la cartella di accesso punta a un percorso inesistente
import os as _os
import tempfile as _tempfile
from camenix import login as _login
_login.DIR = _os.path.join(_tempfile.gettempdir(), "camenix-test-no-login-dir-" + str(_os.getpid()))
