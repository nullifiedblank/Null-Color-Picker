
import pytest
from PySide6.QtCore import QRect, QPoint
from PySide6.QtGui import QPixmap, QImage, QColor
from main import MagnifierWindow

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
    def screenAt(point):
        return MockScreen()

    @staticmethod
    def primaryScreen():
        return MockScreen()

    @staticmethod
    def processEvents():
        pass

@pytest.fixture
def magnifier(monkeypatch):
    # Mock QApplication methods used in ScreenSampler
    monkeypatch.setattr("main.QApplication.screenAt", MockQApplication.screenAt)
    monkeypatch.setattr("main.QApplication.primaryScreen", MockQApplication.primaryScreen)

    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if not app:
        app = QApplication([], title="Test App")

    window = MagnifierWindow()
    return window

def test_magnifier_initialization(magnifier):
    # Just verify it initializes without crashing and has correct default size
    assert magnifier.width() == 200
    assert magnifier.height() == 200
    assert magnifier.isVisible() == False

def test_magnifier_update(magnifier):
    # Test update_pos moves the window
    start_pos = QPoint(100, 100)
    magnifier.update_pos(start_pos)

    # It should be offset by 30, 30
    expected_pos = QPoint(130, 130)
    assert magnifier.pos() == expected_pos
