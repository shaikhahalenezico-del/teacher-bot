import os
from openai import OpenAI

# Initialize OpenAI client using the OPENAI_API_KEY environment variable
api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def generate_lesson_content(subject, grade, topic, objectives, duration, language='ar'):
    prompt_en = f"""
    Generate a complete lesson plan and educational materials based on the Kuwaiti curriculum.
    Subject: {subject}
    Grade: {grade}
    Topic: {topic}
    Objectives: {objectives}
    Duration: {duration}

    The output should include:
    1. A complete lesson plan (Introduction, Body, Conclusion).
    2. Worksheets with exercises.
    3. Classroom activities.
    4. Assessment questions.
    
    Language: English.
    """

    prompt_ar = f"""
    قم بإنشاء خطة درس كاملة ومواد تعليمية بناءً على المنهج الكويتي.
    المادة: {subject}
    الصف: {grade}
    الموضوع: {topic}
    الأهداف: {objectives}
    المدة: {duration}

    يجب أن يتضمن المخرج:
    1. خطة درس كاملة (مقدمة، عرض، خاتمة).
    2. أوراق عمل مع تمارين.
    3. أنشطة صفية.
    4. أسئلة تقييمية.
    
    اللغة: العربية (بأسلوب تربوي مناسب للمدارس الكويتية).
    """

    prompt = prompt_ar if language == 'ar' else prompt_en

    try:
        if not api_key:
            return "Error: OPENAI_API_KEY is not set in the environment."

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert Kuwaiti teacher and curriculum designer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating content: {e}")
        return None

if __name__ == "__main__":
    # Test generation
    test_content = generate_lesson_content("Science", "Grade 5", "Photosynthesis", "Understand how plants make food", "45 mins", "ar")
    print(test_content)
