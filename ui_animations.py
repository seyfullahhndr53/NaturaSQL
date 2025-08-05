
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, pyqtSignal, QTimer
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget
from PyQt6.QtGui import QColor

class AnimationManager:
    """UI animasyonlarını yöneten sınıf"""
    
    def __init__(self):
        self.animations = []
    
    def fade_in(self, widget, duration=300):
        """Widget'ı fade in efektiyle göster"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        animation.start()
        self.animations.append(animation)
        return animation
    
    def fade_out(self, widget, duration=300):
        """Widget'ı fade out efektiyle gizle"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        animation.start()
        self.animations.append(animation)
        return animation
    
    def slide_in_from_left(self, widget, duration=400):
        """Widget'ı soldan kaydırarak getir"""
        original_pos = widget.pos()
        start_pos = original_pos
        start_pos.setX(start_pos.x() - widget.width())
        widget.move(start_pos)
        
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(original_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutQuart)
        
        animation.start()
        self.animations.append(animation)
        return animation
    
    def bounce_in(self, widget, duration=600):
        """Widget'ı bounce efektiyle göster"""
        original_size = widget.size()
        
        widget.resize(0, 0)
        animation = QPropertyAnimation(widget, b"size")
        animation.setDuration(duration)
        animation.setStartValue(widget.size())
        animation.setEndValue(original_size)
        animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        animation.start()
        self.animations.append(animation)
        return animation
    
    def pulse_effect(self, widget, duration=1000, repeat=3):
        """Widget'a nabız efekti uygula"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration // 2)
        animation.setStartValue(1.0)
        animation.setEndValue(0.5)
        animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        animation.setLoopCount(repeat * 2)
        
        animation_back = QPropertyAnimation(effect, b"opacity")
        animation_back.setDuration(duration // 2)
        animation_back.setStartValue(0.5)
        animation_back.setEndValue(1.0)
        animation_back.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        group = QSequentialAnimationGroup()
        group.addAnimation(animation)
        group.addAnimation(animation_back)
        group.setLoopCount(repeat)
        
        group.start()
        self.animations.append(group)
        return group
    
    def typewriter_effect(self, text_widget, text, delay=50):
        """Typewriter efektiyle metin yaz"""
        text_widget.clear()
        self.current_text = ""
        self.target_text = text
        self.text_widget = text_widget
        self.char_index = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._add_next_char)
        self.timer.start(delay)
    
    def _add_next_char(self):
        """Typewriter için bir sonraki karakteri ekle"""
        if self.char_index < len(self.target_text):
            self.current_text += self.target_text[self.char_index]
            self.text_widget.setText(self.current_text)
            self.char_index += 1
        else:
            self.timer.stop()
    
    def glow_effect(self, widget, color=QColor(66, 133, 244), duration=1000):
        """Widget'a glow efekti uygula"""
        original_style = widget.styleSheet()
        
        glow_style = f"""
        {original_style}
        border: 2px solid {color.name()};
        border-radius: 8px;
        """
        
        def apply_glow():
            widget.setStyleSheet(glow_style)
            QTimer.singleShot(duration, lambda: widget.setStyleSheet(original_style))
        
        apply_glow()
    
    def loading_dots(self, label_widget, base_text="İşleniyor", duration=500):
        """Loading dots animasyonu"""
        self.dots_count = 0
        self.base_text = base_text
        self.label_widget = label_widget
        
        self.dots_timer = QTimer()
        self.dots_timer.timeout.connect(self._update_dots)
        self.dots_timer.start(duration)
        
        return self.dots_timer
    
    def _update_dots(self):
        """Loading dots güncelle"""
        dots = "." * (self.dots_count % 4)
        self.label_widget.setText(f"{self.base_text}{dots}")
        self.dots_count += 1
    
    def stop_loading_dots(self, timer, label_widget, final_text="Tamamlandı"):
        """Loading dots animasyonunu durdur"""
        timer.stop()
        label_widget.setText(final_text)
    
    def shake_widget(self, widget, duration=500, amplitude=10):
        """Widget'ı salla (hata için)"""
        original_pos = widget.pos()
        
        move_right = QPropertyAnimation(widget, b"pos")
        move_right.setDuration(duration // 8)
        move_right.setStartValue(original_pos)
        move_right.setEndValue(original_pos + widget.rect().topLeft() + widget.rect().topLeft().__class__(amplitude, 0))
        
        move_left = QPropertyAnimation(widget, b"pos")
        move_left.setDuration(duration // 4)
        move_left.setStartValue(move_right.endValue())
        move_left.setEndValue(original_pos + widget.rect().topLeft().__class__(-amplitude, 0))
        
        move_center = QPropertyAnimation(widget, b"pos")
        move_center.setDuration(duration // 8)
        move_center.setStartValue(move_left.endValue())
        move_center.setEndValue(original_pos)
        
        shake_sequence = QSequentialAnimationGroup()
        shake_sequence.addAnimation(move_right)
        shake_sequence.addAnimation(move_left)
        shake_sequence.addAnimation(move_center)
        shake_sequence.setLoopCount(3)
        
        shake_sequence.start()
        self.animations.append(shake_sequence)
        return shake_sequence
    
    def cleanup_animations(self):
        """Tüm animasyonları temizle"""
        for animation in self.animations:
            if animation.state() == animation.State.Running:
                animation.stop()
        self.animations.clear()

class LoadingSpinner(QWidget):
    """Custom loading spinner widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        
    def start_spinning(self):
        """Spinner'ı başlat"""
        self.timer.start(50)  # 50ms interval
        
    def stop_spinning(self):
        """Spinner'ı durdur"""
        self.timer.stop()
        
    def rotate(self):
        """Döndürme animasyonu"""
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        """Spinner çizimi"""
        from PyQt6.QtGui import QPainter, QPen
        from PyQt6.QtCore import Qt
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor(66, 133, 244), 3)
        painter.setPen(pen)
        
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.translate(rect.center())
        painter.rotate(self.angle)
        
        painter.drawArc(rect.translated(-rect.center()), 0, 270 * 16)  # 270 derece arc