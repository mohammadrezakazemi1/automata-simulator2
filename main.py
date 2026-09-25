"""Automata Simulator - PySide6 desktop application.

Bachelor's Computer Engineering project for Formal Languages and Automata Theory.
The UI is intentionally kept separate from the automata/grammar engines so that
the algorithms can be tested independently.
"""

import math
import sys

from PySide6.QtCore import QPointF, QSplitter, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from automata import FiniteAutomaton, Transition
from grammar import ContextFreeGrammar


AUTHOR = "Mohammadreza Kazemi — ساخته شده توسط محمدرضا کاظمی"


class GraphView(QWidget):
    """Interactive graph widget used by the designer and simulator."""

    state_clicked = Signal(str)
    changed = Signal()

    def __init__(self, editable=False):
        super().__init__()
        self.automaton = None
        self.editable = editable
        self.positions = {}
        self.selected = None
        self.dragging = None
        self.edge_mode = False
        self.edge_source = None
        self.active = None
        self.path = []
        self.flow_t = 0.0

        self.setMinimumHeight(420)
        self.setFocusPolicy(Qt.StrongFocus)

        # Small animation makes the currently simulated transition visible.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(35)

    def set_automaton(self, automaton, active=None, path=None):
        """Update the graph while preserving manually positioned states."""
        self.automaton = automaton
        self.active = active
        self.path = path or []

        old_positions = self.positions.copy()
        self.positions = {}

        if automaton:
            for index, state in enumerate(automaton.states):
                self.positions[state] = old_positions.get(
                    state,
                    self._default_position(index, len(automaton.states)),
                )

        self.update()

    def _default_position(self, index, count):
        """Place states around an ellipse when no manual position exists."""
        center_x = self.width() / 2
        center_y = self.height() / 2

        if count <= 1:
            return QPointF(center_x, center_y)

        radius = min(self.width(), self.height()) * 0.30
        angle = -math.pi / 2 + (2 * math.pi * index / count)

        return QPointF(
            center_x + radius * math.cos(angle),
            center_y + radius * 0.72 * math.sin(angle),
        )

    def _hit(self, point):
        """Return the state under the mouse pointer, if any."""
        for state, position in self.positions.items():
            distance = math.hypot(
                point.x() - position.x(),
                point.y() - position.y(),
            )
            if distance <= 41:
                return state
        return None

    def mouseDoubleClickEvent(self, event):
        """Create a new state on an empty canvas location."""
        if (
            not self.editable
            or event.button() != Qt.LeftButton
            or self._hit(event.position())
        ):
            return

        index = 0
        while f"q{index}" in self.automaton.states:
            index += 1

        state = f"q{index}"
        self.automaton.add_state(state)
        self.positions[state] = event.position()
        self.selected = state

        self.changed.emit()
        self.update()

    def mousePressEvent(self, event):
        """Select/drag states or start drawing a transition."""
        if not self.editable or event.button() != Qt.LeftButton:
            return

        state = self._hit(event.position())

        if self.edge_mode:
            if state:
                if self.edge_source is None:
                    self.edge_source = state
                    self.selected = state
                else:
                    self._add_transition(self.edge_source, state)
                    self.edge_source = None

            self.update()
            return

        self.selected = state
        if state:
            self.dragging = state
            self.state_clicked.emit(state)

        self.update()

    def mouseMoveEvent(self, event):
        """Move the selected state while dragging."""
        if self.editable and self.dragging and not self.edge_mode:
            self.positions[self.dragging] = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        """Finish a drag operation and notify the main window."""
        if self.dragging:
            self.dragging = None
            self.changed.emit()

    def keyPressEvent(self, event):
        """Delete the selected state with Delete/Backspace."""
        if (
            self.editable
            and event.key() in (Qt.Key_Delete, Qt.Key_Backspace)
            and self.selected
        ):
            self.automaton.remove_state(self.selected)
            self.positions.pop(self.selected, None)
            self.selected = None

            self.changed.emit()
            self.update()

    def _add_transition(self, source, target):
        """Ask for a transition symbol and add the transition safely."""
        symbol, accepted = QInputDialog.getText(
            self,
            "Transition",
            f"{source} → {target}\nSymbol:",
        )

        if not accepted or not symbol.strip():
            return

        weight, accepted = QInputDialog.getDouble(
            self,
            "Transition Weight",
            "Weight / وزن:",
            1.0,
            0.0,
            1_000_000_000.0,
            2,
        )

        if not accepted:
            return

        try:
            self.automaton.add_transition(source, symbol.strip(), target, weight)
            self.changed.emit()
        except Exception as error:
            QMessageBox.warning(self, "Transition", str(error))

    def _tick(self):
        self.flow_t = (self.flow_t + 0.018) % 1
        self.update()

    @staticmethod
    def _draw_arrow(painter, tip, back):
        """Draw a small arrow head at the end of a transition."""
        dx = tip.x() - back.x()
        dy = tip.y() - back.y()
        distance = max(math.hypot(dx, dy), 1)

        ux, uy = dx / distance, dy / distance

        left = QPointF(
            tip.x() - ux * 11 + uy * 6,
            tip.y() - uy * 11 - ux * 6,
        )
        right = QPointF(
            tip.x() - ux * 11 - uy * 6,
            tip.y() - uy * 11 + ux * 6,
        )

        painter.drawLine(tip, left)
        painter.drawLine(tip, right)

    def paintEvent(self, event):
        """Render states, transitions, start/final markers and simulation path."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0f131b"))

        if not self.automaton or not self.automaton.states:
            painter.setPen(QColor("#64748b"))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "Double-click to create a state / برای ساخت حالت دوبارکلیک کنید",
            )
            return

        transition_groups = {}
        for transition in self.automaton.transitions:
            key = (transition.source, transition.target)
            transition_groups.setdefault(key, []).append(transition)

        active_pairs = set(zip(self.path, self.path[1:]))
        state_radius = 34

        for (source, target), symbols in transition_groups.items():
            if source not in self.positions or target not in self.positions:
                continue

            start = self.positions[source]
            end = self.positions[target]
            active = (source, target) in active_pairs

            pen = QPen(
                QColor("#9b8cff" if active else "#536174"),
                3 if active else 2,
            )
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            if source == target:
                # Draw a curved self-loop.
                path = QPainterPath(
                    QPointF(start.x() - 28, start.y() - 15)
                )
                path.cubicTo(
                    start.x() - 80,
                    start.y() - 115,
                    start.x() + 80,
                    start.y() - 115,
                    start.x() + 28,
                    start.y() - 15,
                )
                painter.drawPath(path)

                tip = QPointF(start.x() + 28, start.y() - 15)
                self._draw_arrow(
                    painter,
                    tip,
                    QPointF(tip.x() - 3, tip.y() + 14),
                )
                label_position = QPointF(start.x() - 10, start.y() - 92)
            else:
                dx = end.x() - start.x()
                dy = end.y() - start.y()
                distance = max(math.hypot(dx, dy), 1)
                ux, uy = dx / distance, dy / distance

                line_start = QPointF(
                    start.x() + ux * state_radius,
                    start.y() + uy * state_radius,
                )
                line_end = QPointF(
                    end.x() - ux * state_radius,
                    end.y() - uy * state_radius,
                )

                painter.drawLine(line_start, line_end)
                self._draw_arrow(
                    painter,
                    line_end,
                    QPointF(
                        line_end.x() - ux * 12 + uy * 7,
                        line_end.y() - uy * 12 - ux * 7,
                    ),
                )

                label_position = QPointF(
                    (line_start.x() + line_end.x()) / 2 - 10,
                    (line_start.y() + line_end.y()) / 2 - 10,
                )

            painter.setPen(QColor("#d7dced"))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            label = ", ".join(
                f"{transition.symbol} [{transition.weight:g}]"
                for transition in symbols
            )
            painter.drawText(label_position, label)

            if active:
                # Animated dot shows the direction of the current transition.
                t = self.flow_t
                if source == target:
                    flow_position = QPointF(
                        start.x(),
                        start.y() - 70,
                    )
                else:
                    flow_position = QPointF(
                        start.x() + (end.x() - start.x()) * t,
                        start.y() + (end.y() - start.y()) * t,
                    )

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor("#d9d3ff")))
                painter.drawEllipse(flow_position, 5, 5)

        for state, position in self.positions.items():
            selected = state == self.selected
            active = state == self.active
            highlighted = selected or active

            painter.setPen(
                QPen(
                    QColor("#b5aaff" if highlighted else "#66758a"),
                    3 if highlighted else 2,
                )
            )
            painter.setBrush(QBrush(QColor("#1a202c")))
            painter.drawEllipse(position, state_radius, state_radius)

            # A double circle represents an accepting/final state.
            if state in self.automaton.finals:
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(
                    position,
                    state_radius - 6,
                    state_radius - 6,
                )

            painter.setPen(QColor("#f8fafc"))
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
            painter.drawText(
                position.x() - 30,
                position.y() - 10,
                60,
                20,
                Qt.AlignCenter,
                state,
            )

            # Incoming arrow marks the start state.
            if state == self.automaton.start:
                pen = QPen(QColor("#66758a"), 2)
                painter.setPen(pen)
                painter.drawLine(
                    position.x() - 70,
                    position.y(),
                    position.x() - state_radius,
                    position.y(),
                )
                self._draw_arrow(
                    painter,
                    QPointF(position.x() - state_radius, position.y()),
                    QPointF(position.x() - state_radius - 10, position.y() - 5),
                )


class MainWindow(QMainWindow):
    """Main application window and UI/controller layer."""

    TRANSLATIONS = {
        "fa": {
            "automata": "آزمایشگاه اتوماتا",
            "grammar": "آزمایشگاه گرامر",
            "designer": "طراحی ماشین",
            "simulator": "شبیه‌ساز",
            "table": "جدول انتقال",
            "convert": "NFA → DFA",
            "current": "حالت فعلی",
            "result": "نتیجه",
            "ready": "آماده",
            "run": "اجرا",
            "step": "مرحله بعد",
            "reset": "بازنشانی",
            "state": "حالت",
            "path": "مسیر",
            "accepted": "پذیرفته شد ✓",
            "rejected": "رد شد ✕",
        },
        "en": {
            "automata": "Automata Lab",
            "grammar": "Grammar Lab",
            "designer": "Designer",
            "simulator": "Simulator",
            "table": "Transition Table",
            "convert": "NFA → DFA",
            "current": "Current",
            "result": "Result",
            "ready": "Ready",
            "run": "Run",
            "step": "Step",
            "reset": "Reset",
            "state": "State",
            "path": "Path",
            "accepted": "Accepted ✓",
            "rejected": "Rejected ✕",
        },
    }

    def __init__(self):
        super().__init__()

        self.lang = "en"
        self.machine = self._create_sample_machine()
        self.current = self.machine.start
        self.path = [self.current]
        self.input_index = 0

        self.grammar_text = "S -> a A\nA -> b A | ε"

        self._build_ui()
        self._update_texts()
        self._refresh_views()

        # There is no Home page anymore; the application opens in Designer.
        self.navigate("designer")

    @staticmethod
    def _create_sample_machine():
        """Create a small DFA used as the initial demonstration machine."""
        return FiniteAutomaton(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            transitions=[
                Transition("q0", "0", "q1"),
                Transition("q0", "1", "q0"),
                Transition("q1", "0", "q1"),
                Transition("q1", "1", "q2"),
                Transition("q2", "0", "q2"),
                Transition("q2", "1", "q0"),
            ],
            start="q0",
            finals={"q2"},
        )

    @staticmethod
    def panel_style():
        """Common style for cards, editors and toolbars."""
        return """
        QFrame {
            background: #151a23;
            border: 1px solid #272f3d;
            border-radius: 12px;
        }
        QLabel {
            color: #aab5c5;
        }
        QLineEdit, QTextEdit {
            background: #0d1118;
            color: #f4f6fb;
            border: 1px solid #303949;
            border-radius: 7px;
            padding: 8px;
        }
        QPushButton {
            background: #252b39;
            color: #f7f8fb;
            border: 0;
            border-radius: 7px;
            padding: 9px 13px;
        }
        QPushButton:hover {
            background: #353d50;
        }
        """

    def _build_ui(self):
        """Construct the window and all application pages."""
        self.setMinimumSize(1200, 780)

        root = QWidget()
        self.setCentralWidget(root)

        outer_layout = QHBoxLayout(root)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar intentionally contains only actual application modules.
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            """
            QFrame { background: #0a0d13; }
            QPushButton {
                color: #aeb8c8;
                background: transparent;
                border: 0;
                border-radius: 8px;
                padding: 13px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #181d27;
                color: white;
            }
            """
        )

        sidebar_layout = QVBoxLayout(sidebar)

        self.logo = QLabel("◉  AUTOMATA\n    LAB")
        self.logo.setStyleSheet(
            "color:#f8fafc;font-size:17px;font-weight:700;padding:10px;"
        )
        sidebar_layout.addWidget(self.logo)

        self.auto_btn = QPushButton()
        self.auto_btn.setMinimumHeight(42)
        self.auto_btn.clicked.connect(lambda: self.navigate("designer"))
        sidebar_layout.addWidget(self.auto_btn)

        self.grammar_btn = QPushButton()
        self.grammar_btn.setMinimumHeight(42)
        self.grammar_btn.clicked.connect(lambda: self.navigate("grammar"))
        sidebar_layout.addWidget(self.grammar_btn)

        self.nav_buttons = []
        for key in ("designer", "simulator", "table", "convert"):
            button = QPushButton()
            button.setMinimumHeight(40)
            button.clicked.connect(
                lambda checked=False, page=key: self.navigate(page)
            )
            self.nav_buttons.append((key, button))
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        self.lang_btn = QPushButton()
        self.lang_btn.clicked.connect(self.toggle_language)
        sidebar_layout.addWidget(self.lang_btn)
        sidebar_layout.addWidget(QLabel(AUTHOR))

        outer_layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        outer_layout.addWidget(self.stack, 1)

        # Page order is stable and deliberately excludes a Home page.
        self.stack.addWidget(self._designer())
        self.stack.addWidget(self._simulator())
        self.stack.addWidget(self._table())
        self.stack.addWidget(self._convert())
        self.stack.addWidget(self._grammar())

    def _page(self):
        """Create the common page header used by every module."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 22)

        header = QHBoxLayout()

        title = QLabel()
        title.setStyleSheet(
            "font-size:25px;font-weight:700;color:#f8fafc;"
        )

        badge = QLabel()
        badge.setStyleSheet(
            "background:#242039;color:#bdb6ff;padding:7px 14px;border-radius:8px;"
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(badge)
        layout.addLayout(header)

        return page, layout, title, badge

    def _designer(self):
        page, layout, self.dtitle, self.dbadge = self._page()

        toolbar = QFrame()
        toolbar.setStyleSheet(self.panel_style())
        toolbar_layout = QHBoxLayout(toolbar)

        self.add_btn = QPushButton()
        self.edge_btn = QPushButton()
        self.edge_btn.setCheckable(True)
        self.start_btn = QPushButton()
        self.final_btn = QPushButton()
        self.delete_btn = QPushButton()

        self.add_btn.clicked.connect(self.create_state)
        self.edge_btn.toggled.connect(self._set_edge_mode)
        self.start_btn.clicked.connect(self.set_start)
        self.final_btn.clicked.connect(self.toggle_final)
        self.delete_btn.clicked.connect(self.delete_state)

        for button in (
            self.add_btn,
            self.edge_btn,
            self.start_btn,
            self.final_btn,
            self.delete_btn,
        ):
            toolbar_layout.addWidget(button)

        layout.addWidget(toolbar)

        self.design_graph = GraphView(editable=True)
        self.design_graph.state_clicked.connect(self._select_state)
        self.design_graph.changed.connect(self._refresh_views)
        layout.addWidget(self.design_graph, 1)

        self.hint = QLabel()
        layout.addWidget(self.hint)

        return page

    def _simulator(self):
        page, layout, self.stitle, self.sbadge = self._page()

        self.sim_graph = GraphView()
        layout.addWidget(self.sim_graph, 1)

        toolbar = QFrame()
        toolbar.setStyleSheet(self.panel_style())
        toolbar_layout = QHBoxLayout(toolbar)

        self.input = QLineEdit("0101")
        self.run_btn = QPushButton()
        self.step_btn = QPushButton()
        self.reset_btn = QPushButton()
        self.current_lbl = QLabel()
        self.status = QLabel()

        self.run_btn.clicked.connect(self.run_simulation)
        self.step_btn.clicked.connect(self.step_simulation)
        self.reset_btn.clicked.connect(self.reset_simulation)

        for widget in (
            self.input,
            self.run_btn,
            self.step_btn,
            self.reset_btn,
            self.current_lbl,
            self.status,
        ):
            toolbar_layout.addWidget(widget)

        layout.addWidget(toolbar)

        self.path_lbl = QLabel()
        layout.addWidget(self.path_lbl)

        return page

    def _table(self):
        page, layout, self.ttitle, self.tbadge = self._page()

        self.transition_table = QTableWidget()
        self.transition_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout.addWidget(self.transition_table)
        return page

    def _convert(self):
        page, layout, self.ctitle, self.cbadge = self._page()

        self.convert_btn = QPushButton()
        self.convert_btn.clicked.connect(self.convert_nfa)
        layout.addWidget(self.convert_btn)

        self.convert_graph = GraphView()
        layout.addWidget(self.convert_graph, 1)

        self.convert_info = QTextEdit()
        self.convert_info.setReadOnly(True)
        self.convert_info.setMaximumHeight(170)
        layout.addWidget(self.convert_info)

        return page

    def _grammar(self):
        page, layout, self.gtitle, self.gbadge = self._page()

        toolbar = QFrame()
        toolbar.setStyleSheet(self.panel_style())
        toolbar_layout = QHBoxLayout(toolbar)

        self.gback = QPushButton()
        self.ganalyze = QPushButton()
        self.gleft = QPushButton()
        self.gfactor = QPushButton()
        self.gll1 = QPushButton()

        self.gback.clicked.connect(lambda: self.navigate("designer"))
        self.ganalyze.clicked.connect(self.grammar_analyze)
        self.gleft.clicked.connect(self.grammar_left)
        self.gfactor.clicked.connect(self.grammar_factor)
        self.gll1.clicked.connect(self.grammar_ll1)

        for button in (
            self.gback,
            self.ganalyze,
            self.gleft,
            self.gfactor,
            self.gll1,
        ):
            button.setMinimumHeight(40)
            toolbar_layout.addWidget(button)

        layout.addWidget(toolbar)

        self.grammar_info = QLabel()
        self.grammar_info.setStyleSheet("color:#8793a7;padding:5px 2px;")
        layout.addWidget(self.grammar_info)

        splitter = QSplitter(Qt.Horizontal)

        # Grammar editor.
        editor_panel = QFrame()
        editor_panel.setStyleSheet(self.panel_style())
        editor_layout = QVBoxLayout(editor_panel)

        editor_header = QHBoxLayout()
        self.grammar_editor_label = QLabel()
        self.grammar_editor_label.setStyleSheet(
            "font-size:17px;font-weight:700;color:#f8fafc;"
        )

        self.grammar_example_btn = QPushButton()
        self.grammar_example_btn.clicked.connect(self.load_grammar_example)

        editor_header.addWidget(self.grammar_editor_label)
        editor_header.addStretch()
        editor_header.addWidget(self.grammar_example_btn)
        editor_layout.addLayout(editor_header)

        self.geditor = QTextEdit(self.grammar_text)
        self.geditor.setStyleSheet(
            """
            QTextEdit {
                font-family: Consolas;
                font-size: 14px;
                background: #0b1017;
                border: 1px solid #303949;
                border-radius: 9px;
                padding: 10px;
                color: #e8edf5;
            }
            """
        )
        editor_layout.addWidget(self.geditor, 1)

        input_label = QLabel()
        input_label.setObjectName("grammar_input_label")
        editor_layout.addWidget(input_label)

        self.ginput = QLineEdit("abb")
        self.ginput.setMinimumHeight(40)
        editor_layout.addWidget(self.ginput)

        splitter.addWidget(editor_panel)

        # Parse tree and derivation.
        tree_panel = QFrame()
        tree_panel.setStyleSheet(self.panel_style())
        tree_layout = QVBoxLayout(tree_panel)

        self.grammar_tree_label = QLabel()
        self.grammar_tree_label.setStyleSheet(
            "font-size:17px;font-weight:700;color:#f8fafc;"
        )
        tree_layout.addWidget(self.grammar_tree_label)

        self.gtree = QTextEdit()
        self.gtree.setReadOnly(True)
        self.gtree.setStyleSheet(
            """
            QTextEdit {
                font-family: Consolas;
                font-size: 14px;
                background: #0b1017;
                border: 1px solid #303949;
                border-radius: 9px;
                color: #d9e1ef;
                padding: 12px;
            }
            """
        )
        tree_layout.addWidget(self.gtree, 1)

        self.grammar_derivation_label = QLabel()
        self.grammar_derivation_label.setStyleSheet(
            "font-size:17px;font-weight:700;color:#f8fafc;"
        )
        tree_layout.addWidget(self.grammar_derivation_label)

        self.gder = QTextEdit()
        self.gder.setReadOnly(True)
        self.gder.setMaximumHeight(180)
        tree_layout.addWidget(self.gder)

        splitter.addWidget(tree_panel)

        # Analysis, FIRST/FOLLOW and LL(1) output.
        analysis_panel = QFrame()
        analysis_panel.setStyleSheet(self.panel_style())
        analysis_layout = QVBoxLayout(analysis_panel)

        tabs = QHBoxLayout()
        self.gtab_buttons = []

        for key in ("analysis", "first_follow", "ll1"):
            button = QPushButton()
            button.setObjectName(f"grammar_tab_{key}")
            button.setMinimumHeight(34)
            self.gtab_buttons.append((key, button))
            tabs.addWidget(button)

        analysis_layout.addLayout(tabs)

        self.ganalysis = QTextEdit()
        self.ganalysis.setReadOnly(True)
        self.ganalysis.setStyleSheet(
            """
            QTextEdit {
                font-family: Consolas;
                background: #0b1017;
                border: 1px solid #303949;
                border-radius: 9px;
                color: #d9e1ef;
                padding: 12px;
            }
            """
        )
        analysis_layout.addWidget(self.ganalysis, 1)

        splitter.addWidget(analysis_panel)
        splitter.setSizes([430, 430, 360])

        layout.addWidget(splitter, 1)

        return page

    # ------------------------------------------------------------------
    # Automata designer actions
    # ------------------------------------------------------------------

    def _set_edge_mode(self, enabled):
        self.design_graph.edge_mode = enabled
        self.edge_btn.setText(
            ("✓ حالت رسم" if self.lang == "fa" else "✓ Edge mode")
            if enabled
            else ("رسم انتقال" if self.lang == "fa" else "Draw Transition")
        )

    def _select_state(self, state):
        self.design_graph.selected = state
        self._refresh_views()

    def create_state(self):
        """Create the next available qN state."""
        index = 0
        while f"q{index}" in self.machine.states:
            index += 1

        state = f"q{index}"
        self.machine.add_state(state)
        self.design_graph.selected = state
        self._refresh_views()

    def set_start(self):
        """Set the selected state as the automaton start state."""
        if self.design_graph.selected:
            self.machine.start = self.design_graph.selected
            self.current = self.machine.start
            self.path = [self.current]
            self._refresh_views()

    def toggle_final(self):
        """Toggle accepting/final status of the selected state."""
        state = self.design_graph.selected
        if state:
            self.machine.finals.symmetric_difference_update({state})
            self._refresh_views()

    def delete_state(self):
        """Delete the selected state and its incident transitions."""
        state = self.design_graph.selected
        if state:
            self.machine.remove_state(state)
            self.design_graph.selected = None
            self._refresh_views()

    # ------------------------------------------------------------------
    # Shared refresh / table logic
    # ------------------------------------------------------------------

    def _refresh_views(self):
        """Refresh every visible representation of the current machine."""
        self._update_texts()

        self.design_graph.set_automaton(
            self.machine,
            self.current,
            self.path,
        )
        self.sim_graph.set_automaton(
            self.machine,
            self.current,
            self.path,
        )

        self._refresh_transition_table()

        self.current_lbl.setText(
            f"{self.tr('current')}: {self.current or '—'}"
        )
        self.status.setText(
            f"{self.tr('result')}: {self.tr('ready')}"
        )
        self.path_lbl.setText(
            f"{self.tr('path')}: {' → '.join(self.path)}"
        )

    def _refresh_transition_table(self):
        """Render the current automaton as a transition table."""
        self.transition_table.setColumnCount(len(self.machine.alphabet) + 1)
        self.transition_table.setHorizontalHeaderLabels(
            [self.tr("state")] + self.machine.alphabet
        )
        self.transition_table.setRowCount(len(self.machine.states))

        for row, state in enumerate(self.machine.states):
            prefix = "→ " if state == self.machine.start else ""
            final_marker = "* " if state in self.machine.finals else ""

            self.transition_table.setItem(
                row,
                0,
                QTableWidgetItem(prefix + final_marker + state),
            )

            for column, symbol in enumerate(self.machine.alphabet, start=1):
                destinations = sorted(
                    self.machine.destinations(state, symbol)
                )
                value = ", ".join(destinations) or "—"
                self.transition_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

    # ------------------------------------------------------------------
    # Automata simulation
    # ------------------------------------------------------------------

    def run_simulation(self):
        """Run the complete input through DFA or NFA simulation."""
        try:
            text = self.input.text().strip()

            if self.machine.is_deterministic():
                accepted, path = self.machine.simulate_dfa(text)
                self.path = path
                self.current = path[-1]
            else:
                accepted, path = self.machine.simulate_nfa(text)
                self.path = [
                    "{" + ",".join(sorted(states)) + "}"
                    for states in path
                ]
                self.current = self.path[-1]

            self.sim_graph.set_automaton(
                self.machine,
                self.current,
                self.path,
            )
            result = self.tr("accepted") if accepted else self.tr("rejected")
            self.status.setText(f"{self.tr('result')}: {result}")
            self.path_lbl.setText(
                f"{self.tr('path')}: {' → '.join(self.path)}"
            )

        except Exception as error:
            QMessageBox.warning(self, "Error", str(error))

    def step_simulation(self):
        """Advance a DFA simulation by exactly one input symbol."""
        try:
            text = self.input.text().strip()

            if self.input_index == 0:
                self.current = self.machine.start
                self.path = [self.current]

            if self.input_index >= len(text):
                result = (
                    self.tr("accepted")
                    if self.current in self.machine.finals
                    else self.tr("rejected")
                )
                self.status.setText(f"{self.tr('result')}: {result}")
                return

            self.current = self.machine.step_dfa(
                self.current,
                text[self.input_index],
            )
            self.input_index += 1
            self.path.append(self.current)

            self.sim_graph.set_automaton(
                self.machine,
                self.current,
                self.path,
            )
            self.current_lbl.setText(
                f"{self.tr('current')}: {self.current}"
            )

        except Exception as error:
            QMessageBox.warning(self, "Error", str(error))

    def reset_simulation(self):
        """Return the simulator to the start state."""
        self.current = self.machine.start
        self.input_index = 0
        self.path = [self.current]
        self._refresh_views()

    def convert_nfa(self):
        """Convert the current NFA to a DFA using subset construction."""
        try:
            dfa = self.machine.to_dfa()

            self.convert_graph.set_automaton(dfa, dfa.start)

            lines = [
                "DFA created by subset construction",
                "",
                f"States: {', '.join(dfa.states)}",
                f"Start: {dfa.start}",
                f"Final: {', '.join(sorted(dfa.finals)) or '—'}",
                "",
            ]

            lines.extend(
                f"{t.source} --{t.symbol} [w={t.weight:g}]--> {t.target}"
                for t in dfa.transitions
            )

            self.convert_info.setPlainText("\n".join(lines))

        except Exception as error:
            QMessageBox.warning(self, "Conversion", str(error))

    # ------------------------------------------------------------------
    # Grammar actions
    # ------------------------------------------------------------------

    def load_grammar_example(self):
        """Load a standard expression grammar into the editor."""
        self.geditor.setPlainText(
            "E -> E + T | T\n"
            "T -> T * F | F\n"
            "F -> ( E ) | id"
        )

    def _parse_current_grammar(self):
        """Parse the editor content and return a CFG object."""
        return ContextFreeGrammar("S").parse(
            self.geditor.toPlainText()
        )

    def grammar_analyze(self):
        """Validate, classify and analyze the current grammar and input."""
        try:
            grammar = self._parse_current_grammar()
            errors = grammar.validate()

            first = grammar.first_sets()
            follow = grammar.follow_sets()

            accepted, tree, _ = grammar.parse_string(
                self.ginput.text().strip()
            )

            _, conflicts = grammar.ll1_table()

            lines = [
                "Grammar is valid ✓" if not errors else "Grammar errors:",
                *errors,
                f"Classification: {grammar.classification()}",
                f"Productions: {len(grammar.productions)}",
                "",
                "FIRST:",
            ]

            lines.extend(
                f"FIRST({name}) = {{ {', '.join(sorted(first[name]))} }}"
                for name in sorted(first)
            )

            lines.extend(["", "FOLLOW:"])

            lines.extend(
                f"FOLLOW({name}) = {{ {', '.join(sorted(follow[name]))} }}"
                for name in sorted(follow)
            )

            lines.extend(
                [
                    "",
                    f"LL(1): {'Yes' if not conflicts else 'No — conflicts detected'}",
                    "",
                    "String: "
                    + ("Accepted ✓" if accepted else "Rejected ✕"),
                ]
            )

            self.ganalysis.setPlainText("\n".join(lines))
            self.gtree.setPlainText(
                self.format_tree(tree) if accepted else "—"
            )
            self.gder.setPlainText(
                "\n".join(grammar.leftmost_derivation(tree))
                if accepted
                else "—"
            )

        except Exception as error:
            QMessageBox.warning(self, "Grammar Error", str(error))

    def grammar_left(self):
        """Remove direct left recursion from the current grammar."""
        try:
            grammar = self._parse_current_grammar()
            grammar.remove_left_recursion()
            self.geditor.setPlainText(grammar.text())
            self.grammar_analyze()
        except Exception as error:
            QMessageBox.warning(self, "Grammar Error", str(error))

    def grammar_factor(self):
        """Apply simple left factoring to the current grammar."""
        try:
            grammar = self._parse_current_grammar()
            grammar.left_factor()
            self.geditor.setPlainText(grammar.text())
            self.grammar_analyze()
        except Exception as error:
            QMessageBox.warning(self, "Grammar Error", str(error))

    def grammar_ll1(self):
        """Render the LL(1) parsing table and report conflicts."""
        try:
            grammar = self._parse_current_grammar()
            table, conflicts = grammar.ll1_table()

            lines = ["LL(1) Parsing Table", ""]

            if conflicts:
                lines.append("CONFLICTS:")
                lines.extend(conflicts)
                lines.append("")

            for (nonterminal, terminal), productions in sorted(table.items()):
                rendered = " | ".join(productions)
                lines.append(
                    f"{nonterminal}, {terminal} → {rendered}"
                )

            self.ganalysis.setPlainText("\n".join(lines))

        except Exception as error:
            QMessageBox.warning(self, "Grammar Error", str(error))

    def format_tree(self, tree, indent=""):
        """Convert the internal parse-tree tuple into readable text."""
        if not tree:
            return ""

        if tree[0] == "token":
            return indent + tree[1]

        lines = [indent + tree[1]]
        lines.extend(
            self.format_tree(child, indent + "  ")
            for child in tree[2]
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Navigation / localization
    # ------------------------------------------------------------------

    def navigate(self, page):
        """Switch between the five real application modules."""
        indexes = {
            "designer": 0,
            "simulator": 1,
            "table": 2,
            "convert": 3,
            "grammar": 4,
        }
        self.stack.setCurrentIndex(indexes[page])

    def toggle_language(self):
        """Switch between English and Persian UI text."""
        self.lang = "fa" if self.lang == "en" else "en"
        self.setLayoutDirection(
            Qt.RightToLeft if self.lang == "fa" else Qt.LeftToRight
        )
        self._update_texts()

    def tr(self, key):
        return self.TRANSLATIONS[self.lang].get(key, key)

    def _update_texts(self):
        """Update all user-facing labels after a language change."""
        self.auto_btn.setText(self.tr("automata"))
        self.grammar_btn.setText(self.tr("grammar"))

        for key, button in self.nav_buttons:
            button.setText(self.tr(key))

        self.lang_btn.setText("فارسی / English")

        self.dtitle.setText(self.tr("designer"))
        self.stitle.setText(self.tr("simulator"))
        self.ttitle.setText(self.tr("table"))
        self.ctitle.setText(self.tr("convert"))
        self.gtitle.setText(
            "آزمایشگاه گرامر"
            if self.lang == "fa"
            else "Grammar Lab"
        )

        badge = "DFA" if self.machine.is_deterministic() else "NFA"
        self.dbadge.setText(badge)
        self.sbadge.setText(badge)
        self.tbadge.setText(badge)
        self.cbadge.setText(badge)
        self.gbadge.setText("CFG")

        self.add_btn.setText(
            "+ حالت" if self.lang == "fa" else "+ State"
        )
        self.start_btn.setText(
            "شروع" if self.lang == "fa" else "Set Start"
        )
        self.final_btn.setText(
            "نهایی" if self.lang == "fa" else "Toggle Final"
        )
        self.delete_btn.setText(
            "حذف حالت" if self.lang == "fa" else "Delete State"
        )

        self.hint.setText(
            "دوبارکلیک = حالت جدید • کشیدن = جابه‌جایی • "
            "رسم انتقال = اتصال دو حالت"
            if self.lang == "fa"
            else "Double-click = new state • Drag = move • "
            "Draw Transition = connect states"
        )

        self.run_btn.setText(self.tr("run"))
        self.step_btn.setText(self.tr("step"))
        self.reset_btn.setText(self.tr("reset"))

        self.convert_btn.setText(
            "تبدیل NFA به DFA"
            if self.lang == "fa"
            else "Convert NFA to DFA"
        )

        self.gback.setText(
            "← بخش اتوماتا"
            if self.lang == "fa"
            else "← Automata Lab"
        )
        self.ganalyze.setText(
            "▶ تحلیل و آزمون"
            if self.lang == "fa"
            else "▶ Analyze & Test"
        )
        self.gleft.setText(
            "↻ حذف بازگشت چپ"
            if self.lang == "fa"
            else "↻ Remove Left Recursion"
        )
        self.gfactor.setText(
            "⇥ فاکتورگیری چپ"
            if self.lang == "fa"
            else "⇥ Left Factor"
        )
        self.gll1.setText(
            "▦ جدول LL(1)"
            if self.lang == "fa"
            else "▦ LL(1) Table"
        )

        self.grammar_editor_label.setText(
            "ویرایشگر گرامر"
            if self.lang == "fa"
            else "Grammar Editor"
        )
        self.grammar_example_btn.setText(
            "بارگذاری مثال"
            if self.lang == "fa"
            else "Load Example"
        )
        self.grammar_info.setText(
            "تولیدها را مثل  S → a A | ε  بنویسید • "
            "رشته را پایین وارد کنید • برای ساخت درخت و گزارش، تحلیل را بزنید"
            if self.lang == "fa"
            else "Write productions like S → a A | ε • "
            "Test a string below • Analyze to build the tree and report"
        )
        self.grammar_tree_label.setText(
            "درخت تجزیه" if self.lang == "fa" else "Parse Tree"
        )
        self.grammar_derivation_label.setText(
            "اشتقاق" if self.lang == "fa" else "Derivation"
        )

        for key, button in self.gtab_buttons:
            labels_fa = {
                "analysis": "تحلیل",
                "first_follow": "FIRST / FOLLOW",
                "ll1": "LL(1)",
            }
            labels_en = {
                "analysis": "Analysis",
                "first_follow": "FIRST / FOLLOW",
                "ll1": "LL(1)",
            }
            button.setText(
                (labels_fa if self.lang == "fa" else labels_en)[key]
            )

        self.ginput.setPlaceholderText(
            "رشته ورودی" if self.lang == "fa" else "Input string"
        )


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(
        """
        QMainWindow, QWidget {
            background: #10141c;
            color: #e5e7eb;
            font-family: Segoe UI;
        }
        QHeaderView::section {
            background: #1b212c;
            color: #cbd5e1;
            padding: 8px;
            border: 0;
        }
        QTableWidget {
            background: #121720;
            color: #e5e7eb;
            gridline-color: #303746;
            border: 1px solid #272f3d;
        }
        """
    )

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
