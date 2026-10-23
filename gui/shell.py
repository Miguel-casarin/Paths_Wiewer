import queue

que_shell = queue.Queue()

def log_shell(msg, nivel="info"):
    """Qualquer módulo (process, run, utils...) chama isso."""
    que_shell.put((nivel, str(msg)))

def return_que_shell():
    return que_shell