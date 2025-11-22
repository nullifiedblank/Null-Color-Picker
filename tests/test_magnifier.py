
import pytest
from PySide6.QtCore import QRect, QPoint
from PySide6.QtGui import QPixmap, QImage, QColor
from main import MagnifierOverlay

class MockScreen:
    def geometry(self):
        return QRect(0, 0, 1920, 1080)

    def grabWindow(self, *args):
        # Return a solid red pixmap
        img = QImage(1920, 1080, QImage.Format_RGB888)
        img.fill(QColor(255, 0, 0))
        return QPixmap.fromImage(img)

class MockQApplication:
    @staticmethod
    def screens():
        return [MockScreen()]

    @staticmethod
    def processEvents():
        pass

@pytest.fixture
def magnifier(monkeypatch):
    # Mock QApplication.screens and processEvents inside MagnifierOverlay
    monkeypatch.setattr("main.QApplication.screens", MockQApplication.screens)
    monkeypatch.setattr("main.QApplication.processEvents", MockQApplication.processEvents)

    # We need a QApplication instance for QWidget to work, but in headless env it might fail
    # if we don't use the 'offscreen' platform or similar.
    # However, since we imported main, it creates a QApplication if __name__ == main.
    # But here we are importing as module.
    # We need to create a QApplication instance if one doesn't exist.
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if not app:
        app = QApplication([], title="Test App")

    overlay = MagnifierOverlay()
    return overlay

def test_snapshot_logic(magnifier):
    # Start the magnifier (takes snapshot)
    # Note: In this headless environment, grabWindow might fail or return black/empty
    # unless we mock it (which we did above).

    magnifier.start()

    assert len(magnifier.screenshots) == 1

    # Test get_color_at
    # We filled it with Red (255, 0, 0)
    r, g, b = magnifier.get_color_at(QPoint(100, 100))
    assert (r, g, b) == (255, 0, 0)

    # Test with sample size > 1 (Average)
    magnifier.set_sample_size(3)
    r, g, b = magnifier.get_color_at(QPoint(100, 100))
    assert (r, g, b) == (255, 0, 0)

    magnifier.stop()
    assert len(magnifier.screenshots) == 0
