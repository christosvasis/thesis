class SignalBlocker:
    """Context manager to temporarily block Qt signals for widgets."""
    def __init__(self, *widgets):
        self.widgets = widgets

    def __enter__(self):
        for w in self.widgets:
            try:
                w.blockSignals(True)
            except Exception:
                pass
        return self

    def __exit__(self, exc_type, exc, tb):
        for w in self.widgets:
            try:
                w.blockSignals(False)
            except Exception:
                pass
