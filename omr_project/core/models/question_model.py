from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass(slots=True)
class Question:
    """
    Everything you need to know about one multiple choice question.

    This holds all the data for a single question - the text, the answer
    choices, which one is correct, and how many points it's worth. Has
    built-in validation so you can't create completely broken questions.
    """

    text: str = ""
    options: List[str] = field(default_factory=lambda: ["Option A", "Option B", "Option C", "Option D"])
    correct: int = 0
    points: int = 1

    def get_non_empty_options(self) -> List[str]:
        """
        Get only the non-empty options for this question.

        Returns:
            List[str]: List of non-empty option strings
        """
        return [opt.strip() for opt in self.options if opt.strip()]

    def get_option_count(self) -> int:
        """
        Get the number of non-empty options.

        Returns:
            int: Number of valid (non-empty) options
        """
        return len(self.get_non_empty_options())

    def get_adjusted_correct_index(self) -> int:
        """
        Get the correct answer index adjusted for empty options.

        Returns:
            int: Correct answer index within non-empty options, or 0 if invalid
        """
        non_empty_options = self.get_non_empty_options()
        if self.correct < len(self.options) and self.options[self.correct].strip():
            # Find the position of the correct option within non-empty options
            correct_option = self.options[self.correct]
            try:
                return non_empty_options.index(correct_option)
            except ValueError:
                return 0
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Turn this question into a dictionary for saving.

        Useful for JSON serialization and file storage.

        Returns:
            dict: All the question data as key-value pairs
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """
        Create a question from saved dictionary data.

        The opposite of to_dict() - takes saved data and recreates
        the question object. Handles missing fields gracefully.

        Args:
            data (dict): Question data loaded from somewhere

        Returns:
            Question: New question with the loaded data
        """
        return cls(
            text=data.get('text', ''),
            options=list(data.get('options', ["Option A", "Option B", "Option C", "Option D"])),
            correct=data.get('correct', 0),
            points=data.get('points', 1),
        )

    def validate(self) -> List[str]:
        """
        Check if this question makes sense and isn't broken.

        Looks for common problems like empty text, too few options,
        pointing to a non-existent correct answer, etc.

        Returns:
            List[str]: List of problems found (empty list = no problems)
        """
        errors = []

        # Make sure there's actually a question
        if not self.text.strip():
            errors.append("Question text is empty")

        # Need at least 2 choices for a multiple choice question
        valid_options = [opt.strip() for opt in self.options if opt.strip()]
        if len(valid_options) < 2:
            errors.append("At least 2 answer options are required")

        # The correct answer index has to point to a non-empty option
        if self.correct < 0 or self.correct >= len(self.options) or not self.options[self.correct].strip():
            errors.append("Invalid correct answer - must point to a non-empty option")

        # Points can't be negative (that would be weird)
        if self.points < 0:
            errors.append("Points cannot be negative")

        return errors
