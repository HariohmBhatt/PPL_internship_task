"""Mock AI provider for testing and development."""

import hashlib
import random
from typing import Any

from app.services.ai.provider import AIProvider


class MockProvider(AIProvider):
    """Mock AI provider that returns deterministic fake content."""
    
    def __init__(self, seed: int = 42):
        """Initialize with a seed for deterministic results."""
        self.seed = seed
        self._random = random.Random(seed)
    
    def _get_seeded_random(self, input_string: str) -> random.Random:
        """Get a random generator seeded with input string for deterministic results."""
        # Create a hash of the input string for consistent seeding
        hash_object = hashlib.md5(input_string.encode())
        seed = int(hash_object.hexdigest()[:8], 16)
        return random.Random(seed)
    
    async def generate_questions(
        self,
        subject: str,
        grade_level: str,
        num_questions: int,
        difficulty: str,
        topics: list[str],
        question_types: list[str],
        standard: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate mock quiz questions."""
        # Create deterministic seed from parameters
        seed_string = f"{subject}_{grade_level}_{num_questions}_{difficulty}_{'_'.join(topics)}"
        rng = self._get_seeded_random(seed_string)
        
        questions = []
        
        for i in range(num_questions):
            # Cycle through question types
            question_type = question_types[i % len(question_types)]
            topic = topics[i % len(topics)]
            
            # Generate question based on type
            if question_type == "MCQ":
                question = self._generate_mcq(subject, topic, difficulty, i + 1, rng)
            elif question_type == "TF":
                question = self._generate_tf(subject, topic, difficulty, i + 1, rng)
            elif question_type == "short_answer":
                question = self._generate_short_answer(subject, topic, difficulty, i + 1, rng)
            else:  # essay
                question = self._generate_essay(subject, topic, difficulty, i + 1, rng)
            
            questions.append(question)
        
        return questions
    
    def _generate_mcq(self, subject: str, topic: str, difficulty: str, order: int, rng: random.Random) -> dict[str, Any]:
        """Generate a multiple choice question."""
        difficulty_points = {"easy": 1, "medium": 2, "hard": 3}
        
        options = [
            f"Option A for {topic} in {subject}",
            f"Option B for {topic} in {subject}",
            f"Option C for {topic} in {subject}",
            f"Option D for {topic} in {subject}",
        ]
        
        correct_option = rng.choice(options)
        
        return {
            "question_text": f"Question {order}: What is the main concept of {topic} in {subject}? (Difficulty: {difficulty})",
            "question_type": "MCQ",
            "difficulty": difficulty,
            "topic": topic,
            "order": order,
            "points": difficulty_points.get(difficulty, 1),
            "options": options,
            "correct_answer": correct_option,
            "explanation": f"The correct answer is related to the fundamental principles of {topic}.",
            "hint_text": f"Think about the core concepts in {topic}.",
        }
    
    def _generate_tf(self, subject: str, topic: str, difficulty: str, order: int, rng: random.Random) -> dict[str, Any]:
        """Generate a true/false question."""
        difficulty_points = {"easy": 1, "medium": 2, "hard": 3}
        
        statement = f"{topic} is a fundamental concept in {subject}"
        correct_answer = rng.choice(["True", "False"])
        
        return {
            "question_text": f"Question {order}: True or False - {statement}? (Difficulty: {difficulty})",
            "question_type": "TF",
            "difficulty": difficulty,
            "topic": topic,
            "order": order,
            "points": difficulty_points.get(difficulty, 1),
            "options": ["True", "False"],
            "correct_answer": correct_answer,
            "explanation": f"This statement about {topic} is {correct_answer.lower()}.",
            "hint_text": f"Consider the definition of {topic}.",
        }
    
    def _generate_short_answer(self, subject: str, topic: str, difficulty: str, order: int, rng: random.Random) -> dict[str, Any]:
        """Generate a short answer question."""
        difficulty_points = {"easy": 2, "medium": 3, "hard": 5}
        
        return {
            "question_text": f"Question {order}: Explain the key aspects of {topic} in {subject}. (Difficulty: {difficulty})",
            "question_type": "short_answer",
            "difficulty": difficulty,
            "topic": topic,
            "order": order,
            "points": difficulty_points.get(difficulty, 2),
            "options": None,
            "correct_answer": f"The key aspects of {topic} include understanding its fundamental principles and applications.",
            "explanation": f"A good answer should cover the main concepts and practical applications of {topic}.",
            "hint_text": f"Think about how {topic} is used and why it's important.",
        }
    
    def _generate_essay(self, subject: str, topic: str, difficulty: str, order: int, rng: random.Random) -> dict[str, Any]:
        """Generate an essay question."""
        difficulty_points = {"easy": 5, "medium": 8, "hard": 10}
        
        return {
            "question_text": f"Question {order}: Write a comprehensive essay on {topic} in the context of {subject}. (Difficulty: {difficulty})",
            "question_type": "essay",
            "difficulty": difficulty,
            "topic": topic,
            "order": order,
            "points": difficulty_points.get(difficulty, 5),
            "options": None,
            "correct_answer": f"A comprehensive essay on {topic} should cover background, key concepts, applications, and implications.",
            "explanation": f"The essay should demonstrate deep understanding of {topic} and its relevance to {subject}.",
            "hint_text": f"Structure your essay with introduction, main points about {topic}, and conclusion.",
        }
    
    async def grade_short_answer(
        self,
        question: str,
        correct_answer: str,
        student_answer: str,
        max_points: float = 1.0,
    ) -> dict[str, Any]:
        """Grade a short answer question using mock logic."""
        # Create deterministic seed from inputs
        seed_string = f"{question}_{correct_answer}_{student_answer}"
        rng = self._get_seeded_random(seed_string)
        
        # Simple mock grading logic
        if not student_answer or student_answer.strip() == "":
            score = 0.0
            feedback = "No answer provided."
        elif len(student_answer.strip()) < 10:
            score = max_points * 0.3
            feedback = "Answer is too brief. Provide more detail."
        elif "wrong" in student_answer.lower() or "incorrect" in student_answer.lower():
            score = max_points * 0.2
            feedback = "Answer contains incorrect information."
        else:
            # Base score on answer length and some random variation
            base_score = min(len(student_answer) / 100, 0.8)  # Max 80% from length
            variation = rng.uniform(-0.2, 0.2)  # ±20% variation
            score = max(0.0, min(max_points, max_points * (base_score + variation)))
            
            if score > max_points * 0.8:
                feedback = "Excellent answer with good understanding."
            elif score > max_points * 0.6:
                feedback = "Good answer but could be more comprehensive."
            elif score > max_points * 0.4:
                feedback = "Adequate answer but missing key points."
            else:
                feedback = "Weak answer. Review the topic and try again."
        
        return {
            "score": round(score, 2),
            "max_points": max_points,
            "feedback": feedback,
            "confidence": rng.uniform(0.7, 0.95),  # Mock confidence score
        }
    
    async def hint(
        self,
        question: str,
        question_type: str,
        difficulty: str,
        topic: str,
    ) -> str:
        """Generate a hint for a question."""
        # Create deterministic seed from inputs
        seed_string = f"{question}_{question_type}_{difficulty}_{topic}"
        rng = self._get_seeded_random(seed_string)
        
        hint_templates = [
            f"Think about the fundamental concepts of {topic}.",
            f"Consider how {topic} relates to the broader subject area.",
            f"Review the key definitions and principles of {topic}.",
            f"What are the main characteristics or properties of {topic}?",
            f"How is {topic} typically used or applied in practice?",
        ]
        
        if question_type == "MCQ":
            hint_templates.extend([
                "Look for keywords in the question that might point to the answer.",
                "Try to eliminate obviously incorrect options first.",
                "Consider which option best fits the context of the question.",
            ])
        elif question_type == "TF":
            hint_templates.extend([
                "Think about whether the statement is always true or if there are exceptions.",
                "Consider the exact wording of the statement carefully.",
            ])
        elif question_type in ["short_answer", "essay"]:
            hint_templates.extend([
                "Structure your answer with clear main points.",
                "Include specific examples or details to support your answer.",
                "Make sure to address all parts of the question.",
            ])
        
        return rng.choice(hint_templates)
    
    async def suggest_improvements(
        self,
        quiz_results: dict[str, Any],
        student_performance: dict[str, Any],
    ) -> list[str]:
        """Suggest improvements based on quiz performance."""
        percentage = student_performance.get("percentage", 0)
        weak_topics = student_performance.get("weak_topics", [])
        question_types = student_performance.get("question_types", {})
        
        suggestions = []
        
        # Performance-based suggestions
        if percentage < 40:
            suggestions.append("Review fundamental concepts and practice more basic questions before attempting advanced topics.")
        elif percentage < 60:
            suggestions.append("Focus on understanding core concepts better and practice applying them to different scenarios.")
        elif percentage < 80:
            suggestions.append("Work on attention to detail and consider reviewing questions more carefully before answering.")
        else:
            suggestions.append("Great job! Continue practicing with more challenging questions to deepen your understanding.")
        
        # Topic-based suggestions
        if weak_topics:
            topic_list = ", ".join(weak_topics[:3])  # Limit to 3 topics
            suggestions.append(f"Spend extra time studying these topics: {topic_list}. Consider additional practice questions in these areas.")
        else:
            suggestions.append("Your understanding appears consistent across topics. Focus on time management and advanced problem-solving techniques.")
        
        # Question type suggestions
        if question_types.get("MCQ", 0) < question_types.get("short_answer", 0):
            suggestions.append("Practice more multiple-choice strategies such as elimination and keyword identification.")
        elif question_types.get("short_answer", 0) < question_types.get("MCQ", 0):
            suggestions.append("Work on providing more detailed and structured answers for written responses.")
        
        # Always return exactly 2 suggestions as per requirements
        return suggestions[:2] if len(suggestions) >= 2 else suggestions + ["Continue practicing regularly to maintain and improve your skills."]
