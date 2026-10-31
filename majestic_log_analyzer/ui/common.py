from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import (
    QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QLabel,
    QWidget,
)

from ..style import theme_tokens


def section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("SectionLabel")
    return lbl


def card_frame() -> QFrame:
    frame = QFrame()
    frame.setObjectName("Card")
    return frame


def _icon_pixmap(name: str, color: str, size: int) -> QPixmap:
    scale = 2
    pm = QPixmap(size * scale, size * scale)
    pm.setDevicePixelRatio(scale)
    pm.fill(Qt.transparent)

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(size / 18.0, size / 18.0)

    pen = QPen(QColor(color), 1.45, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if name == "analysis":
        painter.drawEllipse(QRectF(3.2, 3.2, 9.4, 9.4))
        painter.drawLine(11.3, 11.3, 15.0, 15.0)
        painter.drawLine(5.8, 8.0, 7.6, 9.8)
        painter.drawLine(7.6, 9.8, 10.4, 6.2)
    elif name == "rules":
        painter.drawLine(3.5, 5.0, 14.5, 5.0)
        painter.drawLine(3.5, 9.0, 14.5, 9.0)
        painter.drawLine(3.5, 13.0, 14.5, 13.0)
        painter.setBrush(QColor(color))
        painter.drawEllipse(QRectF(6.2, 3.4, 3.2, 3.2))
        painter.drawEllipse(QRectF(10.2, 7.4, 3.2, 3.2))
        painter.drawEllipse(QRectF(4.6, 11.4, 3.2, 3.2))
    elif name == "notes":
        path = QPainterPath()
        path.moveTo(4.5, 2.8)
        path.lineTo(11.0, 2.8)
        path.lineTo(14.2, 6.0)
        path.lineTo(14.2, 15.2)
        path.lineTo(4.5, 15.2)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(11.0, 2.8, 11.0, 6.0)
        painter.drawLine(11.0, 6.0, 14.2, 6.0)
        painter.drawLine(6.6, 9.0, 12.0, 9.0)
        painter.drawLine(6.6, 11.7, 12.0, 11.7)
    elif name == "exceptions":
        path = QPainterPath()
        path.moveTo(9.0, 2.6)
        path.lineTo(14.4, 4.8)
        path.lineTo(14.4, 8.7)
        path.cubicTo(14.4, 12.0, 12.2, 14.3, 9.0, 15.5)
        path.cubicTo(5.8, 14.3, 3.6, 12.0, 3.6, 8.7)
        path.lineTo(3.6, 4.8)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(6.4, 9.0, 11.6, 9.0)
    elif name == "moon":
        path = QPainterPath()
        path.moveTo(11.9, 3.2)
        path.cubicTo(8.0, 4.0, 5.6, 7.1, 6.2, 10.5)
        path.cubicTo(6.8, 13.8, 9.8, 15.6, 13.2, 14.8)
        path.cubicTo(10.6, 13.2, 9.4, 10.0, 10.5, 7.2)
        path.cubicTo(10.9, 5.8, 11.5, 4.5, 11.9, 3.2)
        path.closeSubpath()
        painter.drawPath(path)
    elif name == "sun":
        painter.drawEllipse(QRectF(6.3, 6.3, 5.4, 5.4))
        for x1, y1, x2, y2 in (
            (9.0, 1.9, 9.0, 3.5), (9.0, 14.5, 9.0, 16.1),
            (1.9, 9.0, 3.5, 9.0), (14.5, 9.0, 16.1, 9.0),
            (4.0, 4.0, 5.2, 5.2), (12.8, 12.8, 14.0, 14.0),
            (4.0, 14.0, 5.2, 12.8), (12.8, 5.2, 14.0, 4.0),
        ):
            painter.drawLine(x1, y1, x2, y2)
    elif name == "help":
        painter.drawEllipse(QRectF(2.7, 2.7, 12.6, 12.6))
        font = QFont("Segoe UI")
        font.setPixelSize(9)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(
            QRectF(2.7, 2.5, 12.6, 12.6), Qt.AlignCenter, "?"
        )
    elif name == "folder":
        path = QPainterPath()
        path.moveTo(2.8, 5.2)
        path.lineTo(7.0, 5.2)
        path.lineTo(8.4, 6.8)
        path.lineTo(15.2, 6.8)
        path.lineTo(15.2, 14.0)
        path.lineTo(2.8, 14.0)
        path.closeSubpath()
        painter.drawPath(path)
    elif name == "plus":
        painter.drawLine(9.0, 3.4, 9.0, 14.6)
        painter.drawLine(3.4, 9.0, 14.6, 9.0)
    elif name == "trash":
        painter.drawLine(3.8, 5.2, 14.2, 5.2)
        painter.drawLine(7.2, 3.2, 10.8, 3.2)
        painter.drawRect(QRectF(5.0, 5.2, 8.0, 9.6))
        painter.drawLine(7.2, 7.4, 7.2, 12.6)
        painter.drawLine(10.8, 7.4, 10.8, 12.6)
    elif name == "refresh":
        path = QPainterPath()
        path.arcMoveTo(QRectF(3.4, 3.4, 11.2, 11.2), 35)
        path.arcTo(QRectF(3.4, 3.4, 11.2, 11.2), 35, 285)
        painter.drawPath(path)
        painter.drawLine(14.2, 4.0, 14.4, 7.4)
        painter.drawLine(14.4, 7.4, 11.0, 7.2)
    elif name == "download":
        painter.drawLine(9.0, 2.8, 9.0, 11.5)
        painter.drawLine(5.7, 8.4, 9.0, 11.7)
        painter.drawLine(12.3, 8.4, 9.0, 11.7)
        painter.drawLine(3.4, 14.4, 14.6, 14.4)
    elif name == "close":
        painter.drawLine(5.0, 5.0, 13.0, 13.0)
        painter.drawLine(13.0, 5.0, 5.0, 13.0)
    else:
        painter.drawEllipse(QRectF(5.0, 5.0, 8.0, 8.0))

    painter.end()
    return pm


def make_icon(name: str, color: str, size: int = 18) -> QIcon:
    return QIcon(_icon_pixmap(name, color, size))


def make_state_icon(
    name: str,
    normal_color: str,
    active_color: str,
    size: int = 18,
) -> QIcon:
    icon = QIcon()
    for mode in (QIcon.Normal, QIcon.Active):
        icon.addPixmap(
            _icon_pixmap(name, normal_color, size), mode, QIcon.Off
        )
        icon.addPixmap(
            _icon_pixmap(name, active_color, size), mode, QIcon.On
        )
    icon.addPixmap(
        _icon_pixmap(name, "#6F747E", size), QIcon.Disabled, QIcon.Off
    )
    return icon


def fade_in(widget: QWidget, duration: int = 160, delay: int = 0) -> None:
    previous = getattr(widget, "_fade_animation", None)
    if previous is not None:
        previous.stop()

    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

    effect.setOpacity(0.0)
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.OutCubic)
    animation.setParent(widget)
    widget._fade_animation = animation

    def _finish() -> None:
        if widget.graphicsEffect() is effect:
            widget.setGraphicsEffect(None)
        widget._fade_animation = None

    animation.finished.connect(_finish)

    if delay:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(delay, animation.start)
    else:
        animation.start()


def apply_shadow(widget: QWidget, blur: int = 36, offset: int = 10, alpha: int = 90) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


class BrandMark(QWidget):
    def __init__(self, size: int = 38, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, _event) -> None:
        app = QApplication.instance()
        theme = app.property("theme") if app else "dark"
        tokens = theme_tokens(theme or "dark")
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(tokens["accent"]))
        painter.drawRoundedRect(rect, 10, 10)

        w = rect.width()
        h = rect.height()
        mark = QPainterPath()
        mark.moveTo(w * 0.27, h * 0.70)
        mark.lineTo(w * 0.27, h * 0.32)
        mark.lineTo(w * 0.50, h * 0.55)
        mark.lineTo(w * 0.73, h * 0.32)
        mark.lineTo(w * 0.73, h * 0.70)

        pen = QPen(
            QColor("#FFFFFF"),
            max(1.8, w * 0.065),
            Qt.SolidLine,
            Qt.RoundCap,
            Qt.RoundJoin,
        )
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(mark)
        painter.end()
