from typing import List, Optional

from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QLayout, QWidget
)

class UIHelpers:
    """
    Utility functions for consistent user interface element creation.

    This class provides factory methods for creating standardized UI components
    with consistent styling and behavior. By centralizing widget creation,
    we ensure visual consistency and reduce code duplication throughout
    the application.
    """

    @staticmethod
    def create_button(text: str, style_class: Optional[str] = None, callback=None, tooltip: Optional[str] = None) -> QPushButton:
        """
        Create a styled button with optional event handling and tooltip.

        Generates a properly configured button with consistent styling applied
        through CSS classes. Supports automatic event handler connection and
        helpful tooltip text for improved user experience.

        Args:
            text (str): Button display text
            style_class (str, optional): CSS class for styling ("primary", "success", "danger")
            callback: Function to execute on button click
            tooltip (str, optional): Tooltip text displayed on hover

        Returns:
            QPushButton: Fully configured button widget
        """
        btn = QPushButton(text)
        if style_class:
            btn.setProperty("class", style_class)  # Apply CSS styling class
        if callback:
            btn.clicked.connect(callback)  # Connect click event handler
        if tooltip:
            btn.setToolTip(tooltip)  # Set informational tooltip
        return btn

    @staticmethod
    def create_labeled_row(parent_layout: QLayout, label_text: str, widget: QWidget) -> QHBoxLayout:
        """
        Create a horizontal layout combining a label with an input widget.

        Provides a standardized way to create form-style layouts with
        consistent label-widget pairing. Automatically handles layout
        management and adds the row to the specified parent layout.

        Args:
            parent_layout (QLayout): Target layout for the new row
            label_text (str): Text for the descriptive label
            widget (QWidget): Input widget to pair with the label

        Returns:
            QHBoxLayout: The created horizontal layout container
        """
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text))
        row.addWidget(widget)
        parent_layout.addLayout(row)
        return row

    @staticmethod
    def create_combo_with_items(items: List, callback=None, use_index=False) -> QComboBox:
        """
        Create a populated combo box with optional change notification.

        Generates a combo box pre-populated with the specified items and
        optional event handling for selection changes. Supports both
        index-based and text-based callback parameters.

        Args:
            items (List): Items to populate in the dropdown
            callback: Function to call when selection changes
            use_index (bool): If True, callback receives index; if False, receives text

        Returns:
            QComboBox: Configured combo box widget
        """
        combo = QComboBox()
        combo.addItems([str(item) for item in items])  # Ensure all items are strings
        if callback:
            if use_index:
                combo.currentIndexChanged.connect(callback)  # Pass selection index
            else:
                combo.currentTextChanged.connect(callback)   # Pass selection text
        return combo
