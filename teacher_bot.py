import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from database import init_db, create_user, get_user, update_language, increment_generation, check_access, subscribe_user
from ai_generator import generate_lesson_content

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants - Read from environment variable
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
    # For local development if needed, but for Railway it MUST be set
    # exit(1) 

# Conversation states
CHOOSING_LANGUAGE, ENTERING_SUBJECT, ENTERING_GRADE, ENTERING_TOPIC, ENTERING_OBJECTIVES, ENTERING_DURATION = range(6)

# Text mappings
STRINGS = {
    'en': {
        'welcome': "Welcome to the Kuwaiti Teacher's Assistant Bot! 🇰🇼\nI can help you generate lesson plans, worksheets, and activities based on the Kuwaiti curriculum.",
        'choose_lang': "Please choose your language:",
        'start_prompt': "Let's start! Please enter the Subject (e.g., Science, Arabic, Math):",
        'grade_prompt': "Great! What is the Grade level?",
        'topic_prompt': "What is the Lesson Topic?",
        'objectives_prompt': "What are the Lesson Objectives?",
        'duration_prompt': "What is the Lesson Duration (e.g., 45 minutes)?",
        'generating': "Generating your lesson plan and worksheets... Please wait a moment. ⏳",
        'trial_ended': "You have used all your 3 free trial generations. Please use /subscribe to continue using the bot.",
        'subscribe_info': "To subscribe and get unlimited generations, please contact our support at @KuwaitiTeacherSupport. (This is a demo payment flow).",
        'help': "Commands:\n/start - Start the bot\n/generate - Create a new lesson plan\n/subscribe - Subscription info\n/help - Help message",
        'error': "An error occurred. Please try again later.",
        'done': "Here is your generated lesson plan! ✅",
    },
    'ar': {
        'welcome': "أهلاً بك في بوت مساعد المعلم الكويتي! 🇰🇼\nأنا هنا لمساعدتك في إنشاء خطط الدروس، أوراق العمل، والأنشطة بناءً على المنهج الكويتي.",
        'choose_lang': "يرجى اختيار اللغة:",
        'start_prompt': "لنبدأ! يرجى إدخال المادة (مثلاً: علوم، لغة عربية، رياضيات):",
        'grade_prompt': "ممتاز! ما هو الصف الدراسي؟",
        'topic_prompt': "ما هو موضوع الدرس؟",
        'objectives_prompt': "ما هي أهداف الدرس؟",
        'duration_prompt': "ما هي مدة الدرس (مثلاً: ٤٥ دقيقة)؟",
        'generating': "جاري إنشاء خطة الدرس وأوراق العمل... يرجى الانتظار قليلاً. ⏳",
        'trial_ended': "لقد استنفدت المحاولات المجانية الـ ٣. يرجى استخدام /subscribe للاشتراك والاستمرار.",
        'subscribe_info': "للاشتراك والحصول على عدد غير محدود من الخطط، يرجى التواصل مع الدعم الفني @KuwaitiTeacherSupport. (هذا عرض تجريبي لنظام الدفع).",
        'help': "الأوامر:\n/start - بدء البوت\n/generate - إنشاء خطة درس جديدة\n/subscribe - معلومات الاشتراك\n/help - المساعدة",
        'error': "حدث خطأ ما، يرجى المحاولة لاحقاً.",
        'done': "إليك خطة الدرس التي تم إنشاؤها! ✅",
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_user(user.id, user.username)
    
    reply_keyboard = [['العربية 🇰🇼', 'English 🇺🇸']]
    await update.message.reply_text(
        STRINGS['ar']['welcome'] + "\n\n" + STRINGS['en']['welcome'],
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSING_LANGUAGE

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if 'العربية' in text:
        lang = 'ar'
    else:
        lang = 'en'
    
    update_language(user_id, lang)
    context.user_data['lang'] = lang
    
    await update.message.reply_text(
        STRINGS[lang]['start_prompt'],
        reply_markup=ReplyKeyboardRemove()
    )
    return ENTERING_SUBJECT

async def enter_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['subject'] = update.message.text
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(STRINGS[lang]['grade_prompt'])
    return ENTERING_GRADE

async def enter_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['grade'] = update.message.text
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(STRINGS[lang]['topic_prompt'])
    return ENTERING_TOPIC

async def enter_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['topic'] = update.message.text
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(STRINGS[lang]['objectives_prompt'])
    return ENTERING_OBJECTIVES

async def enter_objectives(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['objectives'] = update.message.text
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(STRINGS[lang]['duration_prompt'])
    return ENTERING_DURATION

async def enter_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['duration'] = update.message.text
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'ar')
    
    # Check subscription/trial access
    allowed, message = check_access(user_id)
    if not allowed:
        await update.message.reply_text(STRINGS[lang]['trial_ended'])
        return ConversationHandler.END

    await update.message.reply_text(STRINGS[lang]['generating'])
    
    # Generate content
    content = generate_lesson_content(
        context.user_data['subject'],
        context.user_data['grade'],
        context.user_data['topic'],
        context.user_data['objectives'],
        context.user_data['duration'],
        lang
    )
    
    if content:
        increment_generation(user_id)
        # Send in chunks if too long (Telegram limit is 4096)
        if len(content) > 4000:
            for i in range(0, len(content), 4000):
                await update.message.reply_text(content[i:i+4000])
        else:
            await update.message.reply_text(content)
        await update.message.reply_text(STRINGS[lang]['done'])
    else:
        await update.message.reply_text(STRINGS[lang]['error'])
        
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = user[2] if user else 'ar'
    await update.message.reply_text(STRINGS[lang]['subscribe_info'])

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = user[2] if user else 'ar'
    await update.message.reply_text(STRINGS[lang]['help'])

def main():
    # Initialize DB
    init_db()
    
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing. Bot cannot start.")
        return

    # Create application
    application = Application.builder().token(TOKEN).build()

    # Conversation handler for generating lesson plans
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('generate', start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, start) # Fallback to start for new users
        ],
        states={
            CHOOSING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            ENTERING_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_subject)],
            ENTERING_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_grade)],
            ENTERING_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_topic)],
            ENTERING_OBJECTIVES: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_objectives)],
            ENTERING_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_duration)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("help", help_command))

    # Run the bot
    logger.info("Bot started...")
    application.run_polling()

if __name__ == '__main__':
    main()
